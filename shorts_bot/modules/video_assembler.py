"""
video_assembler.py
Assembles the final YouTube Short from:
  - Stock video clips (Pexels)
  - AI voiceover (edge-tts MP3)
  - Auto-captions (word-level timing)
  - Dark gradient overlay for text readability
  - Optional background music

Output: 1080x1920, H.264, ready to upload.
"""

import logging
import os
import textwrap

import numpy as np
from moviepy.editor import (
    AudioFileClip, ColorClip, CompositeVideoClip,
    TextClip, VideoFileClip, concatenate_videoclips,
    crop, resize
)

import config

log = logging.getLogger(__name__)

W = config.VIDEO_WIDTH    # 1080
H = config.VIDEO_HEIGHT   # 1920


def load_and_prep_clip(path: str, target_duration: float = None) -> VideoFileClip:
    """Load a clip, crop to 9:16, resize to 1080x1920."""
    try:
        clip = VideoFileClip(path, audio=False)

        # Crop to 9:16 aspect ratio
        clip_ratio = clip.w / clip.h
        target_ratio = W / H

        if clip_ratio > target_ratio:
            # Clip is wider than 9:16 — crop sides
            new_w = int(clip.h * target_ratio)
            x_center = clip.w / 2
            clip = crop(clip, width=new_w, x_center=x_center)
        else:
            # Clip is taller than 9:16 — crop top/bottom
            new_h = int(clip.w / target_ratio)
            y_center = clip.h / 2
            clip = crop(clip, height=new_h, y_center=y_center)

        # Resize to 1080x1920
        clip = resize(clip, (W, H))

        # Loop if shorter than needed
        if target_duration and clip.duration < target_duration:
            loops = int(np.ceil(target_duration / clip.duration)) + 1
            from moviepy.editor import concatenate_videoclips as cc
            clip = cc([clip] * loops).subclip(0, target_duration)

        return clip

    except Exception as e:
        log.error(f"Failed to load clip {path}: {e}")
        # Return a black clip as fallback
        return ColorClip((W, H), col=[20, 20, 20],
                         duration=target_duration or 10)


def build_background(clip_paths: list[str], total_duration: float) -> CompositeVideoClip:
    """
    Concatenate clips to fill total_duration.
    Adds dark gradient overlay for text readability.
    """
    if not clip_paths:
        # Fallback: dark background
        return ColorClip((W, H), col=[15, 15, 30], duration=total_duration)

    # Load and trim clips
    clips = []
    remaining = total_duration

    for path in clip_paths * 3:   # cycle through clips if needed
        if remaining <= 0:
            break
        duration = min(remaining, 12)   # max 12s per clip
        c = load_and_prep_clip(path, target_duration=duration)
        c = c.subclip(0, min(duration, c.duration))
        clips.append(c)
        remaining -= c.duration

    bg = concatenate_videoclips(clips, method="compose")
    bg = bg.subclip(0, total_duration)

    # Dark semi-transparent overlay (60% opacity) — improves text readability
    overlay = ColorClip((W, H), col=[0, 0, 0], duration=total_duration)
    overlay = overlay.set_opacity(0.55)

    return CompositeVideoClip([bg, overlay])


def make_caption_clip(caption: dict, duration_s: float) -> TextClip:
    """
    Build a single caption TextClip with white text + black stroke.
    caption = {text, start_ms, end_ms}
    """
    text = caption["text"].upper()
    start = caption["start_ms"] / 1000
    end   = caption["end_ms"]   / 1000
    dur   = max(end - start, 0.1)

    # Wrap long lines
    wrapped = "\n".join(textwrap.wrap(text, width=14))

    try:
        txt = TextClip(
            wrapped,
            fontsize=config.FONT_SIZE_CAPTION,
            color=config.FONT_COLOR,
            font="DejaVu-Sans-Bold",
            stroke_color="black",
            stroke_width=config.CAPTION_STROKE,
            method="caption",
            size=(W - 80, None),
            align="center",
        )
    except Exception:
        # Fallback font
        txt = TextClip(
            wrapped,
            fontsize=config.FONT_SIZE_CAPTION,
            color=config.FONT_COLOR,
            stroke_color="black",
            stroke_width=config.CAPTION_STROKE,
            method="label",
        )

    # Position: bottom-center (30% from bottom)
    txt = txt.set_position(("center", H * 0.62))
    txt = txt.set_start(start).set_duration(dur)

    return txt


def make_title_clip(title: str, total_duration: float) -> TextClip:
    """Top banner with the video title — shows for first 3 seconds."""
    clean = title.replace("#Shorts", "").strip()
    wrapped = "\n".join(textwrap.wrap(clean, width=20))

    try:
        txt = TextClip(
            wrapped,
            fontsize=48,
            color="white",
            font="DejaVu-Sans-Bold",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(W - 80, None),
            align="center",
        )
    except Exception:
        txt = TextClip(wrapped, fontsize=48, color="white", stroke_color="black",
                       stroke_width=3, method="label")

    txt = txt.set_position(("center", 120))
    txt = txt.set_start(0).set_duration(min(3.5, total_duration))
    return txt


def make_cta_clip(cta_text: str, total_duration: float) -> TextClip:
    """Bottom CTA — appears in last 4 seconds."""
    try:
        txt = TextClip(
            "👆 FOLLOW for daily tips!",
            fontsize=52,
            color="#FFD700",   # gold
            font="DejaVu-Sans-Bold",
            stroke_color="black",
            stroke_width=3,
            method="label",
        )
    except Exception:
        txt = TextClip("FOLLOW for daily tips!", fontsize=52, color="yellow",
                       stroke_color="black", stroke_width=3, method="label")

    start = max(0, total_duration - 4)
    txt = txt.set_position(("center", H - 200))
    txt = txt.set_start(start).set_duration(4)
    return txt


def assemble_video(
    clip_paths:  list[str],
    audio_path:  str,
    captions:    list[dict],
    title:       str,
    output_path: str,
) -> str:
    """
    Master assembly function.
    Returns path to final rendered video.
    """
    log.info("Assembling video...")

    # Load voice audio
    audio      = AudioFileClip(audio_path)
    total_dur  = audio.duration + 0.5   # tiny buffer at end

    # Build background
    log.info("Building background...")
    background = build_background(clip_paths, total_dur)

    # Build caption clips
    log.info(f"Building {len(captions)} caption clips...")
    caption_clips = [make_caption_clip(c, total_dur) for c in captions]

    # Title + CTA
    title_clip = make_title_clip(title, total_dur)
    cta_clip   = make_cta_clip("Follow for more!", total_dur)

    # Compose everything
    all_layers = [background] + caption_clips + [title_clip, cta_clip]
    final = CompositeVideoClip(all_layers, size=(W, H))
    final = final.set_audio(audio)
    final = final.set_duration(total_dur)

    # Render
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    log.info(f"Rendering to {output_path}...")

    final.write_videofile(
        output_path,
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate=config.VIDEO_BITRATE,
        threads=4,
        logger=None,   # suppress verbose moviepy output
        preset="fast",
    )

    log.info(f"Video ready: {output_path}")
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Video assembler ready.")
    print(f"Output size: {W}x{H} @ {config.VIDEO_FPS}fps")
