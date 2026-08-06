"""
tiktok_uploader.py

IMPORTANT / READ FIRST:
TikTok's Content Posting API does not allow an unaudited app (i.e. a personal
script like this one) to publish straight to the public feed. Unaudited apps
can only push a video into the creator's TikTok inbox as a DRAFT — the human
still has to open the TikTok app and tap "Post". Full auto-publish requires
submitting your app for TikTok's audit process, which is meant for real
companies/products, not personal automation, and can take weeks with no
guarantee of approval.

So what this module actually does:
  - If you've set up TIKTOK_ACCESS_TOKEN (via TikTok's Login Kit + Content
    Posting API), it pushes the video to your TikTok drafts automatically.
  - Either way, it always copies the finished video into output/tiktok_ready/
    with a text file of the caption, so you (or a scheduling tool like Later,
    Metricool, or Buffer, which already have TikTok's audited access) can post
    it in a couple of taps.

Docs: https://developers.tiktok.com/doc/content-posting-api-get-started/
"""

import os
import shutil

import requests
from dotenv import load_dotenv

load_dotenv()

TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN")
READY_DIR = "output/tiktok_ready"


def _stage_for_manual_post(video_path: str, caption: str) -> str:
    os.makedirs(READY_DIR, exist_ok=True)
    base = os.path.splitext(os.path.basename(video_path))[0]
    dest_video = os.path.join(READY_DIR, f"{base}.mp4")
    dest_caption = os.path.join(READY_DIR, f"{base}_caption.txt")

    shutil.copy2(video_path, dest_video)
    with open(dest_caption, "w") as f:
        f.write(caption)

    return dest_video


def push_to_drafts(video_path: str, caption: str) -> dict:
    """Attempts to push the video to the TikTok inbox as a draft via the
    Content Posting API. Falls back to just staging the file locally if no
    token is configured."""

    staged_path = _stage_for_manual_post(video_path, caption)

    if not TIKTOK_ACCESS_TOKEN:
        print(
            "No TIKTOK_ACCESS_TOKEN set — video staged locally at "
            f"{staged_path} for manual posting. See tiktok_uploader.py docstring."
        )
        return {"status": "staged_only", "path": staged_path}

    # Content Posting API: initialize an inbox upload
    init_resp = requests.post(
        "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/",
        headers={
            "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": os.path.getsize(staged_path),
                "chunk_size": os.path.getsize(staged_path),
                "total_chunk_count": 1,
            }
        },
        timeout=30,
    )

    if init_resp.status_code != 200:
        print(f"TikTok init failed ({init_resp.status_code}): {init_resp.text}")
        return {"status": "staged_only", "path": staged_path}

    data = init_resp.json().get("data", {})
    upload_url = data.get("upload_url")

    if not upload_url:
        return {"status": "staged_only", "path": staged_path}

    with open(staged_path, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.put(
        upload_url,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{len(video_bytes) - 1}/{len(video_bytes)}",
        },
        data=video_bytes,
        timeout=120,
    )

    if upload_resp.status_code in (200, 201):
        print("Pushed to TikTok drafts — open the TikTok app to review & post.")
        return {"status": "drafted", "path": staged_path}

    print(f"TikTok upload step failed ({upload_resp.status_code}): {upload_resp.text}")
    return {"status": "staged_only", "path": staged_path}


if __name__ == "__main__":
    print("Run this from main.py with a real rendered video and caption.")
