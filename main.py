"""
main.py

The orchestrator. Running this once = one full video, generated and uploaded:
  1. Pick a topic (from topics.txt) and write a script (script_generator.py)
  2. Turn the script into narration audio (tts_engine.py)
  3. Assemble the final vertical video with burned-in captions (video_builder.py)
  4. Upload to YouTube (youtube_uploader.py)
  5. Push to TikTok drafts / stage for manual posting (tiktok_uploader.py)

USAGE:
  python main.py                 # runs once, posts one video
  python main.py --loop 4        # runs every 6 hours, forever (4 posts/day)

For truly "set and forget" operation, don't run this in a chat — deploy it
somewhere always-on. See README.md for the two easy options (a cron job on
a cheap VPS, or a scheduled GitHub Action).
"""

import argparse
import os
import random
import time
from datetime import datetime

from script_generator import generate_script
from tts_engine import synthesize_narration
from video_builder import build_video
from youtube_uploader import upload_short
from tiktok_uploader import push_to_drafts

TOPICS_FILE = "topics.txt"
OUTPUT_DIR = "output"


def _next_topic() -> str:
    if not os.path.exists(TOPICS_FILE):
        raise FileNotFoundError(
            f"{TOPICS_FILE} not found. Create it with one topic idea per line."
        )
    with open(TOPICS_FILE) as f:
        topics = [line.strip() for line in f if line.strip()]
    if not topics:
        raise ValueError(f"{TOPICS_FILE} is empty. Add some topic ideas, one per line.")
    return random.choice(topics)


def run_once():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    topic = _next_topic()
    print(f"[1/5] Topic: {topic}")

    script = generate_script(topic)
    print(f"[2/5] Script written: {script['title']}")

    narration_text = script["hook"] + " " + " ".join(script["body"])
    audio_path = os.path.join(OUTPUT_DIR, f"narration_{stamp}.mp3")
    word_boundaries = synthesize_narration(narration_text, audio_path)
    print(f"[3/5] Narration recorded ({len(word_boundaries)} words)")

    video_path = os.path.join(OUTPUT_DIR, f"video_{stamp}.mp4")
    build_video(audio_path, word_boundaries, video_path)
    print(f"[4/5] Video rendered: {video_path}")

    tags = script.get("search_terms", [])
    try:
        upload_short(
            video_path,
            title=script["title"],
            description=script["caption"],
            tags=tags,
        )
    except FileNotFoundError:
        print(
            "Skipped YouTube upload — client_secrets/youtube_client_secret.json "
            "not set up yet. See README.md."
        )

    push_to_drafts(video_path, script["caption"])
    print("[5/5] Done.\n")


def run_loop(times_per_day: int):
    interval_seconds = (24 * 60 * 60) / times_per_day
    print(f"Looping forever: one video every {interval_seconds / 3600:.1f} hours")
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Run failed, will retry next cycle: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loop",
        type=int,
        default=0,
        help="If set, runs forever, posting this many times per day.",
    )
    args = parser.parse_args()

    if args.loop:
        run_loop(args.loop)
    else:
        run_once()
