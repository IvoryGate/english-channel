---
name: audiobook-chapter-tts
description: Prepare audiobook chapters with semantic segmentation, delivery cues, VoxCPM2 voice cloning, per-segment rendering, selective segment regeneration, and final chapter composition. Use when the user asks to turn a book chapter into audio, split a chapter into narration/dialogue segments, add emotion or delivery tags, generate a demo, regenerate specific audiobook segments, compose chapter audio, generate SRT subtitles after audio is approved, design YouTube titles or chapter cover thumbnails, or continuously/repeatedly render a chapter range (e.g. "continuously generate chapters 39 to 61", "resume chapter render from 39", "monitor book chapters").
---

# Audiobook Chapter TTS

## Agent Invocation Policy

### Default workflow (no extra steps unless asked)

1. Create or locate the chapter workspace.
2. Build or refine `000_chapter_XXX.segments.json`.
3. Clean reference audio by default.
4. Render all segments, then compose `000_chapter_XXX_raw.wav`.
5. **Run QC self-check automatically** after compose (layer 1 + ASR on flagged segments).
6. **Report self-check results in the chat** with segment id, flags, manifest text, and ASR text when content looks wrong. **Do not write `000_chapter_XXX.qc.json` by default.**
7. **Stop and wait for user confirmation** before trim, rerender, compose-only fixes, or subtitles. Do not auto-fix flagged segments.

### Opt-in workflows (run only when the user explicitly requests them)

Do not run these proactively after a normal full-chapter render unless the user asks.

| User intent | Action |
| --- | --- |
| Rerender one or more segments | `render_chapter.py --segments 009` or `009,017` |
| Recompose without rendering | `compose_chapter.py` |
| Segment was trimmed in external audio software | `compose_chapter.py` only; do not rerender |
| Check suspicious segment timing | `inspect_chapter.py` |
| Write QC report file to disk | `check_chapter.py --write-report` |
| Generate subtitles after audio is approved | `generate_chapter_srt.py` |
| YouTube title, description, tags, timestamps, or cover image | read `YOUTUBE.md`; write `000_chapter_XXX.youtube.json`; run `prepare_youtube_packaging.py`; generate cover; run `normalize_youtube_cover.py` |
| Continuous sequential chapter render (long batch) | `monitor_book_chapters.py --start X --end Y` (background); see `WORKFLOW.md` |

Never auto-trim segment WAVs in scripts. Never regenerate segments or compose the chapter again unless the user asks.

## Self-Check Reporting Rules

When reporting QC results in chat:

- Group **content issues** first: `CHECK_LONG`, `ASR_MISMATCH`, `ASR_LONGER`, `SHORT_TOO_LONG`, etc.
- Always include the segment **manifest text** for content issues so the user can compare while listening.
- Include **ASR transcript** when ASR ran and the segment may have tail garbage or extra speech.
- Mention **trailing silence >1s** separately; silence within 1s is treated as OK and should not be emphasized.
- End with: waiting for user confirmation before any fixes.

## Quick Start

Default workspace layout:

```text
workspace/<book_slug>/chapter_001/
├── 000_chapter_001_raw.wav
├── 000_chapter_001.run.json
├── 000_chapter_001.segments.json
├── 000_chapter_001.source.txt
├── 000_chapter_001.srt
├── 000_chapter_001.youtube.json
├── 000_chapter_001.youtube_description.txt
├── 000_chapter_001.cover.jpg
├── 000_reference_clean.wav
├── 001_narrator.wav
├── 002_mrs_bennet.wav
└── ...
```

Optional: `000_chapter_001.qc.json` only when the user asks to persist a QC report.

## Workflow

1. `scripts/prepare_workspace.py` — create `workspace/<book_slug>/chapter_XXX`.
2. Chapter text in `000_chapter_XXX.source.txt` (from EPUB via `segment_chapter.py` or hand-edited).
3. Build `000_chapter_XXX.segments.json`: semantic segments, `globalControl`, `characterProfiles` for dialogue speakers, per-segment `deliveryCue`.
4. `scripts/clean_reference_audio.py` — cleaned reference by default; skip only when asked.
5. `scripts/render_chapter.py` — render all segments, peak-boost quiet WAVs, compose `000_chapter_XXX_raw.wav`, then self-check.
6. Summarize self-check in chat; wait for user approval.
7. After the user confirms audio is correct: `scripts/generate_chapter_srt.py` — write `000_chapter_XXX.srt`.
8. When the user asks for upload packaging: read **`YOUTUBE.md`** — choose one title, generate a matching cover, and assemble upload metadata.

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
- `scripts/render_chapter.py` — render all or selected segments; compose; self-check by default.
- `scripts/compose_chapter.py` — compose existing segment WAVs into final raw WAV.
- `scripts/inspect_chapter.py` — list segment durations and suspicious timing (**opt-in**).
- `scripts/check_chapter.py` — standalone QC; use `--write-report` to save JSON (**opt-in**).
- `scripts/generate_chapter_srt.py` — build `000_chapter_XXX.srt` from finalized segment WAVs (**opt-in, after audio approval**).
- `scripts/prepare_youtube_packaging.py` — resolve chapter timestamps (+3s video intro offset) and assemble upload description (**opt-in**).
- `scripts/normalize_youtube_cover.py` — normalize cover art to `2560x1440`. Modes: `auto`/`top-crop` (video bg, fills frame), `contain` (pad), `blur-fill` (blurred backdrop), `blur-fill-composite` (episode covers: blurred backdrop + sharp rounded cover, text never cropped). See `docs/shows/thumbnail_templates.md` "Cover normalization methodology" (**opt-in, after cover generation**).
- `scripts/monitor_book_chapters.py` — thin wrapper to repo `scripts/monitor_book_chapters.py`; continuous one-chapter-at-a-time render with logging (**opt-in, long batch only**).
- `scripts/render_book_chapters.py` — prepare + render a chapter range in one process (**opt-in**; no monitor logging/retry).

For details, read `WORKFLOW.md`, `CONTROLS.md`, `SEGMENTATION.md`, `VOXCPM2.md`, `QC.md`, `SUBTITLES.md`, and `YOUTUBE.md`.
