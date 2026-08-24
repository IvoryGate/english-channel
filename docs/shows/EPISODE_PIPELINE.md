# ELR Episode Pipeline — audiobook monitor parity

Durable workflow for Series A/B/C: topic selection → scriptwriting → validation → approval → visual generation → render → QC → master → pack → export.

Companion: [`ELR_YOUTUBE_PUBLISH.md`](ELR_YOUTUBE_PUBLISH.md), [`AUDIO_MASTERING.md`](AUDIO_MASTERING.md), [`VIDEO_PIPELINE.md`](VIDEO_PIPELINE.md), [`VISUAL_IDENTITY.md`](VISUAL_IDENTITY.md).

## Episode directory structure

Each episode lives under `workspace/shows/series_X/episode_XXX/` and is split into subdirectories so script, audio, video, subtitles, and reports never mix. The manifest and script-stage files stay at the episode root (the "control center"); generated artifacts go into typed subfolders.

```text
workspace/shows/series_X/episode_XXX/
  000_episode_XXX.draft.md                  # script (root)
  000_episode_XXX.youtube.json              # script metadata: hookText, coverScene, coverAction, coverOutfit*, tags (root)
  000_episode_XXX.episode_manifest.json     # render plan (root, control center)
  audio/
    turns/                                   # per-turn rendered WAVs (VoxCPM output)
      turn_001.wav ...
    _master_turns/                           # per-turn mastered WAVs
      p001_turn_001.wav ...
    000_episode_XXX.raw.wav                  # concatenated raw
    000_episode_XXX.master.wav              # mastered program (-16 LUFS / -1.5 dBTP)
    000_episode_XXX.preloudnorm.wav          # intermediate
  video/
    000_episode_XXX.cover_baked_16x9.png      # generated native 16:9 thumbnail with baked text
    000_episode_XXX.video_bg_source_16x9.png  # generated native 16:9 no-text background
    000_episode_XXX.thumbnail.png             # final thumbnail
    000_episode_XXX.video_bg.jpg              # final video bg
    000_episode_XXX.barwave.mov              # waveform overlay
    000_episode_XXX.mp4                      # final composed video (episode 015+: ELR intro + body + outro)
  subtitles/
    000_episode_XXX.words.json                # aligned words
    000_episode_XXX.karaoke.ass                # karaoke ASS
    000_episode_XXX.srt                       # SRT
  reports/
    000_episode_XXX.render_report.json
    000_episode_XXX.qc.json
    000_episode_XXX.master_report.json
    000_episode_XXX.subtitle_report.json
    000_episode_XXX.video_report.json
    000_episode_XXX.thumbnail_report.json
    000_episode_XXX.youtube_description.txt
    000_episode_XXX.youtube_title.txt
    000_episode_XXX.youtube_packaging.json
    000_episode_XXX._prompts.json
```

Old pilot artifacts are archived under `workspace/shows/series_X/_archive/episode_XXX_old_pilot/` and are not read by any tool.

All paths are resolved by `workspace/shows/tools/episode_artifacts.py::artifact_paths()` — the single source of truth. Tools that consume per-turn WAVs use `turn_wav_path()` / `master_turn_wav_path()` so the manifest still stores bare filenames (`turn_001.wav`).

## Topic selection (before scriptwriting)

Topic selection is a real-investigation flow — it is driven by actual competitor research, not static priors. It has two layers:

- **Real investigation (scrapes, anti-ban)** — `scripts/run_research_refresh.py` refreshes the local YouTube corpus via the existing rate-limited research scripts, then re-runs the offline analysis. This is the ONLY step that touches YouTube.
- **Offline selection (no scraping)** — `refresh_topic_backlog.py` → `select_next_topic.py` → (scriptwriting) → `mark_topic_done.py`. These only read local artifacts and can be run freely with zero ban risk.

### Anti-ban hard rules (non-negotiable)

`run_research_refresh.py` enforces: smoke canary before any real collect; one channel at a time; conservative caps (`--candidate-limit 40`, sleep 5–10s, channel pause 30s+); on ANY rate-limit signal it stops, writes a 60-minute cooldown marker, and refuses further runs until it expires; no discovery+collect in the same run; no parallel scraping. Slow is acceptable; account/IP bans are not.

