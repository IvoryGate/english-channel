# YouTube Podcast Research Workflow

## Setup

```powershell
.\.conda-env\python.exe -m pip install -r apps/worker-py/requirements.txt
```

For discovery, also install Playwright (see `youtube-browser-automation` skill):

```powershell
.\.conda-env\python.exe -m playwright install chromium
```

## Rate limits — read first

YouTube will throttle aggressive scraping. See **`CORPUS.md` § Rate limits** for defaults and agent rules.

- Always `--smoke` after a rate-limit incident
- Prefer **one channel at a time** for refresh
- Discovery `--enrich` is capped at **30 videos/run** by default
- Full collect default `--candidate-limit` is **40** (not 80)

## End-To-End Acquisition Loop

1. **Discover** new candidates (Playwright + optional yt-dlp enrich)
2. **Collect** configured channels (yt-dlp metadata + captions)
3. **Select** top-N locally if needed
4. **Score** trending dual-host videos
5. Hand off to **youtube-corpus-analysis** for pattern/brief generation

## Discover Dual-Host Candidates

Smoke:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/discover_youtube_podcasts.py --smoke
```

Full discovery with enrichment and dual-host filter (throttled):

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/discover_youtube_podcasts.py --enrich --dual-host-only --max-enrich 30 --enrich-pause 6
```

## Collect Configured Channels

Smoke (one video per channel):

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --smoke
```

Full collection (one channel recommended after limit incidents):

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --channel speakenglishwithclass --top-n 20 --candidate-limit 40 --language en
```

All channels (slow — ~minutes per channel with default sleeps):

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --top-n 20 --candidate-limit 40 --language en
```

Refresh one channel:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --channel jandmaypodcast --top-n 20 --refresh
```

## Rebuild Top-N Offline

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/select_top_videos.py --top-n 20
```

## Rank Trending Videos

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/score_trending_videos.py --dual-host-only --limit 30
```

Output: `workspace/dialogue_podcast_research/youtube_corpus/analysis/trending_videos.json`

## Next Step

Run **youtube-corpus-analysis** to turn the corpus into patterns, transcript beats, and episode briefs for scriptwriting.
