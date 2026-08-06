# Faceless Content Bot

Generates short-form "facts / stories" narration videos and posts them
automatically. Pipeline: **topic → script → voiceover → captioned video →
YouTube (auto) + TikTok (drafted for a one-tap post)**.

## Before you start — read this

- **YouTube** can be posted to fully automatically, forever, once you do a
  one-time login (see below).
- **TikTok will not let a personal script auto-publish to the public feed.**
  Their API only allows unaudited apps to drop the video into your TikTok
  **drafts/inbox** — you still tap "Post" in the app. This bot always saves
  a ready-to-post copy to `output/tiktok_ready/` either way, so even in the
  worst case you're one tap away, not editing anything by hand.
- This needs to run somewhere that's always on — not in this chat. See
  **Running it 24/7** below for two easy, cheap ways to do that.
- You supply background footage/music (licensing is on you) and API keys.
  Nothing here scrapes stock footage sites for you.

## 1. Install

```bash
cd content-bot
python -m venv venv && source venv/bin/activate      # optional but recommended
pip install -r requirements.txt
```

`ffmpeg` must also be installed on your system (moviepy depends on it):
- Mac: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Windows: https://ffmpeg.org/download.html

## 2. Add your API keys

```bash
cp .env.example .env
```

Open `.env` and fill in:
- `ANTHROPIC_API_KEY` — required, powers the script writer. Get one at
  https://console.anthropic.com
- `TTS_VOICE` — free, no key needed, just pick a voice name
- YouTube and TikTok keys — see sections below

## 3. Add background content

- Drop 3-10 vertical (or any-ratio, it'll be cropped) `.mp4` clips into
  `assets/backgrounds/` — think satisfying/gameplay/nature loop footage.
  The bot picks one at random per video and loops it to fill the narration
  length.
- Optionally drop royalty-free background music `.mp3` files into
  `assets/music/` — it'll be auto-ducked under the narration.

Only use footage/music you have the rights to use.

## 4. Set up YouTube auto-upload (one-time)

1. Go to https://console.cloud.google.com → create a project
2. APIs & Services → Library → enable **YouTube Data API v3**
3. APIs & Services → Credentials → Create Credentials → OAuth client ID →
   Application type: **Desktop app**
4. Download the JSON, save it as
   `client_secrets/youtube_client_secret.json`
5. Run `python youtube_uploader.py` once by hand (or just run `main.py`) —
   a browser window opens asking you to log in and approve. After that, a
   token is cached and every future run is 100% automatic — no more logins.

## 5. Set up TikTok (optional, capped by TikTok's rules — see above)

Full instructions: https://developers.tiktok.com/doc/content-posting-api-get-started/
Even without this set up, finished videos still land in
`output/tiktok_ready/` ready for you (or a scheduler tool) to post.

## 6. Try it once

```bash
python main.py
```

This generates one full video end-to-end and uploads it. Check
`output/` for the rendered file and `output/tiktok_ready/` for the
TikTok-ready copy + caption.

## 7. Add more topics

Edit `topics.txt` — one idea per line. The bot picks randomly each run.
Add new ones any time; it'll never run out as long as the file isn't empty.

## Running it 24/7

Don't leave a terminal open — deploy it properly. Two easy options:

**Option A: cron on a cheap always-on VPS ($4-6/mo, e.g. a small droplet/Lightsail box)**
```bash
crontab -e
# add a line to post 3x/day at 9am, 2pm, 7pm:
0 9,14,19 * * * cd /path/to/content-bot && /path/to/venv/bin/python main.py >> log.txt 2>&1
```

**Option B: GitHub Actions (free, no server to manage)**
Create `.github/workflows/post.yml` in a repo containing this project:
```yaml
name: Post video
on:
  schedule:
    - cron: "0 14 * * *"   # daily at 14:00 UTC — adjust as you like
  workflow_dispatch: {}      # lets you also trigger it manually
jobs:
  post:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: sudo apt-get install -y ffmpeg
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TTS_VOICE: en-US-GuyNeural
```
Add your keys under repo Settings → Secrets → Actions, and commit your
`client_secrets/youtube_token.pickle` as an encrypted secret too (or store
it in a small artifact step) so YouTube auth persists between runs.

## Costs to expect

- Anthropic API: a few cents per script
- edge-tts: free
- YouTube API: free (well within quota for a few videos/day)
- Hosting: free (GitHub Actions) or a few dollars/month (VPS)

## Troubleshooting

- `FileNotFoundError: No background clips found` → add at least one `.mp4`
  to `assets/backgrounds/`
- YouTube upload skipped → you haven't set up
  `client_secrets/youtube_client_secret.json` yet, or haven't authorized
  once locally with a browser
- TikTok stuck at "staged_only" → expected unless you've completed TikTok's
  developer approval process; just post the staged file manually
