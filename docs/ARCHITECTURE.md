# Architecture

- `apps/web`: UI for jobs and playback.
- `apps/api`: orchestration and validation.
- `apps/worker-py`: VoxCPM generation pipeline.
- Redis queue for async jobs.
- `artifacts/` for `chapter.wav` and `trace.json`.

Classic Listening autonomous operations follow the same strict dependency order:

- `worker/classics/types.py`: domain values only.
- `worker/classics/schema.py`: tracked config and persisted-event validation.
- `worker/classics/repo.py`: rights catalog and append-only operation ledger.
- `worker/classics/service.py`: transition, authority, evidence, and audio-acceptance policy.
- `worker/classics/transport.py`: operator command boundary.
- `worker/classics/providers/`: protocols for TTS, publishing, analytics, and other external systems.

Tracked policy is stored under `configs/classics/`. Runtime event history is stored under `workspace/classics/operations/`; current lifecycle state is always reconstructed from events rather than inferred from generated files.

API layer order: `types -> schema -> repo -> service -> transport`; external dependencies via `providers`.
