# Local Model And Runtime Layout

## Project-Local Paths

| Purpose | Path |
|---------|------|
| Python runtime | `.conda-env/` |
| VoxCPM2 weights | `pretrained_models/VoxCPM2/` |
| Generated audio | `artifacts/` |

## Setup

1. Clone Anaconda runtime into the project:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/clone_conda_env.ps1
```

2. Download VoxCPM2 into the project:

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
.\.conda-env\python.exe apps/worker-py/scripts/download_voxcpm2.py --local-dir pretrained_models/VoxCPM2
```

3. Verify:

```powershell
.\.conda-env\python.exe apps/worker-py/scripts/check_env.py
.\.conda-env\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id pretrained_models/VoxCPM2
```

## API Defaults

Copy the template once per machine (`.env` is gitignored):

```powershell
Copy-Item .env.example .env
```

`apps/api` loads the repo root `.env` at startup — `load-env.js` is the
first import in `main.ts` and resolves the file from the module location, so
`tsx` dev and the built `dist` behave the same regardless of cwd. Values
already present in the real process environment always win over the file,
and a missing file is a no-op for CI and fresh clones.

```env
PYTHON_BIN=.conda-env/python.exe
WORKER_ROOT=apps/worker-py
VOXCPM_MODEL_ID=pretrained_models/VoxCPM2
VOXCPM_DEVICE=auto
VOXCPM_OPTIMIZE=true
VOXCPM_LOAD_DENOISER=false
ARTIFACT_DIR=artifacts
JOB_EXECUTION_MODE=inline
HF_ENDPOINT=https://hf-mirror.com
```

`JOB_EXECUTION_MODE=inline` keeps job execution in-process. Without a
`.env` the code default is `queue`, which needs a reachable Redis
(`REDIS_HOST` / `REDIS_PORT`); the canonical local setup therefore runs the
API with no broker at all — the BullMQ queue is constructed lazily on first
enqueue, so inline mode never opens a Redis connection.
