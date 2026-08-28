# Local Runtime

## Project Paths

- Python environment: `.conda-env/`
- Model weights: `pretrained_models/VoxCPM2/`
- Generated audio: `artifacts/`
- Production temporary files: `workspace/runtime/tmp/`

The ELR controller forces child-process `TEMP` and `TMP` into the ignored
project workspace so model loading and media work do not consume a nearly full
Windows system drive. Override with `ELR_RUNTIME_TEMP` only when the selected
drive has enough free space.

## One-Command Setup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_project_runtime.ps1 -UseHfMirror
```

## Verify

```powershell
.\.conda-env\python.exe apps/worker-py/scripts/check_env.py
.\.conda-env\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id pretrained_models/VoxCPM2
```

## Recover GPU / virtual memory (after crash or long serial render)

VoxCPM loads are RAM-heavy. After a marathon A→B→C run or exit `3221225477` / “页面文件太小”, free stale workers before resuming:

```powershell
.\.conda-env\python.exe scripts/release_production_memory.py
```

Dry-run (report only): `--dry-run`. Skip killing processes: `--no-kill`.

If free virtual memory stays below ~2 GB, close heavy apps or reboot — the script cannot grow the Windows page file.


Set these before starting the API:

```powershell
$env:PYTHON_BIN = ".\.conda-env\python.exe"
$env:VOXCPM_MODEL_ID = "pretrained_models/VoxCPM2"
$env:JOB_EXECUTION_MODE = "inline"
```

For normal asynchronous operation, omit `JOB_EXECUTION_MODE` (or set it to `queue`). The API process owns the BullMQ consumer and launches the Python renderer; do not start a separate Python RQ worker.
