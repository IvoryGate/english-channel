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

This runs QC self-check after compose by default. Summarize results in chat and wait for user confirmation before fixes. Do not write `000_chapter_XXX.qc.json` unless the user asks.

Stop after compose + self-check unless the user asks for more.

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

## Opt-In: Automated QC Report File

Use when the user asked to persist `000_chapter_XXX.qc.json` to disk.

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/check_chapter.py --workspace workspace/pride_and_prejudice/chapter_001 --write-report
```

Add `--no-asr` to skip Whisper. See `QC.md`.

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

## Opt-In: YouTube Packaging

Use when the user asks for a YouTube title, description, tags, or cover/thumbnail for a chapter video.

Recommended after audio is approved. Subtitles may already exist, but YouTube packaging does not require them.

1. Read `000_chapter_XXX.source.txt` and `000_chapter_XXX.segments.json`.
2. Follow `YOUTUBE.md`: choose **one final title**, draft chapter-specific description fields and plot markers, then set matching `coverTitle`.
3. Write `000_chapter_XXX.youtube.json` in the chapter workspace.
4. Resolve timestamps and assemble the upload description:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/prepare_youtube_packaging.py --workspace workspace/pride_and_prejudice/chapter_037
```

Use `--intro-offset 3` by default. Increase it if the final video intro is longer than 3 seconds.

5. Generate `000_chapter_XXX.cover.jpg` using the same title as upload; prefer bright/warm compositions; avoid dead-black backgrounds (request `16:9`).
6. Normalize the cover to real YouTube size (`1920x1080`):

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/normalize_youtube_cover.py --input workspace/pride_and_prejudice/chapter_037/000_chapter_037.cover.jpg
```

7. Show the final title, description, timestamps, and cover path in chat; wait for user confirmation.
8. After approval, copy the cover to `videos/<book_display_slug>/chapter_XX/chapter_XX-封面.jpg`.

Reference style: `videos/pride&prejudice/chapter_01/chapter_01-封面.jpg`.

Do not generate titles or covers automatically after render or subtitle generation unless the user asks.

## Opt-In: Continuous Sequential Chapter Render

Use when the user asks to **continuously**, **sequentially**, or **automatically** render many chapters (e.g. "continuously generate chapters 39 to 61", "resume chapter render from 39", "keep rendering until chapter 61").

This is **optional** and separate from the default single-chapter workflow. Do not start the monitor after a normal one-chapter render unless the user asks.

### What it does

The monitor runs one chapter at a time via `render_book_chapters.py`, logs progress to `logs/monitor_book_chapters.log`, retries a failed chapter once by default, and stops on persistent failure or when interrupted.

Chapters whose `000_chapter_XXX_raw.wav` already exists are **skipped** (same as `render_book_chapters.py` without `--force`).

### Start or resume a range

Skill wrapper (preferred in agent commands):

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/monitor_book_chapters.py --start 39 --end 61
```

Equivalent repo script (same behavior):

```powershell
.\.conda-env\python.exe scripts/monitor_book_chapters.py --start 39 --end 61
```

Run in the **background** for long batches. Tell the user the log path and chapter range.

Examples:

| User intent | Command |
| --- | --- |
| Chapters 39 through 61 | `--start 39 --end 61` |
| Resume from chapter 39 through end of book | `--start 39 --end 61` |
| Only chapter 45 | `--start 45 --end 45` |
| Custom workspace root | add `--workspace-root workspace` |

Optional flags: `--retry-on-failure 0` (no retry), `--log-file logs/monitor_book_chapters.log`, `--python .conda-env/python.exe`.

### Stop

- **Graceful:** `Ctrl+C` in the monitor terminal — finishes the current chapter, then exits before the next.
- **After chapter N:** set `--end N` when starting (e.g. `--start 39 --end 45`).
- **Force re-render skipped chapters:** use `render_book_chapters.py --force` for specific chapters; the monitor does not pass `--force`.

### Monitor vs one-shot batch

| Tool | When to use |
| --- | --- |
| `monitor_book_chapters.py` | Long unattended runs, logging, retry, resume by `--start`, graceful stop |
| `render_book_chapters.py` | One-shot batch in a single process; no monitor log or per-chapter retry |

One-shot batch (no monitor):

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_book_chapters.py --start 39 --end 61
```

### Agent behavior

When the user requests continuous sequential render:

1. Confirm book/workspace (default: Pride and Prejudice under `workspace/pride_and_prejudice/`).
2. Parse `--start` / `--end` from the user's range.
3. Start the skill wrapper in the background; do not block the chat on the full run.
4. Point the user to `logs/monitor_book_chapters.log` for progress.
5. Do **not** run QC self-check reporting or wait for per-chapter approval during the monitor run unless the user asks to pause and review.

## Defaults

- Workspace root: `workspace/`.
- Chapter folder: `chapter_001`, `chapter_002`, etc.
- Final audio: `000_chapter_001_raw.wav`.
- Subtitles: `000_chapter_001.srt` (opt-in output).
- YouTube packaging: `000_chapter_001.youtube.json`, `000_chapter_001.youtube_description.txt`, `000_chapter_001.cover.jpg` (opt-in output).
- Published cover copy: `videos/<book_display_slug>/chapter_XX/chapter_XX-封面.jpg`.
- Segment manifest: `000_chapter_001.segments.json`.
- Source text: `000_chapter_001.source.txt`.
- Cleaned reference: `000_reference_clean.wav`.
- Segment audio: `001_<speaker>.wav`, `002_<speaker>.wav`, etc.
- Short segment threshold: 12 words (`max_len` 128; ≤4 words → 56).
- Long dialogue: keep one full quoted turn per segment; do not split at semicolons.
- Post-render: peak boost if segment peak < 0.45 (target 0.88); no RMS chapter normalize.
- Inter-segment silence: 0.34 seconds.
- Reference cleaning: on by default.
- Production reference: `workspace/pride_and_prejudice/chapter_002/` (see `CONTROLS.md`).
