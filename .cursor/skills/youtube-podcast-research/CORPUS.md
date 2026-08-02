# Corpus Contract

Shared local workspace for YouTube podcast research skills.

## Root

```text
workspace/dialogue_podcast_research/youtube_corpus/
```

Generated artifacts stay local and should not be committed by default.

## Layout

```text
youtube_corpus/
  channels.json
  collection_summary.json
  browser_profile/
  discovery/
    browser_search_latest.json      # from youtube-browser-automation
    discovery_latest.json           # from discover_youtube_podcasts.py
  analysis/                         # written by youtube-corpus-analysis
  <channel_slug>/
    channel.json
    selected_videos.json
    videos/<video_id>/
      metadata.json
      description.txt
      transcript.txt
      collection_status.json
```

## Artifact Policy

- Allowed: metadata, descriptions, captions/transcripts, search-result cards
- Forbidden: downloaded video/audio files (except one-off voice reference ops under `assets/voices/`)

## Rate limits (mandatory)

YouTube will **rate-limit or block** aggressive yt-dlp batches. All acquisition scripts must throttle requests.

**Defaults** (implemented in `apps/worker-py/worker/youtube_podcast_research/rate_limit.py`):

| Knob | Default | Meaning |
| --- | --- | --- |
| `sleep_interval` | 5s | yt-dlp minimum sleep between internal requests |
| `max_sleep_interval` | 10s | yt-dlp random sleep ceiling |
| `request_pause` | 5s | Extra sleep between each video metadata/transcript step |
| `channel_pause` | 30s | Sleep between channels in one collect run |
| `enrich_pause` | 6s | Sleep between each `--enrich` video in discovery |
| `max_enrich` | 30 | Cap discovery enrich batch size per run |

**Agent rules:**

1. Always run `--smoke` first after any rate-limit incident or long absence.
2. Never run full `--enrich --dual-host-only` on hundreds of URLs in one shot; use `--max-enrich 30` (default).
3. Prefer `--channel <slug>` one at a time instead of all channels when refreshing.
4. Lower `--candidate-limit` (default **40**, was 80) before raising sleep — fewer calls beats faster calls.
5. On `RATE_LIMIT` / `try again later` errors, **stop immediately** and wait **≥60 minutes** before retrying.
6. Voice reference audio download (`extract_host_reference_clips.py`) is **ops-only**, max **2 videos per run**, never loop discovery + download in one session.

**Example safe refresh (one channel):**

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --channel speakenglishwithclass --top-n 20 --candidate-limit 40 --refresh
```

**Example safe discovery enrich:**

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/discover_youtube_podcasts.py --enrich --dual-host-only --max-enrich 20 --enrich-pause 8
```

## Skill Ownership

| Path | Writer skill | Reader skills |
| --- | --- | --- |
| `discovery/` | youtube-browser-automation, youtube-podcast-research | youtube-corpus-analysis |
| `<channel>/videos/` | youtube-podcast-research | youtube-corpus-analysis |
| `analysis/trending_videos.json` | youtube-podcast-research | youtube-corpus-analysis, scriptwriting |
| `analysis/*.json`, report `.md` | youtube-corpus-analysis | scriptwriting, polished-english |
| `browser_profile/` | youtube-browser-automation | youtube-browser-automation, discovery |
