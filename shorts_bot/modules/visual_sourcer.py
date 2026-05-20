"""
visual_sourcer.py - Downloads free stock videos from Pixabay API.
Free, no auth issues, unlimited downloads.
"""
import logging
import os
import random
import time

import requests

import config

log = logging.getLogger(__name__)

PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "55951851-7282cb13bfe0431ff6400f2a0")
PIXABAY_URL = "https://pixabay.com/api/videos/"

FALLBACK_QUERIES = [
    "money",
    "finance",
    "business",
    "india city",
    "smartphone",
    "success",
]


def search_videos(query: str, count: int = 5) -> list:
    """Search Pixabay for relevant vertical videos."""
    params = {
        "key":        PIXABAY_KEY,
        "q":          query,
        "video_type": "film",
        "per_page":   min(count * 2, 20),
        "safesearch": "true",
        "order":      "popular",
    }
    try:
        r = requests.get(PIXABAY_URL, params=params, timeout=15)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            log.warning(f"No videos for '{query}', trying fallback")
            params["q"] = random.choice(FALLBACK_QUERIES)
            r2 = requests.get(PIXABAY_URL, params=params, timeout=15)
            hits = r2.json().get("hits", [])
        log.info(f"Pixabay: found {len(hits)} videos for '{query}'")
        return hits[:count]
    except Exception as e:
        log.error(f"Pixabay search failed: {e}")
        return []


def download_video(video: dict, output_dir: str, index: int) -> str:
    """Download best quality video file from Pixabay hit."""
    videos = video.get("videos", {})
    # Pick best available quality: large > medium > small > tiny
    for quality in ["large", "medium", "small", "tiny"]:
        vid = videos.get(quality, {})
        url = vid.get("url", "")
        if url:
            break
    if not url:
        return None

    output_path = os.path.join(output_dir, f"clip_{index:02d}.mp4")
    try:
        log.info(f"Downloading clip {index} ({quality})...")
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        log.info(f"Downloaded clip {index}: {size_mb:.1f}MB")
        return output_path
    except Exception as e:
        log.error(f"Download failed for clip {index}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None


def get_video_clips(search_query: str, output_dir: str, count: int = None) -> list:
    """Main entry — search and download clips to output_dir."""
    if count is None:
        count = config.PEXELS_PER_VIDEO

    os.makedirs(output_dir, exist_ok=True)

    # Clean query for Pixabay (shorter is better)
    clean_query = " ".join(search_query.split()[:3])
    videos = search_videos(clean_query, count)

    if len(videos) < 2:
        videos += search_videos("money india", count)

    local_paths = []
    for i, video in enumerate(videos[:count]):
        path = download_video(video, output_dir, i)
        if path:
            local_paths.append(path)
        time.sleep(0.2)

    log.info(f"Got {len(local_paths)} clips for '{clean_query}'")
    return local_paths
