"""
voice_generator.py
Converts script text to speech using Microsoft Edge TTS — 100% FREE.
No API key. No limits. High quality Indian English voices.
"""

import asyncio
import logging
import os
import re

import edge_tts

import config

log = logging.getLogger(__name__)


async def _generate_async(text: str, output_path: str) -> list[dict]:
    """
    Generate speech and return word-level timing for captions.
    Returns list of: {word, start_ms, end_ms}
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=config.VOICE_NAME,
        rate=config.VOICE_RATE,
        pitch=config.VOICE_PITCH,
    )

    # Collect audio chunks and word boundaries
    audio_chunks = []
    timings = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            timings.append({
                "word":     chunk["text"],
                "start_ms": chunk["offset"] // 10000,   # convert to ms
                "end_ms":   (chunk["offset"] + chunk["duration"]) // 10000,
            })

    # Write audio file
    with open(output_path, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    log.info(f"Voice saved: {output_path} | Words: {len(timings)}")
    return timings


def generate_voice(text: str, output_path: str) -> list[dict]:
    """
    Main entry point.
    Returns word timings for subtitle generation.
    """
    # Clean text for TTS
    clean = _clean_text(text)

    log.info(f"Generating voice for {len(clean.split())} words...")
    timings = asyncio.run(_generate_async(clean, output_path))

    return timings


def _clean_text(text: str) -> str:
    """Clean text for better TTS output."""
    # Expand common abbreviations
    replacements = {
        "₹": "rupees ",
        "&": "and",
        "SIP": "S I P",
        "PPF": "P P F",
        "FD":  "F D",
        "EMI": "E M I",
        "NPS": "N P S",
        "EPF": "E P F",
        "%":   "percent",
        "vs":  "versus",
        "p.a.": "per annum",
        "p.m.": "per month",
        "lakh": "lakh",
        "cr":   "crore",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Remove emojis (TTS can't handle them)
    text = re.sub(r"[^\x00-\x7F₹]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_caption_groups(timings: list[dict], words_per_group: int = None) -> list[dict]:
    """
    Group word timings into caption chunks.
    Returns list of: {text, start_ms, end_ms}
    """
    if words_per_group is None:
        words_per_group = config.CAPTION_MAX_WORDS

    if not timings:
        return []

    groups = []
    for i in range(0, len(timings), words_per_group):
        chunk = timings[i:i + words_per_group]
        groups.append({
            "text":     " ".join(w["word"] for w in chunk),
            "start_ms": chunk[0]["start_ms"],
            "end_ms":   chunk[-1]["end_ms"],
        })

    return groups


def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using mutagen."""
    try:
        from mutagen.mp3 import MP3
        return MP3(audio_path).info.length
    except Exception:
        try:
            # Fallback: estimate from file size (~128kbps mp3)
            size = os.path.getsize(audio_path)
            return size / 16000
        except Exception:
            return 55.0   # safe default


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = (
        "Suno! If you earn 25,000 rupees per month and invest just 10 percent "
        "in S I P every month, you will have over 50 lakh rupees in 20 years. "
        "That is the power of compounding. Start today, not tomorrow. "
        "Follow for daily money tips!"
    )
    timings = generate_voice(sample, "/tmp/test_voice.mp3")
    captions = build_caption_groups(timings)
    for c in captions[:5]:
        print(c)
