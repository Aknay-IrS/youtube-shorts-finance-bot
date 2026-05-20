"""
main.py
Master orchestrator for the YouTube Shorts automation pipeline.

Usage:
  python main.py                  # make 2 videos (default)
  python main.py --count 1        # make 1 video
  python main.py --topic "SIP"    # specific topic
  python main.py --dry-run        # generate script only, no video
  python main.py --no-upload      # make video but don't upload
"""

import argparse
import json
import logging
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import config
from modules.trend_detector     import get_trending_topic
from modules.script_generator   import generate_script
from modules.voice_generator    import generate_voice, build_caption_groups, get_audio_duration
from modules.visual_sourcer     import get_video_clips
from modules.video_assembler    import assemble_video
from modules.thumbnail_generator import generate_thumbnail
from modules.youtube_uploader   import upload_short, set_thumbnail

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="a"),
    ],
)
log = logging.getLogger("main")


def make_short(
    topic:     str = None,
    dry_run:   bool = False,
    no_upload: bool = False,
) -> dict:
    """
    Full pipeline for one YouTube Short.
    Returns result dict with status and metadata.
    """
    run_id    = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir  = Path(f"output/{run_id}")
    work_dir.mkdir(parents=True, exist_ok=True)

    result = {"run_id": run_id, "status": "started", "topic": topic}

    # ── Step 1: Trend Detection ───────────────────────────────────────────────
    log.info("═" * 55)
    log.info(f"RUN {run_id} — STEP 1: Trend Detection")

    used_today = _load_used_today()
    if not topic:
        topic = get_trending_topic(used_today)

    result["topic"] = topic
    log.info(f"Topic: {topic}")

    # ── Step 2: Script Generation ─────────────────────────────────────────────
    log.info("STEP 2: Script Generation")
    script = generate_script(topic)

    script_file = work_dir / "script.json"
    script_file.write_text(json.dumps(script, indent=2, ensure_ascii=False))
    result["title"] = script["title"]
    log.info(f"Title: {script['title']}")

    if dry_run:
        log.info("DRY RUN — stopping after script generation")
        log.info(f"Script:\n{script['full_text']}")
        result["status"] = "dry_run_complete"
        return result

    # ── Step 3: Voice Generation ──────────────────────────────────────────────
    log.info("STEP 3: Voice Generation (edge-tts)")
    audio_path = str(work_dir / "voice.mp3")
    timings    = generate_voice(script["full_text"], audio_path)
    captions   = build_caption_groups(timings, config.CAPTION_MAX_WORDS)
    duration   = get_audio_duration(audio_path)
    result["duration"] = round(duration, 1)
    log.info(f"Audio duration: {duration:.1f}s | Captions: {len(captions)}")

    # ── Step 4: Visual Sourcing ───────────────────────────────────────────────
    log.info("STEP 4: Visual Sourcing (Pexels)")
    clips_dir  = str(work_dir / "clips")
    clip_paths = get_video_clips(
        script.get("pexels_search", "money india"),
        clips_dir,
        count=config.PEXELS_PER_VIDEO,
    )
    result["clips"] = len(clip_paths)
    log.info(f"Downloaded {len(clip_paths)} clips")

    # ── Step 5: Video Assembly ────────────────────────────────────────────────
    log.info("STEP 5: Video Assembly")
    video_path = str(work_dir / "short.mp4")

    assemble_video(
        clip_paths  = clip_paths,
        audio_path  = audio_path,
        captions    = captions,
        title       = script["title"],
        output_path = video_path,
    )
    result["video_path"] = video_path

    # ── Step 6: Thumbnail ─────────────────────────────────────────────────────
    log.info("STEP 6: Thumbnail Generation")
    thumb_path = str(work_dir / "thumbnail.jpg")
    generate_thumbnail(
        title        = script["title"],
        hook_text    = script["hook"][:80],
        output_path  = thumb_path,
        pexels_query = script.get("pexels_search", "money india"),
    )
    result["thumbnail_path"] = thumb_path

    if no_upload:
        log.info("--no-upload flag set — skipping YouTube upload")
        result["status"] = "video_ready_no_upload"
        _mark_used(topic)
        return result

    # ── Step 7: YouTube Upload ────────────────────────────────────────────────
    log.info("STEP 7: Uploading to YouTube")
    video_id = upload_short(
        video_path  = video_path,
        title       = script["title"],
        description = script["description"],
        tags        = script["tags"],
        scheduled   = True,
    )

    if video_id:
        set_thumbnail(video_id, thumb_path)
        result["video_id"]  = video_id
        result["video_url"] = f"https://youtube.com/shorts/{video_id}"
        result["status"]    = "uploaded"
        log.info(f"✅ Done! https://youtube.com/shorts/{video_id}")
    else:
        result["status"] = "upload_failed"
        log.error("Upload failed — video saved locally")

    _mark_used(topic)

    # ── Save result log ───────────────────────────────────────────────────────
    result_file = work_dir / "result.json"
    result_file.write_text(json.dumps(result, indent=2))

    return result


def _load_used_today() -> list[str]:
    """Load list of topics already used today."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(f"output/used_{today}.txt")
    if log_file.exists():
        return log_file.read_text().strip().splitlines()
    return []


def _mark_used(topic: str):
    """Record a topic as used today."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = Path(f"output/used_{today}.txt")
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, "a") as f:
        f.write(topic + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Automation Bot"
    )
    parser.add_argument("--count",     type=int, default=config.VIDEOS_PER_RUN,
                        help="Number of Shorts to make")
    parser.add_argument("--topic",     type=str, default=None,
                        help="Specific topic (skips trend detection)")
    parser.add_argument("--dry-run",   action="store_true",
                        help="Generate script only — no video, no upload")
    parser.add_argument("--no-upload", action="store_true",
                        help="Make video but skip YouTube upload")
    args = parser.parse_args()

    # Validate API keys
    if not config.CLAUDE_API_KEY:
        log.error("CLAUDE_API_KEY not set in .env")
        sys.exit(1)
    if not args.dry_run and not config.PEXELS_API_KEY:
        log.error("PEXELS_API_KEY not set in .env")
        sys.exit(1)

    log.info(f"Starting pipeline — making {args.count} Short(s)")
    results = []

    for i in range(args.count):
        log.info(f"\n{'═'*55}")
        log.info(f"VIDEO {i+1} of {args.count}")
        log.info(f"{'═'*55}")

        try:
            r = make_short(
                topic     = args.topic if i == 0 else None,
                dry_run   = args.dry_run,
                no_upload = args.no_upload,
            )
            results.append(r)
            log.info(f"Video {i+1} status: {r['status']}")

        except Exception as e:
            log.error(f"Video {i+1} FAILED: {e}", exc_info=True)
            results.append({"status": "error", "error": str(e)})

        # Brief pause between videos
        if i < args.count - 1:
            time.sleep(10)

    # Summary
    log.info(f"\n{'═'*55}")
    log.info("PIPELINE COMPLETE")
    for i, r in enumerate(results):
        status = r.get("status", "unknown")
        title  = r.get("title", "N/A")
        url    = r.get("video_url", "")
        log.info(f"  Video {i+1}: [{status}] {title} {url}")
    log.info(f"{'═'*55}\n")


if __name__ == "__main__":
    main()
