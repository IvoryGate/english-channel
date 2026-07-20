# Series A — Daily Talk

**Show ID:** `series_a`  
**Public name:** Daily Talk · English Conversations  
**Level:** B1-B2  
**Hosts:** Ethan (male), Nora (female)  
**Max duration:** 20 minutes (~1,600-2,400 spoken words)

## Positioning

Intermediate daily-life English through warm peer conversation. Scene-first emotional hooks in titles; body stays daily-talk, not classroom.

Packaging reference: Speak English With Class (series prefix discipline, emotional scene hook) — **original wording only**.

## Language profile

| Dimension | Target |
| --- | --- |
| Sentence length | 12-18 words average; one clause of subordination OK |
| Vocabulary | Daily phrasal verbs, concrete social/work vocabulary |
| Grammar | Present perfect, basic conditionals, natural questions |
| Recap | One micro-pocket mid-episode (~20-45 sec dialogue) |
| Speed | `1.0` — never slow for level control |

## Structure (full episode)

Required draft markers:

- Teaching Plan (2-3 threads max)
- Structure Map
- Intro Hook → Host Intro → Early Contract
- Acts with question-flow transitions (no syllabus labels)
- Micro-Pocket
- Recycle (conflict > timetable)
- Word Tour (2-4 pre-heard phrases)
- Close with one behavior CTA

## Title formula

```text
English Podcast For [Daily Life / Easy] English Conversation | [Emotional scene hook] | Learn English
```

Examples (original):

- `English Podcast For Daily Life Conversation | When Easy English Stops Changing Your Speaking | Learn English`
- `English Podcast For Easy English Conversation | The Confidence Gap After Laundry Listening | Learn English`

**No episode numbers** in public titles.

**YouTube title hard limit: 100 characters.** The `| Learn English` suffix is optional — drop it (or trim the hook) if the title would exceed 100. `prepare_episode_youtube_packaging.py` fails the pack step on any title over 100, so author the `youtube.json` `title` field ≤100 from the start.

## Validation

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/shows/series_a/episode_XXX/000_episode_XXX.draft.md --profile series_a
```

## Workspace

```text
workspace/shows/series_a/
  episodes_index.json
  topic_backlog.json
  episode_XXX/
    000_episode_XXX.draft.md
    000_episode_XXX.meta.json
    000_episode_XXX.script.json
    000_episode_XXX.episode_manifest.json
```

## Voice profiles

- Ethan → `assets/voices/series_a/ethan_reference_clean.wav`
- Nora → `assets/voices/series_a/nora_reference_clean.wav`

Character bibles: [`workspace/characters/series_a_ethan/`](../../workspace/characters/series_a_ethan/identity.md), [`series_a_nora/`](../../workspace/characters/series_a_nora/identity.md)

Visual anchors (thumbnail/image gen): [`workspace/characters/registry.json`](../../workspace/characters/registry.json)
