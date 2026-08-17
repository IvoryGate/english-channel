---
name: elr-episode-production
description: Preflight, render, monitor, resume, verify, and export approved English Listening Room Series A/B/C episodes. Use after scripts are approved to overlap local audio rendering with remote visual generation, or after native 16:9 visuals are ready to produce, monitor, recover, verify, and export one or all series.
---

# ELR Episode Production

Use the single repository entry point for formal episode production. It derives
all workspaces from series and episode number, runs A/B/C serially, streams every
child process, persists status, resumes existing turn WAVs, and promotes only a
verified complete upload package.

## Commands

Run from the repository root with the project Python:

```powershell
$py = ".\.conda-env\python.exe"

# Inspect scripts, manifests, visuals, runtime, memory, disk, and metadata.
& $py scripts/elr.py preflight --episode 17 --series all

# Audio-first: start local VoxCPM while cover/background image generation runs remotely.
& $py scripts/elr.py render-audio --episode 17 --series all --detach --visible-window

# Foreground: progress stays visible in the current terminal.
& $py scripts/elr.py produce --episode 17 --series all

# Background with a visible Windows console for an unattended run.
& $py scripts/elr.py produce --episode 17 --series all --detach --visible-window

# Read durable state even if the production terminal is hidden or closed.
& $py scripts/elr.py status --episode 17

# Continue after an interruption; completed turn WAVs are reused.
& $py scripts/elr.py resume --episode 17 --series all --detach --visible-window
```

Use `--series series_a|series_b|series_c` for one series. The batch size is 20
by default and may not exceed 20. Use `--force` only when the user explicitly
wants existing turn audio regenerated.

## Workflow

1. Confirm the script is approved. This Skill does not invent or revise content
   during a production run.
2. When visuals are not ready, immediately start `render-audio` and generate the
   cover/background through the remote image tool at the same time. Audio-first
   preflight still enforces script length, 98% manifest coverage, title length,
   voice references, runtime, memory, and workspace disk. It defers only visual,
   branding, and export checks and writes turn WAVs only.
3. After the native 16:9 cover/background are approved, run `preflight`. Resolve
   every `ERROR`; formal production must not bypass any visual or packaging gate.
4. Run `produce` (or `resume` after an interruption). It reuses completed turn
   WAVs, then performs QC, mastering, subtitles, composition, packaging,
   verification, and export. Prefer foreground when the user wants live progress; otherwise
   use `--detach --visible-window` and immediately report the PID, state path,
   and log path printed by the command.
5. Use `status` for progress. Do not infer activity from a silent chat command
   and do not start a second job while the current PID is alive.
6. If the process is interrupted, use `resume`, not `produce --force`.
7. Completion means state `DONE` and three verified upload directories when
   `--series all` was selected. A workspace MP4 by itself is not completion.

## State And Failure Handling

Current state lives at `logs/elr_runs/episode_NNN.json`; the exact run log is in
its `logPath`. State records phase, PID, heartbeat, current series, per-series
status, command, and failure details.

- `STARTING` or `RUNNING` with a dead PID is interrupted and safe to resume.
- `DONE` with phase `AUDIO_DONE` means turn WAVs are ready, not that an upload
  package is complete; finish with `produce`/`resume` after visuals are ready.
- A failed preflight never loads VoxCPM.
- A stale GPU lock may be removed only after its PID is confirmed dead.
- Series run A → B → C and never share the GPU concurrently.
- Remote image generation may overlap the local `render-audio` job because it
  does not consume the workstation GPU or production lock.
- Video is written as `.partial.mp4`; exports are built in `.incomplete` and
  become final only after media and package verification.

## Boundaries

Do not call `monitor_episode_production.py`, `run_all_series_full.py`,
`resume_episode_production.py`, or `launch_episode_pack.py` as public entry
points. They remain internal compatibility layers invoked by `scripts/elr.py`.

For content drafting use the matching series scriptwriting Skill. For detailed
artifact definitions and QC rules read `docs/shows/EPISODE_PIPELINE.md` and
`docs/shows/ELR_YOUTUBE_PUBLISH.md`.
