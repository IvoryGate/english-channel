---
name: audiobook-chapter-tts
description: Prepare audiobook chapters with semantic segmentation, delivery cues, VoxCPM2 voice cloning, per-segment rendering, selective segment regeneration, and final chapter composition. Use when the user asks to turn a book chapter into audio, split a chapter into narration/dialogue segments, add emotion or delivery tags, generate a demo, regenerate specific audiobook segments, or compose chapter audio.
---

# Audiobook Chapter TTS

## Quick Start

Use this skill when producing chapter audio from a book source and reference voice.

Default workspace layout:

```text
workspace/<book_slug>/chapter_001/
├── 000_chapter_001.raw.wav
├── 000_chapter_001.run.json
├── 000_chapter_001.segments.json
├── 000_chapter_001.source.txt
├── 000_reference_clean.wav
├── 001_narrator.wav
├── 002_mrs_bennet.wav
└── ...
```

## Workflow

1. Create or locate the chapter workspace with `scripts/prepare_workspace.py`.
2. Extract or place the chapter text as `000_chapter_XXX.source.txt`.
3. Build `000_chapter_XXX.segments.json` with semantic units and `deliveryCue` values.
4. Clean reference audio by default with `scripts/clean_reference_audio.py`; skip only when the user asks.
5. Render all segments or selected segments with `scripts/render_chapter.py`.
6. Compose the final chapter with `scripts/compose_chapter.py`.
7. Inspect durations and likely bad cases with `scripts/inspect_chapter.py`.

## Required Segmentation Behavior

- Segment by meaning, not by fixed length.
- Keep narration, dialogue turns, speaker changes, and semantic transitions distinct.
- Store the stable narrator instruction once as `globalControl`.
- Store only differential expression in each segment as `deliveryCue`.
- Do not put long global controls in every short segment.
- For segments of 12 words or fewer, use compact control and a `max_len` cap.
- Allow synthesis groups for very short transition text when standalone generation is unstable.

## Rendering Rules

- Use cleaned reference audio by default.
- Preserve every segment WAV.
- Regenerating a segment overwrites that segment WAV in place.
- After regenerating any segment, recompose `000_chapter_XXX.raw.wav`.
- Keep only raw final audio by default; do not create mastered copies unless the user asks.

## Utility Scripts

- `scripts/prepare_workspace.py`: create `workspace/<book_slug>/chapter_XXX`.
- `scripts/segment_chapter.py`: extract/draft chapter text and segment manifest.
- `scripts/clean_reference_audio.py`: create `000_reference_clean.wav`.
- `scripts/render_chapter.py`: render all or selected segments, then compose.
- `scripts/compose_chapter.py`: compose existing segment WAVs into final raw WAV.
- `scripts/inspect_chapter.py`: list segments, durations, missing files, and suspicious timing.

For details, read `WORKFLOW.md`, `SEGMENTATION.md`, and `VOXCPM2.md`.
