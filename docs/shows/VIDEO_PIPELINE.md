# ELR Video Pipeline

End-to-end packaging for dialogue podcast episodes: thumbnail, karaoke subtitles, and ffmpeg video compose.

Audio quality before this stage: [`AUDIO_MASTERING.md`](AUDIO_MASTERING.md) (QC → master → then subtitles/compose).  
Publish flow: [`ELR_YOUTUBE_PUBLISH.md`](ELR_YOUTUBE_PUBLISH.md).

## Layout

Static **2560×1440 (2K)** background + **above-head** ASS karaoke + **lower-middle** audio waveform panel.

- Subtitles: top-center above hosts (`MarginV≈100`); waiting words warm gray, spoken highlight **ivory `#FFF8E7`**
- Karaoke: ASS `\kf` progressive fill (PrimaryColour = spoken, SecondaryColour = waiting)
- Waveform: fixed-position frequency bars (FFT), bottom-aligned, grow upward only — no horizontal scroll

## Brand open and close

Episodes **15 and later** are composed as one continuous program:

```text
English Listening Room intro → episode body (karaoke + waveform) → English Listening Room outro
```

The approved source assets live under `assets/branding/video/`:

- `english-listening-room-intro.mp4`
- `english-listening-room-outro.mp4`

`compose_episode_video.py` adds both automatically when the episode identifier ends in `015` or higher. The assets are scaled to the 2K program canvas and their audio is joined to the mastered body audio in the same encode, so there is no separate full-length second transcode. Episodes `001`–`014` retain their existing body-only format. Use `--no-branding` only for an explicit exception or troubleshooting run.

The packaging step runs after compose and reads the compose report. For branded episodes it measures the approved intro asset and adds that exact duration to every YouTube chapter timestamp; this prevents the prior body-only three-second offset from drifting chapter links. The packaging report records both `videoIntroOffsetSec` and `videoIntroOffsetSource` for audit.

## Cover / background (production)

**Recommended:** generate a **scene without text**, then overlay hook typography in code (keeps hosts consistent, text crisp).

1. Print prompts (includes fixed host visual anchors from `workspace/characters/registry.json`):

```powershell
& $py workspace/shows/tools/render_episode_thumbnail.py `
  --show series_b --episode episode_001 --workspace $ws --print-prompts
```

2. Generate two images with the image-generation tool (16:9, target 1920×1080):
   - `000_episode_XXX.scene_source.png` — hosts + scene, **no text**
   - `000_episode_XXX.video_bg_source.png` — same scene, cleaner center for subtitles

3. Normalize scene + overlay text:

```powershell
& $py workspace/shows/tools/render_episode_thumbnail.py `
  --show series_b --episode episode_001 --workspace $ws `
  --from-scene workspace/shows/series_b/episode_001/000_episode_001.scene_source.png `
  --video-bg-from workspace/shows/series_b/episode_001/000_episode_001.video_bg_source.png
```

See `docs/shows/thumbnail_templates.md` for host visual policy and `coverText` fields.

`--dev-pil` exists only for quick local experiments.

### Three cover modes

- **`--from-baked-scene <cover_baked_16x9.png>`** — native 16:9 cover with typography baked into the artwork; the production default. It preserves the completed composition and uses a separate no-text background scene.
- **`--from-scene <cover_scene_16x9.png>`** — optional native 16:9 no-text scene with programmatic `coverText` overlay.
- **`--from-image <cover_source.png>`** — legacy-only path for an existing cover with hook text baked into pixels. It produces a blur-fill composite and should not be used for new episodes.

### Critical: the video background must be text-free

In **both** modes, `video_bg.jpg` (the still behind the karaoke subtitles in the composed mp4) MUST come from a separate **no-text** image:

```powershell
& $py workspace/shows/tools/render_episode_thumbnail.py `
  --show series_b --episode episode_002 --workspace $ws `
  --from-baked-scene workspace/shows/series_b/episode_002/video/000_episode_002.cover_baked_16x9.png `
  --video-bg-from workspace/shows/series_b/episode_002/video/000_episode_002.video_bg_source.png
