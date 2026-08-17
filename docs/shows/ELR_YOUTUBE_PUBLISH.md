# ELR Dialogue Series — Formal YouTube Publish Workflow

Durable production contract for Series A / B / C episode packages.
Companion packaging reference: [audiobook YOUTUBE.md](../../.cursor/skills/audiobook-chapter-tts/YOUTUBE.md).

## Hard rules

1. **Resolution:** finals are **at least 2K (2560×1440)**, 16:9. Do not publish 1080p frames, covers, or mp4s.
2. **Topic first:** analyze learner-search / competitor **hot themes** before locking a title. Prefer corpus tools under `youtube-podcast-research` + `youtube-corpus-analysis` when corpus is fresh; otherwise use show `topic_backlog.json` + bible + recent ELR uploads.
3. **No politics:** skip elections, parties, wars, geopolitical conflict, and partisan culture-war framing. Stay on daily English, study methods, workplace communication, and social skills.
4. **No topic reuse:** do not repeat a prior `publicTitle` / `slug` already shipped or reserved in any series backlog with status `draft|rendering|published`, or already present under `H:\Youtube\`.
5. **Style:** covers and video backgrounds are **2D comic / hand-drawn** (not photoreal). Generate a native **16:9 final cover with typography baked into the artwork**; generate a separate native 16:9 video background with no text.
6. **Export root:** `H:\Youtube\<SeriesFolder>\episodeNN\` with **local numbering** (zero-padded, matching Pride layout vibe).

## Series folders on `H:\Youtube`

| Show | Folder |
| --- | --- |
| Series A · Daily Talk | `H:\Youtube\DailyTalk\episode01\` |
| Series B · First Steps | `H:\Youtube\FirstSteps\episode01\` |
| Series C · Polished English | `H:\Youtube\PolishedEnglish\episode01\` |

Numbering increments per series (`episode02`, …). Never put episode numbers in the **public YouTube title**.

## Deliverables per episode folder

Mirror audiobook shipping shape:

```text
H:\Youtube\<SeriesFolder>\episodeNN\
  episodeNN.mp4
  episodeNN-封面.jpg
  episodeNN.srt
  episodeNN.wav
  episodeNN.youtube_title.txt
  episodeNN.youtube_description.txt
  episodeNN.youtube.json
```

Workspace (source of truth before export):

```text
workspace/shows/series_x/episode_XXX/
  000_episode_XXX.draft.md
  000_episode_XXX.episode_manifest.json
  000_episode_XXX.raw.wav
  000_episode_XXX.thumbnail.png
  000_episode_XXX.video_bg.jpg
  000_episode_XXX.karaoke.ass
  000_episode_XXX.srt
  000_episode_XXX.mp4
  000_episode_XXX.youtube.json
  000_episode_XXX.youtube_description.txt
```

## Ordered steps (one episode)

1. **Hot-theme scan** — refresh / read trending or analysis outputs; reject political / duplicate themes.
2. **Lock topic** — write/update backlog entry (`status: rendering`); set `publicTitle`, `learnerProblem`, `hookAngle`.
3. **Script** — draft with dialogue-podcast-scriptwriting (or polished-english for C); validate profile.
4. **Manifest** — `prepare_episode_manifest.py` → turns for TTS.
5. **Render audio** — one series at a time, **audiobook-parity launch**:
   - Prefer `scripts/run_episode_render.py --manifest ...` (Python subprocess + log, same shape as `monitor_book_chapters.py`).
   - Do **not** nest long CUDA jobs inside Cursor/PowerShell `Start-Process -Wait` / Tee chains on 8GB GPUs.
   - Load VoxCPM **once** per job (`render_episode.py`); use `--skip-existing` to resume a full episode. Avoid reloading the model every few turns.
   - Selective fixups: `run_episode_render.py --manifest ... --segments p003` (overwrites those WAVs).
6. **Audio QC (required, audiobook-style)** — `check_episode.py --manifest ...` (timing + trailing silence + ASR vs turn text). Report in chat; **stop for human decision** (rerender / trim / accept). Do not compose video until audio is approved.
7. **Audio master (required for formal packs)** — see [`AUDIO_MASTERING.md`](AUDIO_MASTERING.md). Run `master_episode_audio.py` → `000_episode_XXX.master.wav` (−16 LUFS, mild denoise, report JSON). Severe 电音 still needs VoxCPM **rerender** (cfg ~2.15), not master alone.
8. **Pack (QC → master → subs → compose → export)** — one stable job, audiobook monitor style:

```powershell
cd H:\english-channel
& .\.conda-env\python.exe -u scripts\run_episode_pack.py `
  --show series_b --episode episode_001 `
  --workspace workspace\shows\series_b\episode_001 `
  --episode-num 1
```

Run through `scripts/elr.py produce`; for unattended work use
`--detach --visible-window`. Query `scripts/elr.py status --episode N` instead
of guessing from a silent terminal. The state record contains the exact log.
Subtitles use **`--scripted-only`** (audiobook timing from WAV duration + script — no 134× Whisper).  
Shortcut: `scripts\run_series_b_ep001_pack.ps1` (add `--skip-master` if master already exists).

9. **YouTube copy** — `title`, description body, tags, `coverText` layers in `youtube.json` + `youtube_description.txt`.
10. **Prompts** — `render_episode_thumbnail.py --print-prompts` (native **16:9 / 2560×1440**, comic style, exact baked cover typography).
11. **Image gen** — generate a complete thumbnail cover with the specified text baked into the composition, plus a separate subtitle-friendly video background with **no text**.
12. **Compose thumbnail** — `--from-baked-scene` / `--video-bg-from` preserves the native 16:9 baked cover. `--from-image` is legacy-only for a pre-existing 3:2 cover.
13. **Subtitles** — `pack_episode.py` uses `_master_turns` + **scripted-only** (real clip durations + script text). Karaoke: ASS `\kf`; spoken **ivory `#FFF8E7`**, waiting gray `#B0B0B0`.
14. **Compose / export** — included in pack step; compose prefers **`master.wav`** (~5 Mbps video).
15. **Backlog** — mark topic `published`; record export path.

## Resolution source of truth

`media/media_layout.py` → `WIDTH=2560`, `HEIGHT=1440`. All compose / ASS / normalize / prompts must follow it.

## Pilot vs formal

Reference-clip concat is **pilot only**. Formal uploads require original script + host render and full packaging set above.

**Audio QC note:** After VoxCPM render + concat, run `workspace/shows/tools/check_episode.py` (same flags as audiobook: trailing silence >1s, CHECK_LONG, ASR mismatch). Do not compose or export until the human accepts or fixes flagged turns.

**TTS note:** Prefer `render_episode.py` (VoxCPM clone). Interim Edge-TTS packs may exist for early pilots; re-render with VoxCPM before formal re-export when clone audio is approved.
