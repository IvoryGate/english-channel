# Chapter Subtitles (SRT)

## When To Generate

Generate subtitles only when the user explicitly confirms the chapter audio is acceptable.

Do not generate SRT during initial rendering, segment rerenders, or compose passes unless the user asks.

## Timing Source

Subtitle timing follows the same assembly rules as `compose_chapter.py`:

1. Read segments in manifest order from `000_chapter_XXX.segments.json`.
2. Measure each segment duration from the current `NNN_<speaker>.wav` on disk.
3. Insert `interSegmentSilenceSec` between segments (default `0.34`, or the value stored in `000_chapter_XXX.run.json`).

This means externally trimmed segment WAVs are reflected in the SRT without re-rendering audio.

## Subtitle Text

- Use each segment's `text` field from the manifest.
- Strip wrapping quotation marks for display.
- Keep one semantic segment per subtitle cue.

## Output Files

- `000_chapter_XXX.srt`: standard SubRip file aligned to `000_chapter_XXX_raw.wav`.
- Optional `000_chapter_XXX.timeline.json` with per-segment `startSec` / `endSec` for debugging.

## Command

```powershell
.\.conda-env\python.exe .cursor/skills/audiobook-chapter-tts/scripts/generate_chapter_srt.py --workspace workspace/pride_and_prejudice/chapter_001
```

After manual segment trims or a compose-only pass, rerun this command to refresh subtitles.
