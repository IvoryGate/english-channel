# English Channel

Agent-first operating system for building and running an AI-driven YouTube
channel through market research, portfolio planning, content production, safe
publication, analytics, controlled experiments, retrospectives, and iterative
optimization.

The strategic goal is a sustainable path to one million subscribers. The
system is being unified around one channel control plane while retaining
specialized dialogue, Shorts, and Classic Listening production adapters.

## Current State

The integrated baseline combines the frontend/backend VoxCPM2 platform with
Dialogue / English Listening Room research, show definitions, script skills,
resumable production, QC, packaging, and publication preflight. The Shorts
adapter and the rights-gated Classic Listening foundation are also integrated.
The Persuasion production adapter is integrated, while its 33 generated review
assets remain protected and untracked in the original source worktree. Start
with:

- [`docs/YOUTUBE_OPERATING_SYSTEM.md`](docs/YOUTUBE_OPERATING_SYSTEM.md) for the
  target product and operating model.
- [`docs/BRANCH_RECONCILIATION.md`](docs/BRANCH_RECONCILIATION.md) for the
  branch, worktree, capability, and intake inventory.
- [`docs/LEGACY_PIPELINE_PARITY.md`](docs/LEGACY_PIPELINE_PARITY.md) for the
  path-by-path evidence behind superseding the three older feature branches.
- [`docs/CHANNEL_CONTROL_PLANE.md`](docs/CHANNEL_CONTROL_PLANE.md) for the
  implemented canonical identity store, legacy/remote import, reconciliation,
  and collision workflow.
- [`docs/CHANNEL_RECONCILIATION_2026-08-24.md`](docs/CHANNEL_RECONCILIATION_2026-08-24.md)
  for the reviewed 15-item public inventory baseline and its explicit limits.
- [`docs/WEEKLY_CHANNEL_OPERATIONS_2026-08-24.md`](docs/WEEKLY_CHANNEL_OPERATIONS_2026-08-24.md)
  for the current fixed programming grid, ready inventory, production queue,
  community rhythm, and stop conditions.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for current and target system
  boundaries.
- [`docs/exec-plans/active/2026-08-17-youtube-operating-system-unification.md`](docs/exec-plans/active/2026-08-17-youtube-operating-system-unification.md)
  for the phased implementation and release gates.

## Current Monorepo Layout

- `apps/web`: Next.js frontend for job orchestration and playback.
- `apps/api`: Fastify backend for task management and queue orchestration.
- `apps/worker-py`: Python worker for VoxCPM inference pipeline.
- `packages/shared-types`: Shared TypeScript contracts.
- `packages/tooling`: CI linting and repository guard scripts.
- `docs`: System-of-record engineering documentation.
- `infra`: Local and remote deployment scaffolding.

## Quick Start

1. Install Node.js 20+ and Python 3.10-3.12.
2. Install dependencies:
   - `npm install`
   - `pip install -r apps/worker-py/requirements.txt`
3. Start local infrastructure:
   - `docker compose -f infra/docker-compose.dev.yml up -d redis`
4. Run services:
   - `npm run dev:web`
   - `npm run dev:api`

## Phase-0 E2E (Inline TTS)

1. Set API execution mode to inline:
   - PowerShell: `$env:JOB_EXECUTION_MODE="inline"`
2. Start API:
   - `npm run dev:api`
3. Submit a job:
   - `curl -X POST http://localhost:4000/jobs -H "Content-Type: application/json" -d "{\"chapterId\":\"ch1\",\"text\":\"Chapter one starts on a cold morning in London.\",\"voiceProfile\":\"default-narrator\"}"`
4. Query the returned job id:
   - `curl http://localhost:4000/jobs/<jobId>`

Artifacts are written under `artifacts/<chapterId>/<jobId>/` with `chapter.wav` and `trace.json`.

## Shorts pilot

The autonomous Shorts controller validates the twelve-item pilot, creates
canonical workspaces, renders 9:16 packages, prevents duplicate uploads, and
evaluates YouTube Analytics experiments:

```powershell
.\.conda-env\python.exe scripts/shorts.py plan
.\.conda-env\python.exe scripts/shorts.py bootstrap
```

See [`docs/shorts/README.md`](docs/shorts/README.md) for production, private
upload, analytics, review, recovery, and autonomy gates.

## Unified Channel Identity

