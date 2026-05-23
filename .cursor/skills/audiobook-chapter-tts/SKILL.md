---
name: audiobook-chapter-tts
description: Prepare audiobook chapters with semantic segmentation, delivery cues, VoxCPM2 voice cloning, per-segment rendering, selective segment regeneration, and final chapter composition. Use when the user asks to turn a book chapter into audio, split a chapter into narration/dialogue segments, add emotion or delivery tags, generate a demo, regenerate specific audiobook segments, compose chapter audio, or generate SRT subtitles after audio is approved.
---

# Audiobook Chapter TTS

## Agent Invocation Policy

### Default workflow (no extra steps unless asked)

1. Create or locate the chapter workspace.
2. Build or refine `000_chapter_XXX.segments.json`.
3. Clean reference audio by default.
4. Render all segments, then compose `000_chapter_XXX_raw.wav`.

### Opt-in workflows (run only when the user explicitly requests them)

Do not run these proactively after a normal full-chapter render.

| User intent | Action |
| --- | --- |
| Rerender one or more segments | `render_chapter.py --segments 009` or `009,017` |
| Recompose without rendering | `compose_chapter.py` |
| Segment was trimmed in external audio software | `compose_chapter.py` only; do not rerender |
| Check suspicious segment timing | `inspect_chapter.py` |
| Generate subtitles after audio is approved | `generate_chapter_srt.py` |

Never auto-trim segment WAVs in scripts. Never regenerate segments or compose the chapter again unless the user asks.

## Quick Start

Default workspace layout:

```text
workspace/<book_slug>/chapter_001/
├── 000_chapter_001_raw.wav
├── 000_chapter_001.run.json
├── 000_chapter_001.segments.json
├── 000_chapter_001.source.txt
├── 000_chapter_001.srt
├── 000_reference_clean.wav
├── 001_narrator.wav
├── 002_mrs_bennet.wav
└── ...
```

## Workflow

1. `scripts/prepare_workspace.py` — create `workspace/<book_slug>/chapter_XXX`.
2. Chapter text in `000_chapter_XXX.source.txt` (from EPUB via `segment_chapter.py` or hand-edited).
3. Build `000_chapter_XXX.segments.json`: semantic segments, `globalControl`, `characterProfiles` for dialogue speakers, per-segment `deliveryCue`.
4. `scripts/clean_reference_audio.py` — cleaned reference by default; skip only when asked.
5. `scripts/render_chapter.py` — render all segments, peak-boost quiet WAVs, compose `000_chapter_XXX_raw.wav`.
6. After the user confirms audio is correct: `scripts/generate_chapter_srt.py` — write `000_chapter_XXX.srt`.

Production control rules (`compose_control`, `max_len`, long dialogue, post-render peak boost) are in **`CONTROLS.md`**.

## Required Segmentation Behavior

- Segment by meaning, not by fixed length.
- Keep narration, dialogue turns, speaker changes, and semantic transitions distinct.
- Store the stable narrator instruction once as `globalControl` (documentation only; not repeated in every `ttsText`).
- Define `characterProfiles` when the chapter has named speakers.
- Store only differential expression in each segment as `deliveryCue`.
- Split long narration beats if opening words are swallowed or delivery changes mid-sentence.
- For segments of 12 words or fewer, rely on compact control and automatic `max_len` (128; 56 for ≤4 words).
- Use `renderPolicy: include_delivery_cue` on long dialogue that must keep emotion in the control string.
- Allow synthesis groups for very short transition text when standalone generation is unstable.

## Rendering Rules

- Use cleaned reference audio by default.
- Do not set manifest `paceCue` unless the user explicitly wants pacing experiments.
- Preserve every segment WAV.
- Regenerating a segment overwrites that segment WAV in place.
- After regenerating any segment, recompose `000_chapter_XXX_raw.wav` only when the user asked for rerender or recompose.
- If the user manually trims segment WAVs in external audio software, only run `compose_chapter.py`; do not regenerate segments.
- Keep only raw final audio by default; do not create mastered copies unless the user asks.
- Do not add chapter-wide RMS normalization or script-side segment trimming unless the user asks.

## Utility Scripts

- `scripts/prepare_workspace.py` — create workspace.
- `scripts/segment_chapter.py` — extract/draft chapter text and segment manifest.
- `scripts/clean_reference_audio.py` — create `000_reference_clean.wav`.
- `scripts/render_chapter.py` — render all or selected segments; compose when part of a render request.
- `scripts/compose_chapter.py` — compose existing segment WAVs into final raw WAV.
- `scripts/inspect_chapter.py` — list segment durations and suspicious timing (**opt-in**).
- `scripts/generate_chapter_srt.py` — build `000_chapter_XXX.srt` from finalized segment WAVs (**opt-in, after audio approval**).

For details, read `WORKFLOW.md`, `CONTROLS.md`, `SEGMENTATION.md`, `VOXCPM2.md`, and `SUBTITLES.md`.
