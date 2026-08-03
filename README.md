# English Channel

Agent-first, frontend-backend separated audiobook workflow platform centered on VoxCPM2.

## Monorepo Layout

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

After an episode script and its native 16:9 cover/background are approved, use
the production controller rather than launching render and pack scripts
separately:

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/elr.py preflight --episode 17 --series all
& $py scripts/elr.py produce --episode 17 --series all
& $py scripts/elr.py status --episode 17
& $py scripts/elr.py resume --episode 17 --series all
```

The controller derives canonical workspaces, runs A/B/C serially with batch size
20, streams progress, persists state under `logs/elr_runs/`, resumes completed
turns, and exports only after the final package passes verification. See
`docs/shows/EPISODE_PIPELINE.md` and the `elr-episode-production` Skill.