The first shared control-plane slice provides tracked channel/product/series
IDs, versioned SQLite migrations, and read-only adapters for all three legacy
ledger shapes. It records rather than hides cross-pipeline identity collisions
and grants no remote account authority:

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/channel.py init
& $py scripts/channel.py status
& $py scripts/channel.py inventory
& $py scripts/channel.py collisions
& $py scripts/channel.py resources status
& $py scripts/channel.py import-youtube-rss --source <capture.xml> --scope <scope>
& $py scripts/channel.py reconcile
& $py scripts/channel.py release status
```

Runtime state is stored in the ignored
`workspace/channel/channel.sqlite`. See
[`docs/CHANNEL_CONTROL_PLANE.md`](docs/CHANNEL_CONTROL_PLANE.md) before
importing real Dialogue, Shorts, or Classic Listening ledgers.
Heavy Dialogue, Shorts, and Classic Listening entry points acquire the same
SQLite-backed `gpu_heavy` lease and keep the legacy lock file only as a
transition mirror.
Channel-wide release slots are local, transactional reservations. Programs
must be active in `configs/channel/release-policy.json`; a reservation never
grants YouTube scheduling authority.
The remote capture commands are read-only imports: they do not call YouTube or
grant remote mutation authority. The 2026-08-24 formal database reconciles all
15 items in its public RSS window; it does not cover private, unlisted, or
older public inventory outside that window.

Authorized weekly releases use the idempotent API-first controller:

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/youtube.py --manifest configs/channel/youtube-release-2026-08-31.json preflight
& $py scripts/youtube.py --manifest configs/channel/youtube-release-2026-08-31.json sync --apply-upload --apply-schedule
```

See [`docs/YOUTUBE_AUTOMATION.md`](docs/YOUTUBE_AUTOMATION.md) for OAuth,
retries, the crash-recovery journal, and the narrow Studio fallback boundary.

## Local VoxCPM2 Setup On Windows

Your preferred local model is `openbmb/VoxCPM2`.

1. Create the GPU-enabled Python environment:
   - `powershell -ExecutionPolicy Bypass -File scripts/setup_voxcpm_windows.ps1`
2. If Hugging Face is slow or blocked, use the mirror:
   - `powershell -ExecutionPolicy Bypass -File scripts/setup_voxcpm_windows.ps1 -UseHfMirror`
3. Check the runtime:
   - `.\.venv\Scripts\python.exe apps/worker-py/scripts/check_env.py`
4. Download weights explicitly:
   - `.\.venv\Scripts\python.exe apps/worker-py/scripts/download_voxcpm2.py`
5. Generate a short sample:
   - `.\.venv\Scripts\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda`

If CUDA memory is tight, close GPU-heavy applications and retry with:

- `.\.venv\Scripts\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --no-optimize`

## English Listening Room Production

Use the production controller after script approval rather than launching
render and pack scripts separately. It can begin audio before the native 16:9
cover/background is ready:

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/elr.py render-audio --episode 17 --series all --detach --visible-window
& $py scripts/elr.py preflight --episode 17 --series all
& $py scripts/elr.py produce --episode 17 --series all
& $py scripts/elr.py status --episode 17
& $py scripts/elr.py resume --episode 17 --series all
```

Start `render-audio` as soon as scripts are approved while remote cover and
background generation runs in parallel. It writes resumable turn WAVs only and
does not require visual assets. Once visuals are approved, `produce` reuses the
WAVs and keeps the full thumbnail, QC, mastering, subtitles, composition,
packaging, verification, and export gates. The controller derives canonical
workspaces, runs local GPU work serially with batch size 20, streams progress,
and persists state under `logs/elr_runs/`. See
`docs/shows/EPISODE_PIPELINE.md` and the `elr-episode-production` Skill.

## Classic Listening Operations

Classic Listening uses a rights-gated, event-sourced lifecycle. The tracked
policy starts at authority level 0, so local packaging can proceed but uploads
and public transitions are rejected. Its release cadence is only a request;
channel capacity and authorization come from the shared release policy.

- Inspect policy: `npm run classics:ops -- policy`
- Inspect a chapter: `npm run classics:ops -- status --book persuasion --chapter 1`
- Register a chapter: `npm run classics:ops -- transition --book persuasion --chapter 1 --to DISCOVERED --actor codex --reason "Register chapter" --idempotency-key persuasion-001-discovered`

Runtime events are written under `workspace/classics/operations/` and are
intentionally ignored by Git. See
[`docs/classics/AUTONOMOUS_OPERATING_MODEL.md`](docs/classics/AUTONOMOUS_OPERATING_MODEL.md)
before changing authority or publication policy.

The same controller exposes the protected Persuasion production adapter:

```powershell
.\.conda-env\python.exe scripts/classics.py ingest --book persuasion
.\.conda-env\python.exe scripts/classics.py preflight --book persuasion --chapter 1
.\.conda-env\python.exe scripts/classics.py status --book persuasion
```

Heavy production commands share the repository GPU lock with ELR and Shorts.
New Riley/VoxCPM2 audio generation is intentionally rejected by the tracked
`blocked_electronic_texture` acceptance state; ingestion, inspection, and
existing-artifact review remain available.
