---
name: series-b-first-steps
description: Write Series B (First Steps, A2-B1) two-host English learning podcast scripts for Riley & Sam with audiobook-parity delivery cues, contrarian-number hooks, learner-asks rhythm, English Listening Room brand name, and human-feel dialogue (moderate fillers on Sam, multi-line runs, long/short variation). Use when the user asks to create or revise a Series B episode script.
---

# Series B — First Steps

## Agent Invocation Policy

### Default workflow

1. Read [`competitor_script_analysis.md`](../../../docs/shows/competitor_script_analysis.md) Section B (J&May reference) and [`docs/shows/series_b/bible.md`](../../../docs/shows/series_b/bible.md).
2. Get the topic from `select_next_topic.py --show series_b --apply` (writes `workspace/shows/series_b/topic_selection_<date>.json`); or fall back to a user brief. The selector reads real competitor research and excludes already-produced topics. Reject political / duplicate themes.
3. Choose one hook template from STYLE.md §B.2 (1–3). Contrarian-number is the default and most viral.
4. Draft using [`SCRIPT_TEMPLATE.md`](SCRIPT_TEMPLATE.md) — frozen cold-open chassis, then 起承转合 per STYLE.md §B.4.
5. Tag every turn with `[Delivery: …]` per DELIVERY.md. Include `characterProfiles` block in header.
6. Run `validate_podcast_script.py --profile series_b` on the draft. Fix until `ok=true`.
7. Stop and wait for user feedback before TTS prep.

### Hard rules

- **Brand name**: every episode must speak "English Listening Room" at least once (opening, after dual intro).
- **Host intro**: Riley first (coach), Sam second (learner), fused with hook teaser.
- **Word count**: 1400–1900 spoken words. Max 20 min at `speed=1.0`.
- **Filler policy**: moderate on Sam (learner) — `uh`/`emmm`/`hmm` allowed 1 per 4–6 Sam turns. Riley (coach) near-zero fillers.
- **Delivery cues**: every turn carries `[Delivery: …]`. No exceptions.
- **Short sentences**: 8–12 words average. Gloss every new word immediately.
- **No politics, no topic reuse, no `speed` controls**.

### Opt-in workflows

| User intent | Action |
| --- | --- |
| Validate a saved draft | `validate_podcast_script.py --profile series_b` |
| Revise one section | Edit only the named section; preserve host roles and delivery cues |
| Prepare render manifest | `workspace/shows/tools/prepare_episode_manifest.py` (after approval) |

### Related skills

| Need | Skill |
| --- | --- |
| Discover / collect YouTube corpus | `youtube-podcast-research` |
| Analyze competitor patterns | `youtube-corpus-analysis` |
| Render / pack episode | [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) |

## Defaults

| Field | Value |
| --- | --- |
| Show name | First Steps |
| Channel | English Listening Room |
| Hosts | Riley (female, clear coach), Sam (male, hesitant friend) |
| Level | A2–B1 |
| Word band | 1400–1900 |
| Max duration | 20 min @ speed=1.0 |
| Competitor reference | J and May Podcast |

## Revision history

- 2026-07-19: Initial Series B specialized skill (contrarian hooks, learner-asks rhythm, brand name, audiobook delivery cues).
