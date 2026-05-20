"""
visual_sourcer.py
Downloads royalty-free stock videos from Pexels API.
Free tier: 200 requests/hour, unlimited downloads.
Sign up at pexels.com/api — free forever.
"""

import logging
import os
import random
import time

import requests

import config

log = logging.getLogger(__name__)

PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
PEXELS_HEADERS   = {"Authorization": config.PEXELS_API_KEY}

# Fallback queries if topic-specific search returns no results
FALLBACK_QUERIES = [
    "money india",
    "indian rupee",
    "stock market india",
    "savings bank",
    "business india city",
    "smartphone finance app",
    "indian city economy",
]


def search_videos(query: str, count: int = 5) -> list[dict]:
    """
    Search Pexels for relevant vertical videos.
    Returns list of video metadata dicts.
    """
    params = {
        "query":       query,
        "per_page":    count * 2,   # fetch extra in case some are bad
        "orientation": "portrait",   # vertical for Shorts
        "size":        "medium",
        "min_duration": 4,
        "max_duration": 20,
    }

    try:
        r = requests.get(
            PEXELS_VIDEO_URL,
            headers=PEXELS_HEADERS,
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])

        if not videos:
            log.warning(f"No videos for '{query}', trying fallback")
            return search_videos(random.choice(FALLBACK_QUERIES), count)

        # Filter to portrait orientation and reasonable duration
        filtered = [
            v for v in videos
            if v.get("width", 1) < v.get("height", 2)   # portrait
            and 3 <= v.get("duration", 0) <= 25
        ]

        if not filtered:
            filtered = videos   # use all if none pass filter

        log.info(f"Pexels: found {len(filtered)} videos for '{query}'")
        return filtered[:count]

    except requests.RequestException as e:
        log.error(f"Pexels search failed: {e}")
        return []


def download_video(video: dict, output_dir: str, index: int) -> str | None:
    """
    Download the best quality file for a Pexels video.
    Returns local file path or None if failed.
    """
    files = video.get("video_files", [])
    if not files:
        return None

    # Prefer HD portrait files
    def quality_score(f):
        w = f.get("width", 0)
        h = f.get("height", 0)
        is_portrait = h > w
        hd = w >= 720
        return (is_portrait * 10) + (hd * 5) + (w // 100)

    files_sorted = sorted(files, key=quality_score, reverse=True)
    best = files_sorted[0]
    url  = best.get("link", "")

    if not url:
        return None

    output_path = os.path.join(output_dir, f"clip_{index:02d}.mp4")

    try:
        log.info(f"Downloading clip {index}: {url[:60]}...")
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        log.info(f"Downloaded clip {index}: {size_mb:.1f}MB → {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Download failed for clip {index}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def get_video_clips(search_query: str, output_dir: str, count: int = None) -> list[str]:
    """
    Main entry point.
    Searches and downloads `count` clips to output_dir.
    Returns list of local file paths.
    """
    if count is None:
        count = config.PEXELS_PER_VIDEO

    os.makedirs(output_dir, exist_ok=True)

    # Try primary query, then broaden if not enough clips
    videos = search_videos(search_query, count)

    if len(videos) < 2:
        broader = search_query.split()[0]   # single keyword
        videos += search_videos(broader, count - len(videos))

    local_paths = []
    for i, video in enumerate(videos):
        path = download_video(video, output_dir, i)
        if path:
            local_paths.append(path)
        time.sleep(0.3)   # polite rate limiting

    log.info(f"Got {len(local_paths)} clips for '{search_query}'")
    return local_paths


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clips = get_video_clips("money india rupee", "/tmp/test_clips", count=3)
    for c in clips:
        print(c)
