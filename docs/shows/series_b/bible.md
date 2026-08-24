# Series B — First Steps

**Show ID:** `series_b`  
**Public name:** First Steps · Easy English  
**Level:** A2-B1  
**Hosts:** Riley (female teacher/coach) & Sam (male co-learner friend)  
**Max duration:** 20 minutes (~1,400-1,900 spoken words)

## Positioning

Foundation English for learners who want a clear plan, not textbook density. Riley leads with a simple method; Sam asks the questions and doubts the listener has. Explicit episode contract in the first minute.

Packaging reference: J and May Podcast (contrarian/number promises, 15-minute framing) — **original wording only**.

## Language profile

| Dimension | Target |
| --- | --- |
| Sentence length | 8-12 words average; minimal nesting |
| Vocabulary | High-frequency 1-2K; gloss new words immediately |
| Grammar | Simple present/past/future, basic modals |
| Recap | Short recap every 4-5 minutes |
| Speed | `1.0` — never slow for level control |

## Structure (full episode)

Required draft markers:

- Teaching Plan (one spine, 2-3 parts max)
- Episode Contract (first 60 seconds: "By the end you will...")
- Learner pain hook
- Part 1 / Part 2 / Part 3 (plain labels OK for this series)
- Mid recap
- Practice prompt
- Close CTA (comment / try today / subscribe — one light line)

## Title formula

```text
[Number or contrarian promise] + [specific outcome] + (optional time box)
```

Examples (original):

- `Practice English Alone Every Day (Only 15 Minutes — Really!)`
- `You Only Need 3 Sentences to Start a Real Conversation (Not 30!)`
- `Stop Waiting for a Speaking Partner — Do This Instead`

**No episode numbers** in public titles.

**YouTube title hard limit: 100 characters.** If a title would exceed 100, trim the promise or drop optional clauses. `prepare_episode_youtube_packaging.py` fails the pack step on any title over 100, so author the `youtube.json` `title` field ≤100 from the start.

## Validation

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/shows/series_b/episode_XXX/000_episode_XXX.draft.md --profile series_b
```

## Workspace

```text
workspace/shows/series_b/
  episodes_index.json
  topic_backlog.json
  episode_XXX/
```

## Voice profiles

- Sam → `assets/voices/series_b/sam_reference_clean.wav` (source: [I-MWXTNhyGo](https://www.youtube.com/watch?v=I-MWXTNhyGo))
- Riley → `assets/voices/series_b/riley_reference_clean.wav` (source: szoPFcVl2KU, manual clip)

Character bibles: [`workspace/characters/series_b_sam/`](../../workspace/characters/series_b_sam/identity.md), [`series_b_riley/`](../../workspace/characters/series_b_riley/identity.md)

Visual anchors (thumbnail/image gen): [`configs/shows/host-visuals.json`](../../../configs/shows/host-visuals.json)