### Flow

```text
[real investigation]  run_research_refresh.py --channel <slug>   → fresh corpus + analysis
[offline]            refresh_topic_backlog.py --all               → merge research into topic_backlog.json
[offline]            select_next_topic.py --show series_X --apply → pick next topic, write topic_selection_<date>.json
[offline]            (scriptwriting stage uses the selected topic)
[offline]            mark_topic_done.py --show series_X --episode episode_YYY --auto  → backlog status = done
```

Commands:

```powershell
# 1. Real investigation (one channel, safe) — opt-in, slow
.\.conda-env\python.exe scripts/run_research_refresh.py --channel jandmaypodcast
# 1b. Offline re-analyze only (no scraping) — re-rerun analysis after manual corpus edits
.\.conda-env\python.exe scripts/run_research_refresh.py --skip-scrape

# 2. Feed research into the backlog (offline)
.\.conda-env\python.exe workspace/shows/tools/refresh_topic_backlog.py --all

# 3. Pick the next topic (offline) — prints the chosen topic; --apply flips it to "selected"
.\.conda-env\python.exe workspace/shows/tools/select_next_topic.py --show series_a --apply

# 4. ... write the script (see Scriptwriting & validation below) ...

# 5. After the episode is produced, write back (offline)
.\.conda-env\python.exe workspace/shows/tools/mark_topic_done.py --show series_a --episode episode_003 --auto
```

`topic_backlog.json` is the single source of truth for what has been produced: each topic carries `status` ∈ {`planned`, `selected`, `draft`, `done`} and, when done, a `producedEpisode` reference. `select_next_topic.py` auto-excludes topics already matched to a produced episode (and auto-marks stale `planned`/`draft` topics `done` if their title matches an existing episode), so topic reuse is prevented structurally rather than by memory.

### Anti-homogeneity (do not clone competitors)

Studying competitors is for **demand signals** (what topics learners watch), not for copying their format, titles, or phrasing. The flow enforces this at three layers:

- **Candidate generation (`refresh_topic_backlog.py`)**
  - Each candidate records `sourceCompetitor` + `sourceTitle` + a `differentiationAngle` prompt.
  - **Per-channel cap** — at most `MAX_PER_CHANNEL_PER_SERIES = 3` candidates per (competitor channel, series) per refresh. Without this, one high-view channel (e.g. "Speak English With Class", which dominated the trending list 18/30) would flood a single series' backlog with clones of its own playbook. The cap forces candidate diversity across channels even when one channel's videos rank highest by view count.
  - **Channel → CEFR mapping** — `CHANNEL_LEVEL_HINT` assigns each known competitor channel to its correct ELR series (e.g. `Speak English With Class` / `English With HOPE` → series_b A2-B1; `Max & Mia` / `J and May` / `English Goal Podcast` / `BBC Learning English` → series_a B1-B2; `High Level Listening` / `English Unleashed` → series_c B2-C1). Falls back to spine-keyword heuristics for unknown channels. This prevents an "Easy English" channel's topics from landing in series_c, or an advanced channel's topics from landing in series_b.
  - **Stop-word-filtered dedup** — `title_overlap` filters ELR title boilerplate (`english`, `podcast`, `learn`, `daily`, `talk`, `life`, `fast`, `minutes`, `real`, `conversation`, …) before comparing. Without this filter, the shared wrapper `"English Podcast For <X> | Learn English"` made every research candidate collide with every existing topic as a false duplicate, so **fresh research data was silently dropped and the backlog never grew beyond the static seed**. This was the critical bug that made "real investigation" not actually reach the backlog; the stop-word filter is what makes the research → backlog path real.
- **Selection (`select_next_topic.py`)**
  - Exposes `sourceCompetitor` / `sourceTitle` / `differentiationAngle` in the selection record and applies a **source-diversity bonus** so selection rotates across competitors instead of clustering on one channel's playbook.
