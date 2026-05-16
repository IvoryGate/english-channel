# TTS Pipeline

1. Input normalization
2. Text chunking
3. VoxCPM generation per chunk
4. Concatenate waveform
5. Write `chapter.wav` and `trace.json`

## Local Model

- Default model: `openbmb/VoxCPM2`.
- Default device: `auto` (`cuda -> mps -> cpu`), with `cuda` recommended on this project workstation.
- Environment knobs:
  - `VOXCPM_MODEL_ID`
  - `VOXCPM_DEVICE`
  - `VOXCPM_OPTIMIZE`
  - `VOXCPM_LOAD_DENOISER`
  - `ARTIFACT_DIR`

## Trace Fields

Minimum trace fields: `jobId`, `chapterId`, `modelId`, `device`, `optimize`, `voiceProfile`, `segmentCount`, `cfgValue`, `inferenceTimesteps`, `startedAt`, `finishedAt`, `audioPath`, `tracePath`.

## Smoke Test

Run:

`.\.venv\Scripts\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda`
