# Frontend

The frontend in `apps/web` provides:

- chapter submission,
- queue/job status view,
- playback for generated chapter artifacts.

Rules:

- Use contracts from `packages/shared-types`.
- Do not call worker directly; all actions go through API.
