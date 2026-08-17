# Architecture

- `apps/web`: UI for jobs and playback.
- `apps/api`: orchestration and validation.
- `apps/worker-py`: VoxCPM generation pipeline.
- `apps/worker-py/worker/shorts`: Shorts product contracts, workspaces,
  publication ledger, YouTube integration, analytics, and review decisions.
- `src/shorts`: data-driven Remotion 9:16 composition. Generated audio and
  video remain in ignored `workspace/shorts/`.
- Redis/BullMQ queue for async jobs. The API process owns the BullMQ consumer and launches the Python VoxCPM runner for each claimed job; Python does not consume a separate RQ queue.
- Job records are persisted locally under `artifacts/jobs.json` by default (override with `JOB_STORE_PATH`) so status survives an API restart.
- `artifacts/` for `chapter.wav` and `trace.json`.

API layer order: `types -> schema -> repo -> service -> transport`; external dependencies via `providers`.

Shorts keep a separate vertical media domain. Existing 16:9 episode and
audiobook layout constants must not be imported into `src/shorts` or the Shorts
quality contract.
