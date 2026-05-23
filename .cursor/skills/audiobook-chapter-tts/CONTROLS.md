# Control Text And Render Pipeline

This document is the production baseline for VoxCPM2 chapter rendering. It matches `scripts/audiobook_workspace.py` (`compose_control`, `normalize_segment_peak`) and the Pride and Prejudice chapter 002 workflow.

## Manifest Fields

| Field | Required | Role |
| --- | --- | --- |
| `globalControl` | Yes | Human/agent reference for narrator tone. **Not** injected into every `ttsText`. |
| `characterProfiles` | Multi-speaker chapters | One stable cue per dialogue speaker. Prepended in dialogue `ttsText`. |
| `segments[]` | Yes | Semantic units with `kind`, `speaker`, `deliveryCue`, `text`. |
| `cfgValue` | No | Overrides default `2.25` when set (e.g. `2.35` for slightly stronger delivery). |
| `paceCue` | No | **Opt-in only.** Omit by default; when present, prepended to narration/short controls. |
| `cleanReference` | No | Default `true`; produces `000_reference_clean.wav`. |

Per-segment optional fields:

| Field | When to use |
| --- | --- |
| `maxLen` | Override auto `max_len` for fragile short lines. |
| `renderPolicy: include_delivery_cue` | Legacy override; dialogue already keeps profile + `deliveryCue` by default. |

Do **not** add chapter-wide loudness targets (`targetSegmentRms`, `energyLevel`) or post-compose RMS normalization. Those were tried and reverted; peak-only quiet boost stays the default.

## How `compose_control` Builds `ttsText`

`globalControl` is ignored at render time. Voice identity comes from `reference_wav_path` (cleaned reference by default).

### Dialogue

| Condition | Control sent to model | `max_len` |
| --- | --- | --- |
| ≤12 words, has profile | `{profile}, {deliveryCue}` | 128 (or 56 if ≤4 words) |
| >12 words, has profile | `{profile}, {deliveryCue}` | none |
| No profile | `{deliveryCue}` (and `paceCue` if manifest has it) | by word count |

### Narration

| Condition | Control sent to model | `max_len` |
| --- | --- | --- |
| ≤12 words | `same cloned narrator, slightly slower, {deliveryCue}` | 128 (or 56 if ≤4 words) |
| >12 words | `same cloned narrator, {deliveryCue}` | none |

Word limits (code constants):

- `SHORT_SEGMENT_WORD_LIMIT` = 12 → `max_len` 128
- `VERY_SHORT_WORD_LIMIT` = 4 → `max_len` 56
- Long dialogue stays one segment; do not split at semicolons inside the same quoted turn.

## Post-Render Audio (Per Segment)

After each segment WAV is written, `normalize_segment_peak` runs:

- If peak **≥ 0.45**: leave unchanged.
- If peak **< 0.45**: scale to target peak **0.88**.

No time-stretch, trim, or RMS matching across segments. Compose concatenates segment WAVs with **0.34s** silence between them.

## Segmentation Practices That Match This Pipeline

1. **Split long narration** where the model swallows an opening word (e.g. separate “It was then disclosed…” from the following beat).
2. **Active verbs in `deliveryCue`** (`bursting out`, `deadpan comic correction`) outperform flat labels (`matter-of-fact`).
3. **13–22 word dialogue** with profile + cue tends to sound strongest; very short quips rely on tight `max_len`.
4. **Long dialogue** stays one segment with profile + `deliveryCue`; do not split at semicolons inside the same quoted turn.
5. **EPUB source**: use `segment_chapter.py` so italic fragments merge onto the previous line instead of breaking paragraphs.

## Pacing (Opt-In Only)

Do not add `paceCue` or slow reference tempo unless the user asks.

- `paceCue` in manifest — prepended when the key exists.
- `referenceTempoRatio` in `clean_reference_audio.py` (e.g. `0.88`–`0.94`) — changes cloned prosody before render.

Chapter 002 production omits both; unhurried delivery comes from reference choice and segment cues.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Stage directions spoken aloud | Long text stuffed into every segment control | Keep `globalControl` short; use per-segment `deliveryCue` only |
| Extra speech after sentence | Control string too long for short text | Shorter cue; lower `max_len`; split segment |
| Opening word swallowed (“It”) | Long narration block | Split into two narration segments |
| Segment too quiet | Short line + high `max_len` | Rerender with lower `maxLen`; peak boost applies automatically if peak < 0.45 |
| Uneven loudness between segments | Peak boost only helps very quiet peaks | Accept raw variation or master externally; do not re-enable RMS chapter normalize in scripts |
| Odd duration / unstable take | `paceCue` or slowed reference | Remove `paceCue` / reset `referenceTempoRatio` to `1.0` |

**Opt-in:** `inspect_chapter.py` when the user wants duration ratios and suspicious segments listed.

**Opt-in:** Rerender named ids only:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/<book_slug>/chapter_XXX --segments 012,027
```

## Reference Example

`workspace/pride_and_prejudice/chapter_002/000_chapter_002.segments.json` — `characterProfiles`, split `002` / `002b`, `cfgValue: 2.35`, no `paceCue`.