- **Scriptwriting**
  - The scriptwriter MUST read `differentiationAngle` and deliberately diverge in hook, angle, and phrasing — never clone a competitor's title or structure.

The competitor set tracks dual-host English-learning podcasts plus BBC Learning English as a trend reference (see [`COMPETITOR_CHANNELS.md`](COMPETITOR_CHANNELS.md)). Collect new channels one at a time via `run_research_refresh.py --channel <slug>`.

## Scriptwriting & validation (before render)

Each series has a specialized skill that owns the script draft, the human-feel rules, and the word band. Always start here — do not jump straight to render. [`SCRIPT_QUALITY_STANDARD.md`](SCRIPT_QUALITY_STANDARD.md) is the cross-series pre-render gate for situation-first hooks, varied episode engines, and accurate learner promises.

| Series | Skill | Word band | Profile |
| --- | --- | --- | --- |
| A · Daily Talk · B1-B2 | `.cursor/skills/series-a-daily-talk/` | 1800–2400 spoken words | `series_a` |
| B · First Steps · A2-B1 | `.cursor/skills/series-b-first-steps/` | 1400–1900 spoken words | `series_b` |
| C · Polished English · B2-C1 | `.cursor/skills/series-c-polished-english/` | 2000–2800 spoken words | `series_c` |

The legacy `dialogue-podcast-scriptwriting` skill remains as a routing fallback and still hosts `validate_podcast_script.py`.

### Workflow

1. **Read the series skill** (`SKILL.md` + `STYLE.md` + `SCRIPT_TEMPLATE.md` + `DELIVERY.md`), [`SCRIPT_QUALITY_STANDARD.md`](SCRIPT_QUALITY_STANDARD.md), and the series bible (`docs/shows/series_X/bible.md`). Get the topic from `select_next_topic.py --show <series> --apply` (writes `topic_selection_<date>.json`); or fall back to a user brief. Reject political / duplicate themes — the selector already excludes produced topics, but confirm against `ELR_YOUTUBE_PUBLISH.md` hard rules.
2. **Draft** using `SCRIPT_TEMPLATE.md` — situation-first opening, brand name "English Listening Room" spoken once after the scene has landed, flexible episode engine, every turn tagged `[Delivery: …]`, `characterProfiles` block in header.
3. **Validate** the draft until `ok=true`:

```powershell
.\.conda-env\python.exe .cursor/skills/dialogue-podcast-scriptwriting/scripts/validate_podcast_script.py `
  workspace/shows/series_X/episode_YYY/000_episode_YYY.draft.md --profile series_X
