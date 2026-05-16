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

Minimum trace fields: `jobId`, `chapterId`, `modelId`, `device`, `optimize`, `voiceProfile`, `requestedVoiceProfile`, `voiceProfileSettings`, `segmentCount`, `cfgValue`, `inferenceTimesteps`, `startedAt`, `finishedAt`, `audioPath`, `tracePath`.

## Voice Profiles

Voice profiles are stable ids resolved by the Python worker. A profile can define audiobook style, generation defaults, prompt text, and optional VoxCPM2 prompt/reference audio paths.

### `pride-prejudice-regency-narrator`

Primary voice for Jane Austen's `Pride and Prejudice`.

- Style: adult British narrator, poised, warm, articulate, lightly ironic, and restrained.
- Genre fit: Regency social comedy, drawing-room dialogue, family satire, and long-form literary narration.
- Performance target: elegant pacing with clear sentence shape; dry wit should land through slight timing and intonation, not exaggerated character acting.
- Runtime defaults: `cfgValue` 2.15, `inferenceTimesteps` 12, VoxCPM internal text normalization disabled.
- Prompt/reference convention:
  - `assets/voices/pride-prejudice-regency-narrator/prompt.wav`
  - `assets/voices/pride-prejudice-regency-narrator/reference.wav`

VoxCPM2 needs prompt or reference audio to truly shape timbre. Until those files exist, the worker records the selected profile and applies its generation defaults, but the acoustic timbre remains model-driven.

## Smoke Test

Run:

`.\.venv\Scripts\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda`
