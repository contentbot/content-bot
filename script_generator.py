"""
script_generator.py

Generates short-form video scripts for faceless narration content
(facts / stories / quotes) using the Anthropic API.

Each script is returned as structured JSON:
{
  "title": "...",              # working title / YouTube title
  "hook": "...",                # first line, said in the first 2 seconds
  "body": ["line 1", "line 2"], # narration lines, in order
  "caption": "...",             # social caption with hashtags
  "search_terms": ["...", ...]  # keywords to pick matching background footage
}
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You write short-form (30-60 second) faceless narration video scripts \
for TikTok/YouTube Shorts in the "did you know" / bizarre-facts / short-story style.

Rules:
- Hook must grab attention in the first sentence (no throat-clearing, no "did you know" cliche unless it's genuinely the strongest option).
- Total narration should read aloud in 30-55 seconds (roughly 90-140 words).
- Plain, spoken language. Short sentences. No headers, no emojis in the narration itself.
- End on a punchy final line, not a trailing-off summary.
- Output ONLY valid JSON matching this schema, nothing else, no markdown fences:
{
  "title": string,
  "hook": string,
  "body": [string, ...],
  "caption": string,
  "search_terms": [string, string, string]
}
"""


def generate_script(topic: str, niche_notes: str = "") -> dict:
    """Generate one script for a given topic. Returns a dict matching the schema above."""
    user_prompt = f"Topic: {topic}\n"
    if niche_notes:
        user_prompt += f"Channel style notes: {niche_notes}\n"
    user_prompt += "Write one script now."

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON:\n{raw}") from e


if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "a strange fact about the deep ocean"
    script = generate_script(topic)
    print(json.dumps(script, indent=2))