```

The validator checks: title, description, exactly two hosts, balanced turns, CTA present, word count inside the band, required structure markers (`[Teaching Plan]`, `[Structure Map]`, `[Early Contract]`, `[Host Intro]`, `[Micro-Pocket]`, `[Recycle]`, `[Word Tour]` for A/C; `[Teaching Plan]`, `[Episode Contract]` for B), `delivery:` / `emotion` fields present, and no legacy `speed` controls. Word bands are hardcoded in `PROFILE_DEFAULTS` inside the validator.

4. **Stop and wait for human approval.** Do not proceed to render until the user confirms. Do not auto-fix content issues without human confirmation — only fix validator-level issues (length, missing markers) yourself.

### Hard rules (all series)

- **Brand name**: every episode must speak "English Listening Room" at least once (opening, after dual intro).
- **Delivery cues**: every turn carries `[Delivery: …]`. No exceptions.
- **No `speed` controls** in the draft — all series use `speed=1.0` (the validator rejects the word `speed` anywhere in the text).
- **No politics, no topic reuse**.

## Tools map

| Stage | Tool | Audiobook analogue |
| --- | --- | --- |
| Topic selection (real investigation) | `scripts/run_research_refresh.py` (scrapes, anti-ban) | (none — audiobook uses provided chapters) |
| Topic selection (offline) | `refresh_topic_backlog.py` → `select_next_topic.py` → `mark_topic_done.py` | (none) |
| Script draft + validation | series skill + `validate_podcast_script.py` | (audiobook: source text QC) |
| Thumbnail + video bg | `render_episode_thumbnail.py` (now step 0 in pack) | `cover_pipeline.py` |
| Render turns + raw concat + QC | `render_episode.py` | `render_chapter.py` |
| Stable GPU launch | `scripts/elr.py produce` (preflight + serial retry/resume) | `scripts/classics.py produce --book <slug> --chapters <range>` for registered Classic Listening books |
| Production status | `scripts/elr.py status` | monitor status |
| QC report file | `check_episode.py --write-report` | `check_chapter.py --write-report` |
| Master | `master_episode_audio.py` | (audiobook: peak boost only) |
| YouTube packaging (title + description + chapter timestamps) | `prepare_episode_youtube_packaging.py` (step 5 in pack) | `prepare_youtube_packaging.py` |
| Full pack | internal `pack_episode.py`, invoked by `scripts/elr.py` | monitor + packaging |
| Subtitles | `generate_episode_subtitles.py --scripted-only --master-turns-dir` | `generate_chapter_srt.py` |

## Full production (after script approval)

For episodes `015` and later, the pack's compose stage automatically adds the approved brand clips from `assets/branding/video/`. Do not add the clips manually in an editor or append them after export; the compose stage joins their audio and video with the program in one render. The following packaging step then measures the composed intro asset and shifts all YouTube chapters by its exact duration. See [`VIDEO_PIPELINE.md`](VIDEO_PIPELINE.md#brand-open-and-close).

**Only public production entry point:** `scripts/elr.py`. It derives the episode
workspace, refreshes the manifest, serializes local GPU work, streams progress,
persists state, and verifies export before completion.

```powershell
& $py scripts/elr.py render-audio --episode 17 --series all --detach --visible-window
& $py scripts/elr.py preflight --episode 17 --series all
& $py scripts/elr.py produce --episode 17 --series all
```

### Parallel visual and audio lane

After script approval, do not leave the local GPU idle while the remote image
service generates the native 16:9 cover and no-text background:

1. Start `render-audio` immediately. Its audio-only preflight checks the draft,
   manifest coverage, title, voice references, local runtime, memory, and
   workspace capacity, but deliberately defers visual/branding/export checks.
2. Generate and review the cover and video background remotely while VoxCPM
   renders turn WAVs locally.
3. Save both visual sources in the canonical episode workspace.
4. Run full `preflight`, then `produce` or `resume`. Completed WAVs are reused;
   formal production still owns QC, mastering, subtitles, composition,
   packaging, verification, and export.

`render-audio` may overlap remote image generation only. Do not run two local
VoxCPM jobs at once; the global GPU lock continues to serialize A → B → C.

For unattended work with a visible progress window use
`--detach --visible-window`. The command prints the PID, state file, and log
path. Query the durable state at any time:

```powershell
& $py scripts/elr.py status --episode 17
```

### Why per-turn monitor?

Loading VoxCPM once for 134 turns in one process often CUDA-crashes on 8GB GPUs.
The internal monitor renders **batches of turns per subprocess** (default `--batch-size 20`):
one model load → up to N turns → unload. Retries failed batches, resumes when WAVs already exist,
then compose+QC once at the end. Do **not** set batch-size to the full episode turn count.

### GPU memory policy (8GB / stability)

One heavy GPU job at a time — enforced by the shared SQLite `gpu_heavy` lease
through `scripts/gpu_production_lock.py`. `logs/gpu_production.lock` is a
compatibility mirror.

| Rule | Why |
|------|-----|
| **`--batch-size` default 20, max 20** | One VoxCPM load per batch; tested balance between load overhead and 8GB VRAM. Entire episodes still OOM |
| **`torch.cuda.empty_cache()` between turns** | Keeps VRAM stable within a batch on 8GB GPUs |
| **Global GPU lock** on all production entry points | Prevents duplicate relaunches stacking 2× VoxCPM or VoxCPM + NVENC |
| **Render `--no-self-check` when pack uses `--qc-no-asr`** | Skips redundant Whisper load after turns; pack runs layer-1 QC only |
| **Pack compose defaults to `libx264`** (CPU) | ffmpeg NVENC contends with VoxCPM on the same NVIDIA GPU |
| **Serial series** in `scripts/elr.py` | A → B → C; never parallel renders |

`scripts/elr.py` holds the lock for the full selected series set. Internal child
render/pack subprocesses inherit the parent lock.

**Do not** start a second production script while one holds the lease. Inspect
ownership with `.\.conda-env\python.exe scripts/channel.py resources status`.
Automatic recovery requires an expired lease and a confirmed dead PID. Deleting
the compatibility lock file does not release the SQLite lease.

Resume after interrupt:

```powershell
& $py scripts/elr.py resume --episode 17 --series all --detach --visible-window
```

## Visual generation & pack (after script approval)

Visual identity is defined in [`VISUAL_IDENTITY.md`](VISUAL_IDENTITY.md) (palette / fonts / layout / per-episode flexibility). Thumbnail + video bg generation is now **step 0 of `pack_episode.py`** — it runs a `hookText` consistency check first, then calls `render_episode_thumbnail.py`.

### Before pack: generate the cover scene

1. **Print prompts**:

```powershell
& $py workspace/shows/tools/render_episode_thumbnail.py `
  --show series_b --episode episode_001 `
  --workspace workspace/shows/series_b/episode_001 `
  --print-prompts
```

