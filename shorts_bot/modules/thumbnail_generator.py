"""
thumbnail_generator.py
Generates eye-catching thumbnails for YouTube Shorts.
Uses Pillow — 100% free.
"""

import logging
import os
import textwrap

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import config

log = logging.getLogger(__name__)

THUMB_W = 1280
THUMB_H = 720


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Load a bold font, falling back to default if not found."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _download_bg_image(query: str) -> Image.Image | None:
    """Download a relevant background from Pexels."""
    if not config.PEXELS_API_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": config.PEXELS_API_KEY},
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            timeout=10,
        )
        photos = r.json().get("photos", [])
        if not photos:
            return None

        img_url = photos[0]["src"]["large"]
        img_r   = requests.get(img_url, timeout=15)
        return Image.open(img_r.raw).convert("RGB")
    except Exception as e:
        log.warning(f"Thumbnail BG download failed: {e}")
        return None


def generate_thumbnail(
    title:       str,
    hook_text:   str,
    output_path: str,
    pexels_query: str = "money india",
) -> str:
    """
    Generate a thumbnail image.
    Returns path to saved thumbnail.
    """
    # Background
    bg = _download_bg_image(pexels_query)
    if bg:
        bg = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (THUMB_W, THUMB_H), color=(20, 30, 60))

    # Dark overlay
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 160))
    bg.paste(Image.fromarray(
        __import__("numpy").array(overlay)), (0, 0),
        mask=overlay.split()[3]
    )

    draw = ImageDraw.Draw(bg)

    # Title text (large, top area)
    title_font = _get_font(88)
    clean_title = title.replace("#Shorts", "").replace("💰", "").strip()
    wrapped = "\n".join(textwrap.wrap(clean_title, width=18))

    # Draw text shadow
    for offset in [(4, 4), (-4, -4), (4, -4), (-4, 4)]:
        draw.text(
            (THUMB_W // 2 + offset[0], 120 + offset[1]),
            wrapped,
            font=title_font,
            fill=(0, 0, 0, 200),
            anchor="mt",
        )

    # Draw title
    draw.text(
        (THUMB_W // 2, 120),
        wrapped,
        font=title_font,
        fill=(255, 255, 255),
        anchor="mt",
    )

    # Gold banner at bottom
    banner_y = THUMB_H - 160
    draw.rectangle([(0, banner_y), (THUMB_W, THUMB_H)],
                   fill=(255, 193, 7))   # gold

    # Hook text in banner
    hook_font  = _get_font(52)
    short_hook = hook_text[:60] + ("..." if len(hook_text) > 60 else "")
    draw.text(
        (THUMB_W // 2, banner_y + 75),
        short_hook,
        font=hook_font,
        fill=(20, 20, 20),
        anchor="mm",
    )

    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    bg.convert("RGB").save(output_path, "JPEG", quality=95)
    log.info(f"Thumbnail saved: {output_path}")
    return output_path
