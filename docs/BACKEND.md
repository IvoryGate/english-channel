# Backend

- `apps/api` owns input validation, job lifecycle, queue orchestration, and artifact index APIs.
- Layering:
  - `types`: domain records
  - `schema`: zod schemas
  - `repo`: persistence
  - `service`: business logic
  - `transport`: HTTP routes
  - `providers`: external infra adapters