```

`video_bg_source_16x9.png` is generated from the `videoBgImagePrompt` ("absolutely no text, letters, logos, or watermarks anywhere"). Always generate both a native 16:9 baked cover and a separate native 16:9 background per episode; the latter must reserve clean subtitle and waveform space.

Series accent colors live in `workspace/shows/tools/show_config.json` under each show's `thumbnail` block. See also `docs/shows/thumbnail_templates.md`.

## Artifact convention

For episode workspace `workspace/shows/series_X/episode_XXX/`:

| File | Purpose |
| --- | --- |
| `000_episode_XXX.youtube.json` | `hookText` for thumbnail |
| `000_episode_XXX.episode_manifest.json` | Turn script (used as alignment reference) |
| `000_episode_XXX.raw.wav` | Concat peak-boosted turns (pre-master) |
| `000_episode_XXX.master.wav` | Formal program audio (−16 LUFS); preferred for subs/compose/export |
| `000_episode_XXX.master_report.json` | Measured LUFS / true peak before & after |
| `000_episode_XXX.thumbnail.png` | YouTube thumbnail |
| `000_episode_XXX.video_bg.jpg` | Video background still |
| `000_episode_XXX.words.json` | faster-whisper word timestamps |
| `000_episode_XXX.karaoke.ass` | Karaoke subtitles |
| `000_episode_XXX.srt` | Plain SRT export |
| `000_episode_XXX.mp4` | Final video |

## Commands

Use project Python (`docs/LOCAL_RUNTIME.md`):

```powershell
$py = ".\.conda-env\python.exe"
$ws = "workspace/shows/series_b/episode_001"

# 1) Thumbnail + video background (scene gen + text overlay)
& $py workspace/shows/tools/render_episode_thumbnail.py `
  --show series_b --episode episode_001 --workspace $ws `
  --from-scene workspace/shows/series_b/episode_001/000_episode_001.scene_source.png `
  --video-bg-from workspace/shows/series_b/episode_001/000_episode_001.video_bg_source.png

# 2) After human audio QC — master (see AUDIO_MASTERING.md)
& $py workspace/shows/tools/master_episode_audio.py `
  --manifest "$ws/000_episode_001.episode_manifest.json"

# 3) Word alignment + ASS + SRT (prefers master.wav when present)
$env:KMP_DUPLICATE_LIB_OK = "TRUE"
& $py workspace/shows/tools/generate_episode_subtitles.py `
  --show series_b --episode episode_001 --workspace $ws --device cpu

# 4) ffmpeg compose (prefers master.wav; episodes 015+ include ELR intro/outro automatically)
#    Encoder auto-selects NVENC (NVIDIA GPU) when the driver supports it,
#    otherwise libx264 veryfast. Quality is gated by -b:v 5M / -maxrate 6M
#    (VBR), not by the preset, so veryfast is visually equivalent to medium
#    for this static-background + subtitle content. Override with
#    --encoder qsv|amf|libx264 and --preset <name> as needed.
& $py workspace/shows/tools/compose_episode_video.py `
  --show series_b --episode episode_001 --workspace $ws
```

## Pilot shortcut (reference audio)

Before full VoxCPM render is ready, concat host reference clips:

```powershell
& $py workspace/shows/tools/prepare_reference_concat_audio.py `
  --output workspace/shows/series_b/episode_001/000_episode_001.raw.wav `
  --clips assets/voices/series_b/riley_reference_clean.wav assets/voices/series_b/sam_reference_clean.wav
```

Manifest turns must match the spoken reference text for meaningful `referenceCoverage` in `words.json`.

## Implementation map

| Module | Role |
| --- | --- |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/host_visuals.py` | Fixed host visual anchors + scene prompts |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/thumbnail_overlay.py` | Class-style layered text on scene |
| `workspace/characters/registry.json` | Six-host visual registry |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/turn_alignment.py` | Split words by manifest turn |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/thumbnail_compositor.py` | `--dev-pil` fallback only |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/align_media_words.py` | faster-whisper word align |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/generate_karaoke_ass.py` | ASS `\kf` progressive karaoke fill |
| `.cursor/skills/audiobook-chapter-tts/scripts/media/compose_media_video.py` | ffmpeg filter graph |
| `workspace/shows/tools/master_episode_audio.py` | Per-turn cleanup + loudnorm master |
| `workspace/shows/tools/render_episode_thumbnail.py` | CLI |
| `workspace/shows/tools/generate_episode_subtitles.py` | CLI |
| `workspace/shows/tools/compose_episode_video.py` | CLI + episode-15 branding gate |

## Dependencies

- `Pillow` — thumbnail compositor
- `faster-whisper` — word alignment (`apps/worker-py/requirements.txt`)
- `ffmpeg` on PATH — video compose. If absent, the project uses the local Remotion ffmpeg binary installed by `npm install`.

Optional: bundle fonts under `assets/fonts/` for libass portability on Windows.
