# Radar Bot — automated skills & monetization scanner

Runs on a schedule, no server required. GitHub Actions calls the Anthropic
API with web search, checks a fixed list of sources, and commits any new
findings to `findings.json`.

## Costs

Each scan run is a handful of Anthropic API calls (web search + one
completion). At every-6-hours frequency that's roughly 120 runs a month —
a few dollars of API usage, not more. Drop to `cron: "0 0 * * *"` (once a
day) in `scan.yml` if you'd rather keep it minimal.

## Changing what it looks for

Edit the `SOURCES` list and the `PROMPT` text in `scripts/scan.py`. Nothing
else needs to change — the workflow just runs whatever the script does.

## What this doesn't do

- It doesn't act on findings — no auto-purchasing, no auto-building. It only
  logs what it finds. Review and decide is still on you.
- It can hallucinate a finding if search comes back thin — spot-check
  anything before you act on it, same as you would with any research feed.
