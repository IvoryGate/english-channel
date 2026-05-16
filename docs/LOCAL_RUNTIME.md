# Local Runtime

## Project Paths

- Python environment: `.conda-env/`
- Model weights: `pretrained_models/VoxCPM2/`
- Generated audio: `artifacts/`

## One-Command Setup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_project_runtime.ps1 -UseHfMirror
```

## Verify

```powershell
.\.conda-env\python.exe apps/worker-py/scripts/check_env.py
.\.conda-env\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id pretrained_models/VoxCPM2
```

## API Integration

Set these before starting the API:

```powershell
$env:PYTHON_BIN = ".\.conda-env\python.exe"
$env:VOXCPM_MODEL_ID = "pretrained_models/VoxCPM2"
$env:JOB_EXECUTION_MODE = "inline"
```
