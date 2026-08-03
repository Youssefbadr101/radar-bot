#!/usr/bin/env python3
"""
Radar scan — calls the Anthropic API with web search enabled, checks a fixed
list of sources for new AI skills / tools / monetization plays, and merges
any new findings into findings.json.

Run manually:   ANTHROPIC_API_KEY=sk-... python3 scripts/scan.py
Run on schedule: see .github/workflows/scan.yml
"""

import json
import os
import re
import sys
from datetime import date, datetime, timezone

import urllib.request
import urllib.error

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"
FINDINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "findings.json")

# Edit this list to change what gets scanned each run.
SOURCES = [
    "github.com/ComposioHQ/awesome-claude-skills",
    "claudeskillsmarket.com",
    "skillsmp.com",
    "skills.pawgrammer.com",
    "github.com/anthropics/skills",
    "agent37.com/blog",
]

VENTURES = ["iVend", "One Life", "Mandisalab", "Passive/Digital", "General"]

PROMPT = f"""You are scanning the web for a venture studio founder (retail/vending tech,
healthy snacking CPG, Korean brand import, and a personal interest in passive
digital income). Search each of these sources for anything NEW in the last
7 days: {", ".join(SOURCES)}.

Look specifically for:
- New or notably updated Claude/AI "skills" (packaged instruction sets / plugins)
- New MCP servers or automation tools relevant to ops, retail, CPG, or e-commerce
- Monetization plays: skills, tools, or workflows that are being packaged and SOLD
  (not just used internally) — these matter most

For each real finding, output one JSON object with these exact fields:
  title (string, short)
  cat (one of: "Skill", "Tool / MCP", "Monetization play", "Marketplace")
  venture (one of: {", ".join(VENTURES)} — pick the closest fit, default "General")
  desc (1-2 sentences on what it is and why it's worth tracking)
  link (the actual URL if you have one, else "")

Return ONLY a JSON array of these objects, nothing else. No markdown fences,
no preamble. If you find nothing genuinely new, return an empty array: []
Do not invent findings — only include things you actually found via search."""


def call_claude():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    body = json.dumps({
        "model": MODEL,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": PROMPT}],
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)


def extract_json_array(text):
    """Pull the JSON array out of Claude's text response, tolerating stray text."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def load_existing():
    if os.path.exists(FINDINGS_PATH):
        with open(FINDINGS_PATH, "r") as f:
            return json.load(f)
    return []


def save(findings):
    with open(FINDINGS_PATH, "w") as f:
        json.dump(findings, f, indent=2)


def main():
    data = call_claude()

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    full_text = "\n".join(text_blocks)

    new_items = extract_json_array(full_text)
    existing = load_existing()
    existing_titles = {e["title"].strip().lower() for e in existing}

    added = 0
    today = date.today().isoformat()
    scanned_at = datetime.now(timezone.utc).isoformat()

    for item in new_items:
        title = str(item.get("title", "")).strip()
        if not title or title.lower() in existing_titles:
            continue
        existing.insert(0, {
            "title": title,
            "cat": item.get("cat", "Skill"),
            "venture": item.get("venture", "General"),
            "desc": item.get("desc", ""),
            "link": item.get("link", ""),
            "date": today,
            "source": "auto",
            "scanned_at": scanned_at,
        })
        existing_titles.add(title.lower())
        added += 1

    save(existing)
    print(f"Scan complete. {added} new finding(s) added. {len(existing)} total.")


if __name__ == "__main__":
    main()
