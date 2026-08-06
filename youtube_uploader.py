from __future__ import annotations
"""
youtube_uploader.py

Uploads a finished video to YouTube (works great for Shorts if the video is
vertical and under 60s). Fully automatable after the one-time browser auth.

Setup (one-time):
  1. https://console.cloud.google.com -> create a project
  2. Enable "YouTube Data API v3"
  3. Create OAuth client credentials, type "Desktop app"
  4. Download the JSON, save as client_secrets/youtube_client_secret.json
  5. Run this file once by hand -> a browser opens -> log in & approve
     -> a token.json is cached in client_secrets/ so future runs need no
        human interaction at all.
"""

import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secrets/youtube_client_secret.json"
TOKEN_FILE = "client_secrets/youtube_token.pickle"


def _get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
) -> str:
    """Uploads video_path to YouTube. Returns the resulting video ID."""
    youtube = _get_authenticated_service()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags or [],
            "categoryId": os.environ.get("YOUTUBE_CATEGORY_ID", "24"),
        },
        "status": {
            "privacyStatus": os.environ.get("YOUTUBE_PRIVACY_STATUS", "public"),
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")
    return video_id


if __name__ == "__main__":
    print("Run this from main.py with a real rendered video, title, and description.")
