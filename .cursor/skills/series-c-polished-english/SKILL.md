---
name: series-c-polished-english
description: Write Series C (Polished English, B2-C1) two-host English learning podcast scripts for Leo & Mia with audiobook-parity delivery cues, thesis-first hooks, narrative engine (起承转合 + question-flow + micro-pocket + conflict recycle + honest word tour), anti-listicle discipline, English Listening Room brand name, and human-feel dialogue (sparse fillers, Mia pushback, long/short variation). Use when the user asks to create or revise a Series C episode script.
---

# Series C — Polished English

## Agent Invocation Policy

### Default workflow

1. Read [`competitor_script_analysis.md`](../../../docs/shows/competitor_script_analysis.md) (cross-channel), [`docs/shows/series_c/bible.md`](../../../docs/shows/series_c/bible.md), [`docs/shows/strategy.md`](../../../docs/shows/strategy.md), and character identity files [`workspace/characters/leo/identity.md`](../../../workspace/characters/leo/identity.md) + [`workspace/characters/mia/identity.md`](../../../workspace/characters/mia/identity.md).
2. Get the topic from `select_next_topic.py --show series_c --apply` (writes `workspace/shows/series_c/topic_selection_<date>.json`); or fall back to a user brief. The selector reads real competitor research and excludes already-produced topics. Pick a theme + archetype (A narrative / B checklist / C topic-deep; default A). Reject political / duplicate themes.
3. Design 2–3 threads (no more). Each thread = a communicative move or sticky idea.
4. Draft using [`SCRIPT_TEMPLATE.md`](SCRIPT_TEMPLATE.md) — thesis-first hook, 起承转合 per STYLE.md §C.4, question-flow transitions, micro-pocket after first thread, conflict recycle, honest word tour.
5. Tag every turn with `[Delivery: …]` per DELIVERY.md. Include `characterProfiles` block in header.
6. Run `validate_podcast_script.py --profile series_c` on the draft. Fix until `ok=true`.
7. Stop and wait for user feedback before TTS prep.

### Hard rules

- **Brand name**: every episode must speak "English Listening Room" at least once (opening, after dual intro).
- **Host intro**: Leo first (facilitator), Mia second (listener voice), fused with hook.
- **Word count**: 2000–2800 spoken words. Max 20 min at `speed=1.0`.
- **Filler policy**: sparse — Mia may hesitate or laugh slightly more; Leo stays cleaner when tightening a phrase. Max 1 filler per 8–12 turns. No `emmm`/`额` spellings.
- **Delivery cues**: every turn carries `[Delivery: …]`. No exceptions.
- **Anti-listicle**: cap at 2–3 threads per episode. No "first pillar / second pillar" syllabus voice on-mic.
- **Daily talk fiction**: never explain production ethics on-mic ("we don't copy", "we're independent"). Reads as defensive.
- **Mia default**: experienced user with human setbacks, NOT "clueless tourist English" unless brief explicitly says beginner.
- **No politics, no topic reuse, no `speed` controls**.

### Opt-in workflows

| User intent | Action |
| --- | --- |
| Validate a saved draft | `validate_podcast_script.py --profile series_c` |
| Revise one section | Edit only the named section; preserve host roles and delivery cues |
| Prepare render manifest | `workspace/shows/tools/prepare_episode_manifest.py` (after approval) |
| Export to Studio script.json | See SCRIPT_TEMPLATE.md §Studio JSON handoff |

### Related skills

| Need | Skill |
| --- | --- |
| Discover / collect YouTube corpus | `youtube-podcast-research` |
| Analyze competitor patterns | `youtube-corpus-analysis` |
| Render / pack episode | [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) |
| Legacy Series C skill (reference) | `polished-english-episode-script` |

## Defaults

| Field | Value |
| --- | --- |
| Show name | Polished English |
| Channel | English Listening Room |
| Hosts | Leo (male, facilitator, tightens phrases), Mia (female, listener voice, stories) |
| Level | B2–C1 |
| Word band | 2000–2800 |
| Max duration | 20 min @ speed=1.0 |
| Competitor reference | English Leap class corpus (structure report, function not wording) |

## Revision history

- 2026-07-19: Initial Series C specialized skill (consolidates polished-english-episode-script rules + audiobook-parity delivery cues + brand name + human-feel dialogue).
