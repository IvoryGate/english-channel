# Local Runtime

## Project Paths

- Python environment: `.conda-env/`
- Model weights: `pretrained_models/VoxCPM2/`
- Generated audio: `artifacts/`
- Production temporary files: `workspace/runtime/tmp/`

## TTS provider runtimes

Provider-native float WAV output is peak-normalized to 0.89 before its trace
hash is recorded. For artifacts rendered before this guard was introduced,
`scripts/normalize_float_tts_audio.py --segments-dir <path>` repairs the WAVs
and their trace hashes without regenerating speech.

Dialogue and Classic Listening select one provider for an entire public
episode. Provider subprocesses keep incompatible dependencies isolated and
load the selected model once per render batch.

| Provider | Interpreter / model | Public role |
| --- | --- | --- |
| Kokoro Heart + Fenrir | `workspace/runtime/tts-audition/kokoro-env/Scripts/python.exe` | Dialogue preset voices |
| Chatterbox original 500M | `workspace/runtime/tts-audition/chatterbox-env/Scripts/python.exe`; `workspace/runtime/tts-audition/models/chatterbox-500m/` | Dialogue cloning and Classic narration |
| VoxCPM | `.conda-env/python.exe`; `pretrained_models/VoxCPM2/` | Compatibility fallback |

Kokoro is pinned to revision
`f3ff3571791e39611d31c381e3a41a3af07b4987`; Chatterbox original 500M is
pinned to `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`. Chatterbox Turbo remains
internal-only during the first migration week. Environments, model weights,
caches, temporary request files, and generated previews stay on the H drive
under ignored runtime paths and must never be committed.

Every provider turn is accompanied by a trace containing provider, pinned
revision, voice/reference hash, normalized text, seed, effective settings,
output format, watermark state, and output hash. Resume reuses a WAV only when
that complete identity and the current file hash match.

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
The runner also sets `TEMP`, `TMP`, and `TMPDIR` to an isolated per-command
subdirectory under `workspace/runtime/tmp/python`, keeping tests, package
builds, and model helper commands off the system drive while preventing mixed
permission contexts from sharing a temp directory. `ELR_RUNTIME_TEMP` remains
the explicit root override.

## Recover GPU / virtual memory (after crash or long serial render)

VoxCPM loads are RAM-heavy. After a marathon A→B→C run or exit `3221225477` / “页面文件太小”, free stale workers before resuming:

```powershell
.\.conda-env\python.exe scripts/release_production_memory.py
```

Dry-run (report only): `--dry-run`. Skip killing processes: `--no-kill`.

If free virtual memory stays below ~2 GB, close heavy apps or reboot — the script cannot grow the Windows page file.

VoxCPM runs initialize checkpoint-backed modules on PyTorch's meta device. On
Windows they also stream the 4.27 GB safetensors checkpoint into the target
device one tensor at a time and cap the checkpoint's 8,192-token context at
1,024. This avoids a full-file memory map competing with the model and CUDA
allocations for Windows commit space. Other platforms retain the 2,048-token
default and the normal safetensors loader. Override only for a measured need:

```powershell
$env:ELR_VOXCPM_MAX_LENGTH = "1024" # validated for current Shorts production
```

Values below 256 are rejected. This optimization reduces peak committed memory
but does not replace healthy Windows virtual memory. Set
`ELR_VOXCPM_STREAMING_LOAD=0` only on a host with enough commit capacity for the
fast full-checkpoint path. `ELR_VOXCPM_CHECKPOINT_DEVICE=cpu|cuda` selects that
path's load device. Persistent error 1455 still requires closing heavy
applications, increasing the D-drive page file, or rebooting.


Set these before starting the API:

```powershell
$env:PYTHON_BIN = ".\.conda-env\python.exe"
$env:VOXCPM_MODEL_ID = "pretrained_models/VoxCPM2"
$env:JOB_EXECUTION_MODE = "inline"
```

For normal asynchronous operation, omit `JOB_EXECUTION_MODE` (or set it to `queue`). The API process owns the BullMQ consumer and launches the Python renderer; do not start a separate Python RQ worker.
