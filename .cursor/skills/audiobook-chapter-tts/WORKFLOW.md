# Audiobook Chapter Workflow

## First-Time Chapter Build

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/prepare_workspace.py --book "Pride and Prejudice" --chapter 1
```

Extract chapter text from EPUB (merges italic/word continuation lines):

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/segment_chapter.py --book "Pride and Prejudice" --chapter 2 --epub "books/Pride  Prejudice (Jane Austen).epub"
```

Then create or refine:

```text
workspace/pride_and_prejudice/chapter_001/000_chapter_001.source.txt
workspace/pride_and_prejudice/chapter_001/000_chapter_001.segments.json
```

### Manifest checklist before first render

- `globalControl` — short narrator brief for agents; not injected into every segment.
- `characterProfiles` — one stable cue per dialogue speaker (see `SEGMENTATION.md`).
- `segments[]` — `kind`, `speaker`, `deliveryCue`, accurate `wordCount`; split narration if openings are swallowed.
- Optional `cfgValue` (e.g. `2.35`) if the chapter needs slightly stronger cfg adherence.
- Omit `paceCue` unless the user requested slower pacing experiments.
- Long dialogue (>35 words) that must stay emotional: `renderPolicy: include_delivery_cue`.

Control assembly and troubleshooting: **`CONTROLS.md`**.

Clean reference audio:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/clean_reference_audio.py --workspace workspace/pride_and_prejudice/chapter_001 --reference reference/40-121026/40-121026-0001.flac
```

Render and compose:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

Stop after compose unless the user asks for more.

## Opt-In: Regenerate Selected Segments

Use only when the user names specific segment ids.

One segment:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001 --segments 009
```

Multiple segments:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001 --segments 003,009,017
```

`render_chapter.py` overwrites the listed `NNN_<speaker>.wav` files and recomposes `000_chapter_001_raw.wav`.

## Opt-In: Compose Without Rendering

Use when segment WAVs already exist and the user asked to recompose only.

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/compose_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

## Opt-In: External Trimming

When a segment has extra tail audio, the user may trim the segment WAV manually in external audio software.

After saving the edited segment in place:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/compose_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

Do not rerun `render_chapter.py` unless the user also asked to regenerate audio.

## Opt-In: Inspect Segments

Use when the user asked to check timing or find suspicious segments.

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/inspect_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

## Opt-In: Subtitles After Audio Approval

Use only after the user confirms the chapter audio is correct.

Timing follows the same rules as compose:

- segment order from `000_chapter_001.segments.json`
- duration from current `NNN_<speaker>.wav` files on disk
- `0.34s` silence between segments (or the value in `000_chapter_001.run.json`)

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/generate_chapter_srt.py --workspace workspace/pride_and_prejudice/chapter_001
```

If the user later trims segments or recomposes only, rerun `generate_chapter_srt.py` when they ask for refreshed subtitles.

See `SUBTITLES.md` for format details.

## Defaults

- Workspace root: `workspace/`.
- Chapter folder: `chapter_001`, `chapter_002`, etc.
- Final audio: `000_chapter_001_raw.wav`.
- Subtitles: `000_chapter_001.srt` (opt-in output).
- Segment manifest: `000_chapter_001.segments.json`.
- Source text: `000_chapter_001.source.txt`.
- Cleaned reference: `000_reference_clean.wav`.
- Segment audio: `001_<speaker>.wav`, `002_<speaker>.wav`, etc.
- Short segment threshold: 12 words (`max_len` 128; ≤4 words → 56).
- Long dialogue profile-only threshold: 35 words (override with `renderPolicy: include_delivery_cue`).
- Post-render: peak boost if segment peak < 0.45 (target 0.88); no RMS chapter normalize.
- Inter-segment silence: 0.34 seconds.
- Reference cleaning: on by default.
- Production reference: `workspace/pride_and_prejudice/chapter_002/` (see `CONTROLS.md`).
