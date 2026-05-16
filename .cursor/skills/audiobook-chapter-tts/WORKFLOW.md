# Audiobook Chapter Workflow

## First-Time Chapter Build

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/prepare_workspace.py --book "Pride and Prejudice" --chapter 1
```

Then create or refine:

```text
workspace/pride_and_prejudice/chapter_001/000_chapter_001.source.txt
workspace/pride_and_prejudice/chapter_001/000_chapter_001.segments.json
```

Clean reference audio:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/clean_reference_audio.py --workspace workspace/pride_and_prejudice/chapter_001 --reference reference/40-121026/40-121026-0001.flac
```

Render and compose:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

## Regenerate Segments

Overwrite one segment and recompose:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001 --segments 009
```

Overwrite multiple segments and recompose:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_001 --segments 003,009,010
```

Compose without rendering:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/compose_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

Inspect:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/inspect_chapter.py --workspace workspace/pride_and_prejudice/chapter_001
```

## Defaults

- Workspace root: `workspace/`.
- Chapter folder: `chapter_001`, `chapter_002`, etc.
- Final audio: `000_chapter_001.raw.wav`.
- Segment manifest: `000_chapter_001.segments.json`.
- Source text: `000_chapter_001.source.txt`.
- Cleaned reference: `000_reference_clean.wav`.
- Segment audio: `001_<speaker>.wav`, `002_<speaker>.wav`, etc.
- Short segment threshold: 12 words.
- Inter-segment silence: 0.34 seconds.
- Reference cleaning: on by default.