2. **Built-in image generation** → save native **16:9** scene files:
   - `000_episode_XXX.cover_baked_16x9.png` (final thumbnail composition, with the exact `coverText` baked into the artwork)
   - `000_episode_XXX.video_bg_source_16x9.png` (subtitle-friendly video background; no text, letters, logos, or watermarks)

   Use `render_episode_thumbnail.py --from-baked-scene` with the first file and `--video-bg-from` with the second. The `--from-scene` path is optional for experimental programmatic overlays; `--from-image` remains only for already-generated 3:2 covers.

3. **Fill `youtube.json`** with `coverScene` / `coverAction` / `coverOutfitFemale` / `coverOutfitMale` / `tags`. **Do not hand-write `hookText` or `title`** — both are auto-synced from draft `Title:` when you run `prepare_episode_manifest.py` or at pack step 0 (`episode_youtube_meta.py`). **Never reuse the previous episode's scene/outfit/action** — see per-episode flexibility policy in [`VISUAL_IDENTITY.md`](VISUAL_IDENTITY.md).

### Pack (one-dragon)

After both images are saved, the production controller performs thumbnail,
render, QC, master, subtitles, compose, packaging, verification, and export:

```powershell
& $py scripts/elr.py produce --episode 17 --series series_b
```

If either image is absent, formal `preflight`/`produce` stops before packaging.
`render-audio` is the only supported way to render reusable turn WAVs before
those visuals arrive; do not skip the gate for a formal episode.

## Render (after manifest)

```powershell
$py = ".\.conda-env\python.exe"
$man = "workspace/shows/series_b/episode_001/000_episode_001.episode_manifest.json"

# Long GPU job — stable launcher (same idea as monitor):
& $py scripts/run_episode_render.py --manifest $man --skip-existing

# Or direct (shorter jobs):
& $py workspace/shows/tools/render_episode.py --manifest $man
```

`render_episode.py` by default:
1. Renders turns (one VoxCPM load)
2. Concats `000_episode_XXX.raw.wav`
3. **QC self-check** in chat (layer 1 + ASR on flagged turns)

Flags: `--no-compose`, `--no-self-check`, `--segments p003`, `--skip-existing`.

Selective rerender then recompose — **do not** call `render_episode.py` directly from Cursor agent shell after a full production run (VRAM/RAM fragmentation → crash). Use the GPU-safe repair tool instead:

```powershell
& $py workspace/shows/tools/repair_episode_qc.py `
  --manifest $man --write-report
