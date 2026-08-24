# Audiobook Chapter QC

Automated checks reduce manual listening by flagging suspicious segments before you approve a chapter.

## When To Run

- **Default:** runs automatically after `render_chapter.py` compose (no report file).
- **Standalone:** run manually when the user asks for QC outside render.
- **Persist report:** add `--write-report`.

Run after rendering, re-rendering selected segments, manual segment trims, or compose-only passes.

Do not run during initial segmentation unless the user asked for QC.

## Command

Layer 1 + layer 2 (default during render; standalone without report file):

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/check_chapter.py --workspace workspace/pride_and_prejudice/chapter_018
```

Persist JSON report:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/check_chapter.py --workspace workspace/pride_and_prejudice/chapter_018 --write-report
```

Layer 1 only:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/check_chapter.py --workspace workspace/pride_and_prejudice/chapter_018 --no-asr
```

Skip self-check during render:

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/render_chapter.py --workspace workspace/pride_and_prejudice/chapter_018 --no-self-check
```

ASR uses `faster-whisper` (`base` model) on flagged segments by default. If CUDA libraries are unavailable, the script falls back to CPU automatically.

```powershell
.\.conda-env\python.exe -m pip install faster-whisper
```

Or reinstall project requirements:

```powershell
.\.conda-env\python.exe -m pip install -r apps/worker-py/requirements.txt
```

## Output

- **Default:** console summary only; agent relays results in chat with manifest text and ASR for content issues.
- **Optional:** `000_chapter_XXX.qc.json` when `--write-report` is set.

## Trailing Silence Rule

Trailing silence **≤1.0s** is treated as OK. Only silence **>1.0s** raises `TRAILING_SILENCE`.

## Segment Flags

| Flag | Meaning |
| --- | --- |
| `MISSING` | Segment WAV listed in manifest but missing on disk |
| `CHECK_LONG` | Duration per word is unusually high; likely extra speech or tail |
| `CHECK_FAST` | Duration per word is unusually low; likely truncation |
| `TRAILING_SILENCE` | More than 1.0s low-energy tail after speech; optional trim |
| `TOO_QUIET` | Peak below 0.45 |
| `CLIPPING` | Samples exceed 1.0 (true digital overs) |
| `SHORT_TOO_LONG` | Very short text (≤4 words) but long audio (≥5s) |
| `ASR_MISMATCH` | Whisper transcript differs materially from manifest text |
| `ASR_LONGER` | Transcript has many more words than expected |
| `ASR_SHORTER` | Transcript has many fewer words than expected |

## Chapter Flags

| Flag | Meaning |
| --- | --- |
| `COMPOSE_DRIFT` | `000_chapter_XXX_raw.wav` duration differs from segment sum + silence |
| `RAW_MISSING` | Final raw WAV missing |
| `RAW_SAMPLE_RATE_MISMATCH` | Raw WAV sample rate differs from segments |
| `SAMPLE_RATE_MISMATCH` | Segment WAV sample rates are inconsistent |

## Defaults

- `warnSecPerWordHigh`: 0.7
- `warnSecPerWordLow`: 0.14
- `warnTrailingSilenceSec`: 1.0 (only flags when tail silence is **greater than** 1.0s)
- `shortTooLongSec`: 5.0 for ≤4-word segments
- `composeDriftSec`: 0.5
- `asrMatchRatio`: 0.75

## Workflow

1. Render or recompose the chapter.
2. Run `check_chapter.py`.
3. Listen only to segments listed with `status=review`.
4. Trim, rerender, or approve segments; rerun QC until review count is acceptable.
5. Generate subtitles only after the chapter passes QC.

`inspect_chapter.py` remains a lightweight timing table. Use `check_chapter.py` for the full report.
