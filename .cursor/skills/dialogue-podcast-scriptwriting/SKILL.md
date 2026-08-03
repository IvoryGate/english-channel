---
name: dialogue-podcast-scriptwriting
description: Write two-person English learning podcast scripts for ELR Series A/B/C (Ethan/Nora, Riley/Sam, Leo/Mia). Use when the user asks to create a two-host dialogue podcast episode, generate podcast titles/descriptions, or validate a saved dialogue script. For YouTube research or competitor analysis, use youtube-podcast-research and youtube-corpus-analysis instead.
---

# Dialogue Podcast Scriptwriting

## Agent Invocation Policy

### Default workflow

1. Clarify the episode learner problem, target level, show series (A/B/C), approximate duration, and host names if not provided.
2. Read the matching show bible in `docs/shows/series_{a,b,c}/bible.md`.
3. If the user asks for **Series C**, `polished_english`, Leo/Mia, or full narrative-engine structure, read `POLISHED_ENGLISH.md` and prefer **polished-english-episode-script**.
4. **Series A** (Ethan/Nora, B1-B2): daily-talk + Class-style packaging; profile `series_a`.
5. **Series B** (Riley/Sam, A2-B1): episode contract + simple parts; profile `series_b`.
6. When market-informed drafting is requested, read **youtube-corpus-analysis** outputs — not raw competitor transcripts.
7. Read `docs/shows/SCRIPT_QUALITY_STANDARD.md`, then use `RESEARCH.md`, `SCRIPT_TEMPLATE.md`, and series bibles; draft original dialogue with exactly two hosts and a situation-first opening.
8. Run `QC.md`; stop after the draft and wait for user feedback before TTS prep.

### Render / pack (after script approval)

See `docs/shows/EPISODE_PIPELINE.md`. **Production monitor** (audiobook parity):

1. **Full job:** `scripts/monitor_episode_production.py --detach --force ...`  
   Per-turn VoxCPM render (retry on crash) → master → scripted subs → compose → export.  
   Log: `logs/monitor_episode_<show>_<episode>.log`
2. Do **not** block chat; poll log when user asks.
3. Human QC after render self-check; pack runs automatically in monitor (master always refreshed unless `--skip-master` added later).

### Opt-in workflows

| User intent | Action |
| --- | --- |
| Validate a saved script file | `validate_podcast_script.py --profile series_a|series_b|series_c` |
| Validate legacy polished_english draft | `validate_podcast_script.py --profile series_c` |
| Extract host reference clips (ops) | `extract_host_reference_clips.py` |
| Prepare render manifest | `workspace/shows/tools/prepare_episode_manifest.py` |
| Render episode (VoxCPM) | `scripts/run_episode_render.py --manifest ...` (long jobs) |
| Pack episode (master + video) | `scripts/launch_episode_pack.py --detach ...` (background + log) |
| Rewrite one section | Revise only the named section and preserve host roles |

### Related skills (do not duplicate here)

| Need | Skill |
| --- | --- |
| Playwright / browser session | `youtube-browser-automation` |
| Discover / collect / rank YouTube corpus | `youtube-podcast-research` |
| Analyze patterns / transcript beats / briefs | `youtube-corpus-analysis` |
| Leo/Mia formal episode structure + JSON export | `polished-english-episode-script` |

Do not download YouTube audio or video. Do not copy transcript passages into scripts.

## Output Contract

When drafting a new episode, include:

```text
Title: ...
Description: ...
Target Level: ...
Hosts: Host A, Host B
Show Profile: general | series_a | series_b | series_c | polished_english

[Intro Hook]
Host A: ...
Host B: ...

[Teaching Dialogue]
Host A: ...
Host B: ...

[Practice]
Host A: ...
Host B: ...

[Recap And CTA]
Host A: ...
Host B: ...
```

## Utility Scripts

- `scripts/validate_podcast_script.py` — check a saved script for title, description, two-host turn-taking, length, CTA, and optional `polished_english` structure markers.

For details, read `WORKFLOW.md`, `RESEARCH.md`, `SCRIPT_TEMPLATE.md`, `POLISHED_ENGLISH.md`, and `QC.md`.