```

`pack_episode.py` runs this automatically before strict QC (`--no-auto-qc-repair` to disable).

### Series C QC pattern (Word Tour)

Series C `[Word Tour + Close]` uses slow mirror echoes (`Hook.`, `Tangent.`, sign-off `This is Mia.`). VoxCPM often generates 5–9s hallucinations on **single-word** turns → `SHORT_TOO_LONG` (blocking). Mitigations (layered):

1. **Script:** mirror echoes should be 2–4 words (`Hook — got it.`), not bare one-word lines (see Series C `SCRIPT_TEMPLATE.md`).
2. **Manifest:** `prepare_episode_manifest.py` caps `maxLen=28` for 1-word turns (was 56).
3. **Pack:** `repair_episode_qc.py` trims trailing silence when possible, then re-renders blocking turns **one subprocess at a time** with GPU lock, re-composes `raw.wav`, loops up to 3 rounds.

Timing-only flags (`CHECK_LONG` on slow Word Tour repeats) remain advisory and do not block pack when ASR/content is fine.

## Pack (after human audio approval)

One job: **thumbnail (step 0) → QC → master → scripted subs → compose → export**. See [Visual generation & pack](#visual-generation--pack-after-script-approval) above for step 0 details.

**YouTube title hard limit (100 chars).** `prepare_episode_youtube_packaging.py` (step 5) fails the pack if `youtube.json` `title` exceeds 100 characters — YouTube silently truncates or rejects longer titles. Author the title ≤100 from the start; the `| Learn English` suffix on Series A titles is optional and should be dropped first if a title is over 100. The same guard runs in `export_episode_to_youtube_dir.py` as a safety net.

**Workspace-only production.** The public controller accepts `--skip-export` on
`produce` and `resume`. This keeps the verified MP4, WAV, subtitles, thumbnail,
YouTube metadata, and reports in the canonical episode workspace while skipping
the duplicate copy under `H:\Youtube`. Repository-managed production uses this
mode unless an external upload directory is explicitly requested.

```powershell
& $py scripts/elr.py produce --episode 17 --series series_b
```

The state file identifies the exact run log. Subtitles use **scripted-only**
(no per-turn Whisper pass).

Resume when master exists:

```powershell
& $py scripts/elr.py resume --episode 17 --series series_b
```

Do not skip required cover, manifest, QC, or export checks for a formal package.

## YouTube packaging (step 5, post-audio)

After audio is rendered + mastered, `prepare_episode_youtube_packaging.py` builds the upload title and description **with real chapter timestamps** from the spoken turn durations. This mirrors the audiobook's `prepare_youtube_packaging.py`.

### Why post-audio

Chapter timestamps must reflect the actual spoken timeline, so this step runs only after turn WAVs exist. If audio is missing it fails fast with `Missing turn audio for timeline: ...turn_001.wav. Run render first.` — do not run it before render.

### What it does

1. Builds a cumulative turn timeline from rendered turn WAV durations + `interTurnSilenceSec`.
2. Resolves chapter markers to **video timestamps** (audio start + `intro_offset_sec`, default 3s, matching the composed video's intro).
3. Assembles the description: opening hook (`youtube.json` `description`) → chapter timestamps block → optional highlights / engagement question → subscribe CTA → hashtags (from `tags`).
4. Writes to `reports/`:
   - `000_episode_XXX.youtube_description.txt` (consumed by the export step)
   - `000_episode_XXX.youtube_title.txt`
   - `000_episode_XXX.youtube_packaging.json` (resolved markers + timeline audit)

### Marker sources (first non-empty wins)

1. **Explicit** — `youtube.json` `chapterMarkers`: `[{"turnId": "p001", "label": "Intro"}, ...]`. Use this for hand-tuned chapters.
2. **Auto-derived (viewer-facing labels)** — each draft `## ` section maps to the first dialogue turn after it, but the **published chapter title** comes from learner-facing copy, not internal beat names:
   - **Intro** → `youtube.json` `hookText`
   - **Teaching / Body / Part N** → `[Teaching Plan]` Thread/Part lines in order
   - **Micro-Pocket** → `[Micro-Pocket]` phrase replay note (e.g. `Slow replay: mid-stream & join in`)
   - **Recycle / Pattern Interrupt** → `[Recycle]` summary sentence
   - **Word Tour** → `[Word Tour]` phrase preview
   - **Close** → `Recap & your practice`
   Never ship raw headers like `Teaching Dialogue` or `Meta Pivot` to YouTube.

