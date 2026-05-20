"""
thumbnail_generator.py - Generates thumbnails using Pillow.
"""
import logging
import os
import textwrap

import requests
from PIL import Image, ImageDraw, ImageFont

import config

log = logging.getLogger(__name__)
THUMB_W = 1280
THUMB_H = 720

def _get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def _download_bg(query):
    if not config.PEXELS_API_KEY:
        return None
    try:
        import os as _os
        key = _os.environ.get("PEXELS_API_KEY") or config.PEXELS_API_KEY
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 3, "orientation": "landscape"},
            timeout=10,
        )
        photos = r.json().get("photos", [])
        if not photos:
            return None
        img_r = requests.get(photos[0]["src"]["large"], timeout=15)
        from io import BytesIO
        return Image.open(BytesIO(img_r.content)).convert("RGB")
    except Exception as e:
        log.warning(f"Thumbnail BG failed: {e}")
        return None

def generate_thumbnail(title, hook_text, output_path, pexels_query="money india"):
    # Background
    bg = _download_bg(pexels_query)
    if bg:
        bg = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    else:
        bg = Image.new("RGB", (THUMB_W, THUMB_H), color=(20, 30, 60))

    # Dark overlay
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 155))
    bg = bg.convert("RGBA")
    bg.paste(overlay, (0, 0), overlay)
    bg = bg.convert("RGB")

    draw = ImageDraw.Draw(bg)
    title_font = _get_font(72)
    hook_font = _get_font(44)

    # Clean text - ASCII only for Pillow compatibility
    clean_title = ''.join(c if ord(c) < 128 else ' ' for c in title).strip()
    clean_hook = ''.join(c if ord(c) < 128 else ' ' for c in hook_text).strip()[:60]

    wrapped_title = "\n".join(textwrap.wrap(clean_title[:50], width=18))
    
    # Draw title - no anchor for multiline, use manual positioning
    lines = wrapped_title.split("\n")
    y = 100
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        w = bbox[2] - bbox[0]
        x = (THUMB_W - w) // 2
        # Shadow
        draw.text((x+3, y+3), line, font=title_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255))
        y += bbox[3] - bbox[1] + 10

    # Gold banner
    banner_y = THUMB_H - 130
    draw.rectangle([(0, banner_y), (THUMB_W, THUMB_H)], fill=(255, 193, 7))

    # Hook text in banner
    if clean_hook:
        bbox = draw.textbbox((0, 0), clean_hook, font=hook_font)
        w = bbox[2] - bbox[0]
        x = (THUMB_W - w) // 2
        draw.text((x, banner_y + 35), clean_hook, font=hook_font, fill=(20, 20, 20))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    bg.save(output_path, "JPEG", quality=90)
    log.info(f"Thumbnail saved: {output_path}")
    return output_path
