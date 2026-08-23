---
name: youtube-podcast-research
description: Discover and archive YouTube dual-host English learning podcasts — browser discovery, yt-dlp metadata/transcript collection, and trending ranking. Use when the user asks to refresh YouTube research, collect competitor podcasts, rank trending English podcast videos, or build the local YouTube corpus.
---

# YouTube Podcast Research

## Scope

This skill owns **data acquisition and ranking**:

- Discover candidates via Playwright search (delegates browser layer to `youtube-browser-automation`)
- Collect metadata, descriptions, and captions with `yt-dlp`
- Rank archived videos by views, engagement, and growth velocity
- Filter likely dual-host English podcasts

It does **not** analyze transcript structure or write scripts.

## Agent Invocation Policy

| User intent | Action |
| --- | --- |
| Discover new channels/videos | `discover_youtube_podcasts.py` |
| Refresh configured channel corpus | `collect_youtube_corpus.py` |
| Rebuild top-N from local metadata | `select_top_videos.py` |
| Rank by growth/engagement | `score_trending_videos.py` |

Do not download video or audio files. Archive metadata, descriptions, and transcript text only.

## Rate limits (non-negotiable)

Read **`CORPUS.md` § Rate limits** before any acquisition run. All yt-dlp loops use sleep/throttle defaults; agents must not disable them or fire large batches without `--smoke` first. On rate-limit errors, stop and wait ≥60 minutes.

## Corpus Contract

Read `CORPUS.md` for paths, schemas, and artifact policy.

Default root:

```text
workspace/dialogue_podcast_research/youtube_corpus/
```

## Sibling Skills

- **youtube-browser-automation** — Playwright setup and low-level search
- **youtube-corpus-analysis** — pattern analysis, transcript beats, episode briefs
- **dialogue-podcast-scriptwriting** — original two-host script drafts
- **polished-english-episode-script** — Leo/Mia show-shaped episodes

Read `WORKFLOW.md` and `CHANNELS.md` for commands and source channels.
