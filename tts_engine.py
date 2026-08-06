"""
tts_engine.py

Converts narration text to a voiced-over .mp3 using edge-tts (free, no API key).
Also returns word-level timing so video_builder.py can sync captions.
"""

import asyncio
import os
import edge_tts
from dotenv import load_dotenv

load_dotenv()

VOICE = os.environ.get("TTS_VOICE", "en-US-GuyNeural")


async def _synthesize(text: str, out_path: str) -> list:
    communicate = edge_tts.Communicate(text, VOICE)
    word_boundaries = []

    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append(
                    {
                        "text": chunk["text"],
                        "start": chunk["offset"] / 10_000_000,  # 100ns units -> seconds
                        "duration": chunk["duration"] / 10_000_000,
                    }
                )
    return word_boundaries


def synthesize_narration(text: str, out_path: str) -> list:
    """Writes narration audio to out_path (mp3) and returns word timing list."""
    return asyncio.run(_synthesize(text, out_path))


if __name__ == "__main__":
    words = synthesize_narration(
        "This is a test of the narration voice.", "/home/claude/content-bot/output/test.mp3"
    )
    print(f"Wrote test.mp3 with {len(words)} word boundaries")
