# YouTube Trending Research And Playwright Discovery

## Goal

Split YouTube podcast research into independently operable skills with a shared worker library, so browser automation, corpus collection, analysis, and scriptwriting can evolve separately.

## Scope

Included:

- Shared library: `apps/worker-py/worker/youtube_podcast_research/`
- **youtube-browser-automation** — Playwright sessions and search
- **youtube-podcast-research** — discover, collect, rank trending
- **youtube-corpus-analysis** — patterns, transcript beats, briefs, reports
- **dialogue-podcast-scriptwriting** — slimmed to script drafting + validation only

## Status

Completed.

## Validation

- Python compile for worker package and skill scripts
- `run_tests.py` for dialogue podcast + corpus analysis tests

