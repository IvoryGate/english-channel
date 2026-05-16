# 2026-05-16 Pride And Prejudice Voice Profile

## Goal

Design and implement a reusable English narration voice profile for Jane Austen's `Pride and Prejudice`, optimized for long-form audiobook generation with VoxCPM2.

## Scope

- Define a voice profile that matches Regency-era social comedy, restrained irony, and dialogue-heavy narration.
- Make the profile available to the Python worker by stable id.
- Preserve traceability of profile settings in generated artifacts.
- Document the expected reference-audio path so future cloning samples can be added without changing callers.

Non-goals:

- Do not commit source EPUBs, generated audio, model weights, or local runtime folders.
- Do not build a full multi-character dialogue system in this slice.
- Do not require a reference audio file before the profile can be selected.

## System Boundaries

- `apps/worker-py/worker/voice_profiles.py`
- `apps/worker-py/worker/runner.py`
- `docs/TTS_PIPELINE.md`
- `docs/exec-plans/completed/`

## Status

- Owner agent: Cursor agent
- Last update: 2026-05-16
- State: completed

## Plan

1. Define the `pride-prejudice-regency-narrator` voice profile.
2. Wire the worker to resolve profile defaults for cfg, timesteps, denoise, prompt text, and optional reference audio paths.
3. Add trace fields that record resolved profile settings.
4. Validate encoding, Python compilation, tests, and smoke generation.

## Validation

- `node packages/tooling/scripts/check-file-encoding.mjs`
- `node packages/tooling/scripts/check-docs-index.mjs`
- `node packages/tooling/scripts/check-api-architecture.mjs`
- `.\.conda-env\python.exe -m compileall apps/worker-py/worker apps/worker-py/scripts`
- `.\.conda-env\python.exe apps/worker-py/scripts/run_tests.py`
- `.\.conda-env\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id pretrained_models/VoxCPM2 --no-optimize --voice-profile pride-prejudice-regency-narrator --text "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife."`

## Risks And Decisions

- VoxCPM2 needs prompt or reference audio to truly clone a timbre. Until a reference file exists, the profile controls generation defaults and trace metadata, but acoustic timbre remains model-default.
- VoxCPM internal normalization is disabled for this profile because the current local conda environment has an `inflect`/`typeguard` dependency mismatch. Text normalization should be handled by the project pipeline in a later slice.
- Use one primary narrator first. Character-specific voices can be layered later after chapter extraction and dialogue attribution exist.

## Archive Criteria

- Profile is selectable by id.
- Worker applies profile runtime defaults.
- TTS docs describe the profile and reference-audio convention.
- Checks pass.
