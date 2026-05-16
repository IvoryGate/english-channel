# Architecture

- `apps/web`: UI for jobs and playback.
- `apps/api`: orchestration and validation.
- `apps/worker-py`: VoxCPM generation pipeline.
- Redis queue for async jobs.
- `artifacts/` for `chapter.wav` and `trace.json`.

API layer order: `types -> schema -> repo -> service -> transport`; external dependencies via `providers`.
