from __future__ import annotations
"""
video_builder.py

Assembles the final vertical (1080x1920) video from:
  - a narration audio file (from tts_engine.py)
  - word-level timing (for karaoke-style burned-in captions)
  - a background video clip (you supply these — see assets/backgrounds/)
  - optional background music (assets/music/), ducked under the narration

You need to drop your own royalty-free background clips into
assets/backgrounds/*.mp4 (loopable gameplay/nature/satisfying clips work well
for faceless content) and, optionally, music into assets/music/*.mp3.
This script does not fetch footage for you — do not scrape stock sites without
checking their license terms.
"""

import os
import random
import textwrap

from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    afx,
)

W, H = 1080, 1920
BACKGROUNDS_DIR = "assets/backgrounds"
MUSIC_DIR = "assets/music"


def _pick_random(dir_path: str, exts: tuple) -> str | None:
    if not os.path.isdir(dir_path):
        return None
    files = [f for f in os.listdir(dir_path) if f.lower().endswith(exts)]
    return os.path.join(dir_path, random.choice(files)) if files else None


def _make_caption_clips(word_boundaries: list, duration: float) -> list:
    """Word-by-word bottom-third captions, synced to narration audio."""
    clips = []
    # group words into short chunks of ~3-4 words so text isn't too jumpy
    chunk_size = 4
    for i in range(0, len(word_boundaries), chunk_size):
        chunk = word_boundaries[i : i + chunk_size]
        if not chunk:
            continue
        text = " ".join(w["text"] for w in chunk)
        start = chunk[0]["start"]
        end = chunk[-1]["start"] + chunk[-1]["duration"]
        txt_clip = (
            TextClip(
                textwrap.fill(text, width=20),
                fontsize=70,
                font="DejaVu-Sans-Bold",
                color="white",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(W - 120, None),
                align="center",
            )
            .set_start(start)
            .set_end(min(end, duration))
            .set_position(("center", H * 0.72))
        )
        clips.append(txt_clip)
    return clips


def build_video(
    narration_audio_path: str,
    word_boundaries: list,
    output_path: str,
    background_path: str | None = None,
    music_path: str | None = None,
) -> str:
    narration = AudioFileClip(narration_audio_path)
    duration = narration.duration

    background_path = background_path or _pick_random(BACKGROUNDS_DIR, (".mp4", ".mov"))
    if not background_path:
        raise FileNotFoundError(
            f"No background clips found in {BACKGROUNDS_DIR}/. Add at least one .mp4 there."
        )

    bg = VideoFileClip(background_path)
    # loop/crop background to fill the narration duration and vertical frame
    if bg.duration < duration:
        loops = int(duration // bg.duration) + 1
        bg = bg.loop(n=loops)
    bg = bg.subclip(0, duration)

    # center-crop to 1080x1920
    bg = bg.resize(height=H) if bg.h / bg.w < H / W else bg.resize(width=W)
    bg = bg.crop(
        x_center=bg.w / 2, y_center=bg.h / 2, width=min(W, bg.w), height=min(H, bg.h)
    )

    captions = _make_caption_clips(word_boundaries, duration)
    video = CompositeVideoClip([bg, *captions], size=(W, H)).set_duration(duration)

    music_path = music_path or _pick_random(MUSIC_DIR, (".mp3", ".wav"))
    if music_path:
        music = AudioFileClip(music_path).fx(afx.audio_loop, duration=duration)
        music = music.volumex(0.12)  # ducked well under narration
        final_audio = CompositeAudioClip([music, narration])
    else:
        final_audio = narration

    video = video.set_audio(final_audio)
    video.write_videofile(
        output_path, fps=30, codec="libx264", audio_codec="aac", threads=4, preset="medium"
    )

    narration.close()
    bg.close()
    return output_path


if __name__ == "__main__":
    print("Run this via main.py — it needs a narration file and word timings to work.")
