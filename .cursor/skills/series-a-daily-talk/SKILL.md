---
name: series-a-daily-talk
description: Write Series A (Daily Talk, B1-B2) two-host English learning podcast scripts for Ethan & Nora with audiobook-parity delivery cues, frozen cold-open chassis, English Listening Room brand name, and human-feel dialogue (sparse fillers, multi-line runs, long/short sentence variation). Use when the user asks to create or revise a Series A episode script.
---

# Series A — Daily Talk

## Agent Invocation Policy

### Default workflow

1. Read [`competitor_script_analysis.md`](../../../docs/shows/competitor_script_analysis.md) Section A (Class reference) and [`docs/shows/series_a/bible.md`](../../../docs/shows/series_a/bible.md).
2. Get the topic from `select_next_topic.py --show series_a --apply` (writes `workspace/shows/series_a/topic_selection_<date>.json`); or fall back to a user brief. The selector reads real competitor research and excludes already-produced topics. Reject political / duplicate themes per [`ELR_YOUTUBE_PUBLISH.md`](../../../docs/shows/ELR_YOUTUBE_PUBLISH.md) hard rules.
3. Choose one hook template from STYLE.md §A.2 (A–E). Do not mix templates.
4. Draft using [`SCRIPT_TEMPLATE.md`](SCRIPT_TEMPLATE.md) — frozen cold-open chassis, then 起承转合 per STYLE.md §A.4.
5. Tag every turn with `[Delivery: …]` per DELIVERY.md. Include `characterProfiles` block in header.
6. Run `validate_podcast_script.py --profile series_a` on the draft. Fix until `ok=true`.
7. Stop and wait for user feedback before TTS prep.

### Hard rules

- **Brand name**: every episode must speak "English Listening Room" at least once (opening, after dual intro).
- **Host intro**: Ethan first, Nora second, fused with hook (never a separate beat).
- **Word count**: 1800–2400 spoken words. Max 20 min at `speed=1.0`.
- **Filler policy**: sparse — 1 filler (`uh`/`um`/`you know`/`I mean`) per 8–12 turns max. `Mhm`/`Hmm`/`Oh` backchannels allowed freely.
- **Delivery cues**: every turn carries `[Delivery: …]`. No exceptions.
- **No politics, no topic reuse, no `speed` controls** (per QC.md).

### Opt-in workflows

| User intent | Action |
| --- | --- |
| Validate a saved draft | `validate_podcast_script.py --profile series_a` |
| Revise one section | Edit only the named section; preserve host roles and delivery cues |
| Prepare render manifest | `workspace/shows/tools/prepare_episode_manifest.py` (after approval) |

### Related skills (do not duplicate here)

| Need | Skill |
| --- | --- |
| Discover / collect YouTube corpus | `youtube-podcast-research` |
| Analyze competitor patterns | `youtube-corpus-analysis` |
| Render / pack episode | see [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) |

## Defaults

| Field | Value |
| --- | --- |
| Show name | Daily Talk |
| Channel | English Listening Room |
| Hosts | Ethan (male, curious learner), Nora (female, warm peer coach) |
| Level | B1–B2 |
| Word band | 1800–2400 |
| Max duration | 20 min @ speed=1.0 |
| Competitor reference | Speak English With Class (English Leap Podcast) |

## Revision history

- 2026-07-19: Initial Series A specialized skill (audiobook-parity delivery cues, frozen chassis, brand name).
