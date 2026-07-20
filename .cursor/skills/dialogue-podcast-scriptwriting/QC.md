# Dialogue Podcast Script QC

## Required Checks

Before presenting a draft, verify:

- `Title:` promises one specific learner outcome.
- `Description:` matches the actual lesson.
- Exactly two hosts appear unless the user requested guests.
- Host roles are stable: one learner proxy, one coach.
- Turns are balanced enough that neither host becomes a narrator.
- Each teaching beat includes a natural example, not only explanation.
- The script includes at least one practice loop for the listener.
- The ending has one clear CTA or learner action.
- The script is original and does not copy transcript passages.
- Current-model render handoff uses `emotion` / `delivery` notes when performance matters; do not require old `speed` controls.

## Common Issues

| Code | Meaning | Fix |
| --- | --- | --- |
| `MISSING_TITLE` | No `Title:` line | Add a specific outcome title |
| `MISSING_DESCRIPTION` | No `Description:` line | Add a concise YouTube-style description |
| `HOST_COUNT` | More or fewer than two hosts | Merge or rename speakers |
| `TURN_IMBALANCE` | One host dominates | Convert explanation into Q&A |
| `TOO_SHORT` | Script is below target length | Add practice beats or examples |
| `TOO_LONG` | Script is above target length | Remove repeated explanations |
| `MISSING_CTA` | No final listener action | Add one practice/comment/subscribe action |
| `POLISHED_STRUCTURE` | A polished_english draft is missing a core show block | Add the missing teaching plan, structure map, micro-pocket, recycle, or word tour marker |
| `MISSING_DELIVERY` | A polished_english draft has no delivery/emotion guidance | Add section-level delivery notes or render-handoff emotion/delivery fields |
| `MISSING_HOST_INTRO` | A polished_english formal draft hooks but never introduces the hosts | Add a brief Leo/Mia intro after the hook, then return to the topic |

## Manual Review Questions

- Would a learner immediately understand why this episode matters?
- Can the listener repeat useful phrases without reading?
- Does the dialogue sound like two people talking, not a textbook?
- Are examples culturally general and safe for a broad English-learning audience?
- Could the script later be segmented into one-speaker TTS turns without rewriting?

## Polished English Checks

Apply these checks when `Show Profile: polished_english`, `polished_english`, Leo/Mia, or the user asks for the Polished English show:

- First 30-45 seconds establish a stake: paradox, pain, promise, or vivid scene.
- Formal episodes use hook first, then a brief Leo/Mia self-intro, then the episode theme.
- `Teaching Plan` has 2-3 threads, not a sprawling list.
- `Structure Map` names cold open, early contract, micro-pocket, recycle, word tour, and close.
- Formal episode target is 15-20 minutes, about 1.9k-2.8k spoken English words; shorter scripts are labeled as smoke demos.
- Each act adds a new scene, objection, example, or transformation. Do not explain the same concept repeatedly under different wording.
- The core learning mechanism is clear: one problem -> one phrase cluster -> one usable sentence.
- Early contract casually previews a slow recap or word tour.
- Full episodes include one micro-pocket after the first major thread unless intentionally waived.
- Recycle is a fresh mini-scene with resistance, not a dry timetable.
- Word tour has 2-4 items, all heard earlier in the dialogue.
- Leo tightens phrases briefly; Mia brings lived friction and is not a default helpless beginner.
- On-mic language avoids "pillar", "chapter", "vocabulary section", and defensive originality disclaimers.
- Delivery notes mark clear performance shifts, especially hook, micro-pocket, word tour, and close.
- No `speed` field is required in draft or handoff.

## Script Validator

Use the validator for saved drafts:

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/dialogue_podcast_research/drafts/episode_001.md
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py workspace/dialogue_podcast_research/drafts/polished_001.md --profile polished_english --min-words 1900 --max-words 3000
```

The validator is a floor, not a full editorial review. Passing it does not replace the manual checks above.
