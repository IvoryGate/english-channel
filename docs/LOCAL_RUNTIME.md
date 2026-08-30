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

Remotion uses four parallel render workers by default on this production host.
Set `ELR_REMOTION_CONCURRENCY` before rendering to override it; values are
clamped to `1..8` so an accidental setting cannot exhaust the shared machine.

## One-Command Setup

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_project_runtime.ps1 -UseHfMirror
```

## Verify

```powershell
.\.conda-env\python.exe apps/worker-py/scripts/check_env.py
.\.conda-env\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id pretrained_models/VoxCPM2
```

Npm commands use `packages/tooling/scripts/run-python.mjs` so the same quality
gates work on Windows production hosts and Linux CI. Runtime selection is:

1. `PYTHON_BIN`, when explicitly set;
2. the repository `.conda-env` interpreter for the current platform;
3. `python` on Windows or `python3` on other platforms.

The production machine therefore keeps using `.conda-env/python.exe`, while
GitHub Actions uses the interpreter installed by `actions/setup-python`.
The runner also sets `TEMP`, `TMP`, and `TMPDIR` to
`workspace/runtime/tmp/python`, keeping tests, package builds, and model helper
commands off the system drive. `ELR_RUNTIME_TEMP` remains the explicit override.

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