### Standalone run

```powershell
& $py workspace/shows/tools/prepare_episode_youtube_packaging.py `
  --workspace workspace/shows/series_b/episode_001 `
  --episode episode_001
```

It is also wired as **step 5 of `pack_episode.py`** (between compose and export), so the one-dragon pack produces it automatically.

## Agent behavior

1. Use the `elr-episode-production` Skill and `scripts/elr.py` for all formal
   render/pack/export work.
2. Once scripts are approved, start `render-audio` while generating visuals
   remotely. After visuals are approved, run full preflight and `produce`.
3. For a background run, use `--detach --visible-window`
   and report the printed PID, state path, and log path immediately.
4. Answer progress questions with `scripts/elr.py status`; do not start a second
   job because a terminal appears quiet.
5. Resume an interrupted job with `resume`, never `produce --force`, unless the
   user explicitly requests new audio.
6. After the final production state reaches `DONE`, write the topic back as done so the next selector
   excludes it: `workspace/shows/tools/mark_topic_done.py --show <series>
   --episode <episode_id> --auto`.

### Do not

- Run 134-turn Whisper subtitle alignment in agent shell (use `--scripted-only`).
- Start production through a low-level compatibility script.
- Auto-fix flagged turns without human confirmation.

## Revision history

- 2026-08-03: Added the public `scripts/elr.py render-audio` stage. Agents now
  start resumable local VoxCPM turn rendering immediately after script approval
  while remote cover/background generation runs concurrently. Audio-first
  preflight defers visual-only checks; formal `produce`/`resume` retains every
  visual, QC, mastering, subtitle, compose, packaging, verification, and export
  gate.
