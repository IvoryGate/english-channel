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

Set in `.env`:

```env
PYTHON_BIN=.conda-env/python.exe
WORKER_ROOT=apps/worker-py
VOXCPM_MODEL_ID=pretrained_models/VoxCPM2
VOXCPM_DEVICE=cuda
JOB_EXECUTION_MODE=inline
```
