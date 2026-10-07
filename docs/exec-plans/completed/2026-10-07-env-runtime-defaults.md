# API Environment Defaults And Loader

## Goal

Make the documented `.env` contract in `docs/MODEL_LOCAL.md` real: a UTF-8
example file that the encoding gate actually covers, an API loader that reads
the repo root `.env` at startup, and a local `.env` on the production host —
so the API runs in `inline` mode without a Redis server.

## Scope

Included:

- Convert `.env.example` from UTF-16/CRLF to UTF-8/LF and align its keys with
  what `apps/api` reads (`PYTHON_BIN`, `WORKER_ROOT` were documented in
  `MODEL_LOCAL.md` but missing from the example).
- Add `apps/api/src/load-env.ts` as the first import of `main.ts`, resolving
  the repo root `.env` from `import.meta.url` so `tsx` dev and `dist` builds
  behave identically regardless of cwd.
- Close the encoding-gate gap that let UTF-16 through: `extensionOf` on
  `.env.example` returns `.example`, which was not in `checkedExtensions`.
- A loader test and a `docs/MODEL_LOCAL.md` update in the same change.
- Create the ignored local `.env` on this machine (not committed).
- Construct the BullMQ `Queue` lazily in `createQueueProvider`: the smoke
  test showed `ECONNREFUSED 127.0.0.1:6379` spam in inline mode because the
  provider eagerly opened a Redis connection it never uses.

Explicit non-goals:

- No queue or Redis work: `JOB_EXECUTION_MODE=inline` (the documented
  default) keeps execution in-process; staging infrastructure keeps its own
  `infra/environments/staging.env.example`.
- No dotenv dependency; no CI secrets; no changes to the TTS provider
  configuration.

## Status

- Owner: OpenCode agent.
- Started: 2026-10-07.
- State: completed 2026-10-07. Loader, example conversion, gate fix, lazy
  queue, tests, and docs verified (lint exit 0, API tests 5/5, Python
  215/215 twice, live smoke with zero ECONNREFUSED); archived in this PR.

## Plan

1. Branch and this plan.
2. Loader, example conversion, encoding-gate fix, test, docs.
3. Gates, PR, CI green, merge; archive this plan in the same PR.

## Validation

- `npm run lint` (now scanning `.example` files) exits 0.
- `npm run test` stays green with the new loader test included.
- The API starts from the repo root `.env` with `JOB_EXECUTION_MODE=inline`
  and never attempts a Redis connection in that mode — verified by a live
  smoke run (`GET /health` 200, zero `ECONNREFUSED` log lines).
- `.env.example` and `infra/environments/staging.env.example` are read by the
  encoding gate as UTF-8 with LF endings.

## Risks And Decisions

- Decision: no dotenv dependency — `process.loadEnvFile` (Node >= 20.12)
  was verified empirically to keep existing process environment values and
  only fill gaps from the file, which is the safe precedence.
- Decision: the loader resolves the root from `import.meta.url`
  (`../../../.env` from both `src/` and `dist/`), so npm workspace cwd
  conventions cannot point it at the wrong file.
- Decision: `load-env.js` must stay the first import in `main.ts`, because
  `job-repo.ts` resolves `JOB_STORE_PATH` at module scope.
- Risk: enabling `.example` in the gate surfaces a violating file.
  Mitigation: both example files were inspected (LF, ASCII content) before
  the rule change.
- Observation (out of scope here): two validation runs of the Python suite
  failed 1–2 timing-sensitive episode-delivery tests while a stray API
  smoke process was still consuming the machine; three subsequent runs
  were 215/215. The flake predates this change and is recorded for a
  separate investigation.

## Archive Criteria

- PR merged with gates green and this plan moved to
  `docs/exec-plans/completed/` in that same PR.