- 2026-07-20: YouTube title 100-char hard limit enforced in the pipeline. `prepare_episode_youtube_packaging.py` and `export_episode_to_youtube_dir.py` now fail if `youtube.json` `title` exceeds 100 characters (YouTube's upload limit), with an actionable error pointing at the offending title. Series A/B/C bibles' Title formula sections now document the ≤100 rule and that the optional `| Learn English` suffix should be dropped first. Existing Series A episode_001/002 titles were shortened (109/111 → 93/95) and the `youtube.json` `title` fields updated to match.
- 2026-07-20: Hardened the topic-selection candidate pipeline so fresh research actually reaches the backlog. Three fixes in `refresh_topic_backlog.py`: (1) **stop-word-filtered dedup** — `title_overlap` now strips ELR title boilerplate (`english`/`podcast`/`learn`/`daily`/`talk`/`life`/…) before comparing; previously the shared wrapper `"English Podcast For <X> | Learn English"` made every research candidate collide with every existing topic as a false duplicate, so `addedCount` was always 0 and the backlog never grew beyond the static seed — the "real investigation" was silently discarded. (2) **Per-channel cap** (`MAX_PER_CHANNEL_PER_SERIES = 3`) so one high-view channel cannot flood a single series' backlog with clones of its own playbook (the trending list was 18/30 from one channel). (3) **Channel → CEFR hint map** (`CHANNEL_LEVEL_HINT`) assigns each known competitor channel to its correct ELR series, with spine-keyword fallback, so an "Easy English" channel's topics don't land in series_c. Validated: a post-maxandmia refresh now adds 9/6/2 source-tracked candidates to series_a/b/c respectively, capped at 3 per channel, with `differentiationAngle` exposed for the scriptwriter.
- 2026-07-21: Added **English Goal Podcast** (`englishgoalpodcast`, series_a B1-B2) to the competitor reference set. Channel registry moved to [`COMPETITOR_CHANNELS.md`](COMPETITOR_CHANNELS.md) (includes full topic-investigation flow summary).
- 2026-07-20: Expanded the competitor set from 3 to 11 channels and added anti-homogeneity guardrails. `DEFAULT_CHANNELS` now includes dual-host competitor podcasts surfaced by discovery + BBC Learning English as a trend reference (see [`COMPETITOR_CHANNELS.md`](COMPETITOR_CHANNELS.md)). `refresh_topic_backlog.py` now records `sourceCompetitor` + `sourceTitle` + `differentiationAngle` per candidate; `select_next_topic.py` exposes those in the selection record and applies a source-diversity bonus so selection rotates across competitors instead of clustering on one channel's playbook. Rationale: tracking only the original 3 channels risked both narrow trend bias and homogeneity (copying a single competitor's style → reportable + uncompetitive). Collect new channels one at a time via `run_research_refresh.py --channel <slug>`.
- 2026-07-20: Added a real-investigation Topic selection stage before scriptwriting. `scripts/run_research_refresh.py` is the only step that scrapes — it wraps the existing rate-limited research scripts with anti-ban hard rules (smoke canary first, one channel at a time, conservative caps, 60-min cooldown on any rate-limit signal, no parallel, no discovery+collect in one run). Three offline scripts (no scraping) consume the research: `refresh_topic_backlog.py` merges research signals into `topic_backlog.json`, `select_next_topic.py` scores planned topics by trend signal + series fit and picks the next one (writing `topic_selection_<date>.json`), and `mark_topic_done.py` writes back `status=done` + `producedEpisode` after an episode is produced. The selector auto-excludes topics already matched to a produced episode, so topic reuse is prevented structurally. `topic_backlog.json` is now the single source of truth for what has been produced.
- 2026-07-20: QC now raises on issues + YouTube upload texts co-located with final products + no-text video background. (1) `check_episode.py` gained `--strict` (exit 1 when any segment is flagged for review or chapter-level flags fire, e.g. `HAS_REVIEW_SEGMENTS`/`COMPOSE_DRIFT`); `pack_episode.py` passes `--strict` so QC problems stop the pipeline and print a clear message instead of silently passing. (2) `export_episode_to_youtube_dir.py` now also writes `000_episode_XXX.youtube_title.txt` + `000_episode_002.youtube_description.txt` into the workspace `video/` dir (next to the mp4), so the upload-ready copy/paste texts sit with the final program — not only in `reports/` and the `H:\Youtube\<Show>\episodeNN\` export folder. (3) Video background must be a separate no-text image: `render_episode_thumbnail.py --video-bg-from <video_bg_source.png>` consumes a text-free scene render (`videoBgImagePrompt`: "absolutely no text/letters/logos/watermarks"); without it `video_bg.jpg` falls back to the text-baked cover and the cover's baked words leak into the video behind the subtitles. Generate `cover_source.png` (3:2, with baked hook text) AND `video_bg_source.png` (no text) per episode.
- 2026-07-19: GPU/hardware video encoding + redundant-QC skip — `compose_media_video.py` auto-detects NVENC (NVIDIA) and falls back to libx264 `veryfast`; QSV/AMF opt-in via `--encoder`. Encoder is real-probed (an outdated NVIDIA driver lists h264_nvenc but can't open it). Default libx264 preset lowered to `veryfast` (quality gated by VBR bitrate caps, not preset). `run_all_series_full.py` now defaults `--qc-no-asr` so pack's QC skips Whisper (render's compose_and_qc already ran full ASR), removing the redundant ~2–3 min/series ASR pass.
- 2026-07-19: Added YouTube packaging stage (step 5 of `pack_episode.py`) — `prepare_episode_youtube_packaging.py` builds the upload title + description with real chapter timestamps from rendered turn durations; auto-derives markers from draft `## ` headers or uses explicit `youtube.json` `chapterMarkers`; runs post-audio only.
- 2026-07-19: Episode directory restructure — split into `audio/` `video/` `subtitles/` `reports/` subdirs; `artifact_paths()` is the single source of truth; old pilot artifacts archived under `_archive/`.
- 2026-07-19: Added Visual generation & pack stage — step 0 of `pack_episode.py` now does hookText consistency check + thumbnail/video bg generation; `--skip-thumbnail` flag; references `VISUAL_IDENTITY.md`.
- 2026-07-19: Added Scriptwriting & validation stage (before render) — wires the three specialized series skills + `validate_podcast_script.py` word-band gate into the main pipeline so agents do not skip straight to render.
- 2026-07-17: Audiobook-parity render self-check + detached pack launcher + scripted subtitles.
