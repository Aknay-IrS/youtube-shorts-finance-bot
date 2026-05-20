"""
video_assembler.py - Uses FFmpeg directly to avoid MoviePy audio bugs.
"""
import logging
import os
import subprocess
import textwrap

import config

log = logging.getLogger(__name__)

W = config.VIDEO_WIDTH
H = config.VIDEO_HEIGHT


def get_audio_duration_ffprobe(audio_path):
    """Get exact audio duration using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ], capture_output=True, text=True, timeout=30)
        return float(result.stdout.strip())
    except Exception as e:
        log.warning(f"ffprobe failed: {e}, using mutagen")
        try:
            from mutagen.mp3 import MP3
            return MP3(audio_path).info.length
        except Exception:
            return 55.0


def build_background_video(clip_paths, total_duration, output_path):
    """Concatenate and loop clips to fill duration using FFmpeg."""
    if not clip_paths:
        # Generate a dark blue background
        cmd = [
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', f'color=c=0x0f1a2e:size={W}x{H}:duration={total_duration}:rate={config.VIDEO_FPS}',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
            output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path

    # Create concat list - loop clips to fill duration
    concat_file = output_path + '_concat.txt'
    with open(concat_file, 'w') as f:
        # Repeat clips enough times to cover duration
        repeats = int(total_duration / 5) + 3
        for _ in range(repeats):
            for clip in clip_paths:
                f.write(f"file '{os.path.abspath(clip)}'\n")

    # Concat and trim to exact duration
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_file,
        '-t', str(total_duration),
        '-vf', f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={config.VIDEO_FPS}',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '28',
        '-an', output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=300)
    if os.path.exists(concat_file):
        os.remove(concat_file)
    if result.returncode != 0:
        log.error(f"FFmpeg concat failed: {result.stderr.decode()[:500]}")
        # Fallback to solid color
        return build_background_video([], total_duration, output_path)
    return output_path


def add_overlay_and_audio(bg_video, audio_path, title, captions, total_duration, output_path):
    """Add dark overlay, title text, captions, and audio using FFmpeg."""
    
    # Build drawtext filters
    filters = []
    
    # Dark overlay
    filters.append(f'drawbox=x=0:y=0:w={W}:h={H}:color=black@0.55:t=fill')
    
    # Title text (top, first 3.5 seconds)
    clean_title = title.replace("'", "").replace('"', '').replace(':', ' ').replace('#', '')
    # Keep only ASCII for FFmpeg drawtext
    ascii_title = ''.join(c if ord(c) < 128 else ' ' for c in clean_title).strip()[:50]
    if ascii_title:
        wrapped = '\n'.join(textwrap.wrap(ascii_title, width=20))
        filters.append(
            f"drawtext=text='{wrapped}':fontsize=64:fontcolor=white:borderw=4:bordercolor=black:"
            f"x=(w-text_w)/2:y=100:enable='between(t,0,3.5)'"
        )
    
    # Caption text
    for cap in captions[:30]:  # limit captions
        start = cap['start_ms'] / 1000
        end = cap['end_ms'] / 1000
        if end <= start:
            end = start + 0.5
        text = cap['text'].upper().replace("'", "").replace('"', '')
        ascii_text = ''.join(c if ord(c) < 128 else ' ' for c in text).strip()
        if not ascii_text:
            continue
        # Wrap long captions
        if len(ascii_text) > 20:
            ascii_text = ascii_text[:20]
        filters.append(
            f"drawtext=text='{ascii_text}':fontsize=80:fontcolor=white:borderw=5:bordercolor=black:"
            f"x=(w-text_w)/2:y=(h*0.65):enable='between(t,{start:.2f},{end:.2f})'"
        )
    
    # CTA (last 4 seconds)
    cta_start = max(0, total_duration - 4)
    filters.append(
        f"drawtext=text='FOLLOW for daily tips!':fontsize=60:fontcolor=yellow:borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y=(h-200):enable='between(t,{cta_start:.2f},{total_duration:.2f})'"
    )
    
    vf = ','.join(filters)
    
    cmd = [
        'ffmpeg', '-y',
        '-i', bg_video,
        '-i', audio_path,
        '-vf', vf,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-t', str(total_duration),
        '-shortest',
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=600)
    if result.returncode != 0:
        log.error(f"FFmpeg overlay failed: {result.stderr.decode()[:500]}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr.decode()[:200]}")
    return output_path


def assemble_video(clip_paths, audio_path, captions, title, output_path):
    """Master assembly function using FFmpeg directly."""
    log.info("Assembling video with FFmpeg...")
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    # Get exact duration
    total_dur = get_audio_duration_ffprobe(audio_path)
    log.info(f"Audio duration: {total_dur:.2f}s")
    
    # Build background
    bg_path = output_path.replace('.mp4', '_bg.mp4')
    log.info("Building background...")
    build_background_video(clip_paths, total_dur + 0.5, bg_path)
    
    # Add overlay + audio
    log.info("Adding text overlays and audio...")
    add_overlay_and_audio(bg_path, audio_path, title, captions, total_dur, output_path)
    
    # Cleanup
    if os.path.exists(bg_path):
        os.remove(bg_path)
    
    log.info(f"Video ready: {output_path}")
    return output_path
