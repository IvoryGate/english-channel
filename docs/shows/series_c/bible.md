# Series C — Polished English

**Show ID:** `series_c`  
**Public name:** Polished English · Real Talk  
**Level:** B2-C1  
**Hosts:** Leo (male), Mia (female)  
**Max duration:** 20 minutes (~2,000-2,800 spoken words)

## Positioning

Advanced daily-talk English: depth, nuance, light debate, narrative retention engine. Teaching emerges through conversation, not meta-lessons.

Use skill: [`.cursor/skills/polished-english-episode-script/SKILL.md`](../../../.cursor/skills/polished-english-episode-script/SKILL.md)

## Language profile

| Dimension | Target |
| --- | --- |
| Sentence length | 18-25 words; asides and layered clauses OK |
| Vocabulary | Idioms, abstract nouns, workplace/social nuance |
| Grammar | Conditionals, concession, subtle register shifts |
| Recap | Micro-pocket + conflict recycle + honest word tour |
| Speed | `1.0` — never slow for level control |

## Structure (full episode)

Same narrative engine as polished-english skill:

- 起承转合 mapped to hook / develop / turn / land
- Question-flow act transitions (forbidden: "Chapter 2", "Vocabulary section")
- Anti-listicle: max 2-3 threads
- Word tour: 2-4 pre-heard items with honest payoff line

## Title formula

```text
[Concrete situation] + [outcome or paradox] — original wording, no "Learn English Tips"
```

Examples (original):

- `You Sound Polite, But Are You Actually Clear at Work?`
- `They Agreed With You — So Why Did the Room Feel Wrong?`
- `When Fluent People Still Avoid the Hard Sentence`

**No episode numbers** in public titles.

## Validation

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/shows/series_c/episode_XXX/000_episode_XXX.draft.md --profile series_c
```

## Workspace

```text
workspace/shows/series_c/
  episodes_index.json
  topic_backlog.json
  episode_XXX/
```

Legacy path `workspace/polished_english/` redirects here via README stub.

## Voice profiles

- Leo → `workspace/dialogue_podcast_research/voices/leo/leo_reference_clean.wav`
- Mia → `workspace/dialogue_podcast_research/voices/mia/mia_reference_clean.wav`

Character bibles: [`workspace/characters/series_c_leo/`](../../workspace/characters/series_c_leo/identity.md), [`series_c_mia/`](../../workspace/characters/series_c_mia/identity.md)

Visual anchors (thumbnail/image gen): [`workspace/characters/registry.json`](../../workspace/characters/registry.json)
