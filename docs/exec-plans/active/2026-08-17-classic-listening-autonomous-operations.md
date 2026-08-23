# Classic Listening Autonomous Operations

## Goal

Turn the existing Classic Listening chapter-production pilot into a permissioned autonomous operating system that can maintain the public-domain audiobook series from book selection through production, private upload, scheduled publication, experiments, analytics, retrospectives, and next-action planning.

The product and operating contract is defined in `docs/classics/AUTONOMOUS_OPERATING_MODEL.md`.

## Scope

Included:

- A rights-verified book catalog and scored backlog.
- A durable book/chapter publication state machine.
- Provider-based production orchestration, strict quality gates, and repair queues.
- Versioned packaging hypotheses and three thumbnail variants.
- Permissioned YouTube private upload, captions, playlists, scheduling, and status reconciliation.
- Native thumbnail experiment tracking plus browser-only integration where the public API has no supported operation.
- YouTube Analytics/Reporting snapshots, retention analysis, demographic and continuation reporting.
- Evidence windows at 6 hours, 24 hours, 72 hours, 7 days, 14 days, and 28 days.
- Retrospective and next-action records with fail-closed policy enforcement.
- Progressive publishing authority levels from package-only to autonomous operation.

Non-goals:

- Publishing the current `Persuasion` audio while the electronic voice artifact remains unresolved.
- Weakening rights, source fidelity, audio, subtitle, visual, or platform checks in order to maintain cadence.
- Deleting, unlisting, or materially rewriting published videos without explicit user authorization.
- Storing OAuth tokens or account credentials in tracked files.
- Claiming causal title-test results from uncontrolled sequential metadata changes.
- Depending on brittle Studio browser automation when a supported API exists.

## System Boundaries

Expected tracked surfaces:

- `configs/classics/series.json` — product policy, cadence, authority, experiment limits, and quality thresholds.
- `configs/classics/books/*.json` — rights-verified book contracts and season configuration.
- `apps/worker-py/worker/classics/types.py` — domain types and state enums.
- `apps/worker-py/worker/classics/schema.py` — persisted contract validation.
- `apps/worker-py/worker/classics/repo.py` — catalog, ledger, experiment, snapshot, and decision storage.
- `apps/worker-py/worker/classics/service.py` — orchestration and transition policy.
- `apps/worker-py/worker/classics/providers/` — TTS, image, YouTube, Studio, and Analytics adapters.
- `apps/worker-py/worker/classics/transport.py` and `scripts/classics.py` — public commands.
- `docs/classics/` — operator, product, analytics, experiment, and incident contracts.
- Focused tests under `apps/worker-py/tests/`.

Runtime-only surfaces:

- `workspace/classics/catalog/`
- `workspace/classics/operations/`
- `workspace/classics/analytics/`
- `workspace/classics/experiments/`
- `workspace/classics/retrospectives/`
- Configured YouTube export roots and credential stores.

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-17.
- State: planning complete; implementation not started.
- Branch: implementation requires a dedicated short-lived branch from current `main` after the `Persuasion` pilot changes are reconciled.
- Current blocker: the approved Riley/VoxCPM2 path has a speech-coupled electronic artifact. VoxCPM2 encodes references at 16 kHz, so a 48 kHz Riley reference does not address the model limit.

## Plan

### Milestone 0: unblock the audio product

- Define a blind-listening acceptance set with narration, dialogue, fragile short lines, long sentences, names, dates, and sibilants.
- Compare synthesis providers behind the provider contract; do not hard-code the next engine into orchestration.
- Require source recovery, voice stability, long-form consistency, latency/cost evidence, and absence of the detected 7.5-8.8 kHz texture.
- Lock one approved narrator profile and a reproducible generation trace before another full chapter render.

Exit: one provider/voice combination passes automated QC and explicit blind listening on the acceptance set.

### Milestone 1: catalog, policy, and state machine

- Add the series policy configuration and rights-scored catalog.
- Define book, chapter, publication, experiment, analytics, and decision schemas.
- Implement guarded state transitions and immutable event history.
- Add authority levels, stop conditions, retry classes, and idempotency keys.
- Migrate the `Persuasion` pilot record without changing existing media.

Exit: state reconstruction and simulated interruption tests pass without using file existence as completion.

### Milestone 2: reusable production and quality services

- Move remaining chapter-specific V2 behavior behind reusable services and providers.
- Preserve strict layering `types -> schema -> repo -> service -> transport`.
- Add audio-artifact classification, ASR review, word-alignment, scene-manifest, black-frame, timestamp, and package gates.
- Add deterministic repair planning and selective regeneration.
- Produce three packaging variants per eligible chapter.

Exit: a dry-run book fixture and one real chapter reach `READY_TO_UPLOAD` with a complete trace.

### Milestone 3: permissioned YouTube publishing

- Configure OAuth through the approved secret store.
- Implement idempotent private upload, metadata, captions, playlist membership, and status reconciliation.
- Record real video, caption, and playlist IDs.
- Poll platform processing and copyright checks before scheduling.
- Add schedule collision, duplicate upload, and partial-failure recovery tests.
- Keep public transition behind authority Level 1 until a human approves several complete runs.

Exit: a private test upload can be safely retried without duplicate public content and can be reconciled from YouTube state.

### Milestone 4: analytics warehouse and reports

- Add targeted YouTube Analytics queries and bulk-report ingestion where appropriate.
- Persist immutable snapshots at the six decision windows.
- Store reach, consumption, retention curve, continuation, playlist, audience, and growth metrics.
- Derive comparable rolling baselines by book stage, duration band, publish slot, and traffic source.
- Distinguish unavailable/private-threshold data from zero.

Exit: one published historical video can be backfilled into a complete 28-day report with reproducible derived metrics.

### Milestone 5: experiment engine

- Add hypothesis, variable, variants, evidence rule, guardrails, platform result, and decision contracts.
- Support native thumbnail Test & Compare records with `Winner`, `Preferred`, `None`, and `Insufficient Evidence` outcomes.
- Add audited Studio browser actions only for operations unavailable through supported APIs.
- Implement matched-cohort title and production-policy experiments without claiming uncontrolled causality.
- Enforce one changed variable and one active causal production-policy experiment at a time.

Exit: one thumbnail experiment and one matched-cohort experiment complete with recorded decisions and reusable learnings.

### Milestone 6: retrospective and next-action engine

- Generate 7-day and 28-day evidence-backed retrospectives.
- Map retention cliffs to intro/body/outro, subtitle, scene, and technical timelines.
- Implement allowed autonomous actions and prohibited escalations.
- Update thumbnail archetype rankings, cadence, scene-density ranges, and book scores only from sufficient evidence.
- Maintain a three-chapter ready buffer and rights-verified next-book shortlist.

Exit: the engine selects and explains the next action from stored evidence while respecting all policy constraints.

### Milestone 7: progressive autonomous operation

- Run package-only shadow mode against current manual decisions.
- Advance to private-upload authority after parity is demonstrated.
- Advance to scheduling authority after stable platform and recovery runs.
- Advance to autonomous series operation only after an agreed observation period with no gate bypasses or duplicate actions.
- Add exception notifications, weekly summaries, season retrospectives, and credential-expiry handling.

Exit: routine chapters require no human action; only policy, rights, account, quality, or platform exceptions are escalated.

## Validation

Repository gates:

- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- Focused and full Python tests.

Functional gates:

- Exact state/event replay after interruption.
- Idempotent production, upload, caption, playlist, schedule, and analytics operations.
- No credential material in tracked files, logs, traces, or test fixtures.
- No public transition above configured authority.
- Rights, source, audio, subtitle, visual, media, and platform failures stop publication.
- Analytics distinguishes missing, delayed, privacy-suppressed, and zero values.
- Experiments reject multiple changed variables and premature winners.
- Retrospectives cite the exact snapshot and experiment evidence used.
- Browser-only actions capture before/after state and fail closed on unexpected Studio UI.
- A full shadow season demonstrates buffer maintenance, scheduling, analytics, and next-action selection.

## Risks And Decisions

- The current audio defect is a product blocker, not a mastering problem. Autonomous scale begins only after a clean narrator path is approved.
- A 48 kHz stored reference does not bypass VoxCPM2's 16 kHz reference encoder.
- YouTube native thumbnail tests optimize watch-time share and may remain inconclusive with low impressions. The system must preserve inconclusive outcomes.
- Native thumbnail tests and end-screen editing are not fully exposed by the public API. Browser automation is permissioned, audited, and secondary to supported APIs.
- Public API uploads from unverified projects may remain private until Google completes the required audit.
- Demographic data can be absent or privacy-suppressed. Product decisions cannot assume missing data means no 55-plus female audience.
- Chapter-to-chapter narrative differences confound title and production-policy experiments. Matched cohorts provide evidence, not laboratory certainty.
- Fully autonomous publishing requires explicit account authorization and an approved Level 3 policy; it cannot be inferred from permission to produce local artifacts.

## Archive Criteria

Move this plan to `completed/` only when:

- The narrator/audio blocker is resolved.
- All seven milestones and validation gates pass.
- At least one real book season has operated through publication and 28-day retrospectives.
- Publishing authority and exception rules are recorded and approved.
- No routine operation depends on an undocumented manual step.
- Code, tests, docs, provider contracts, and incident recovery agree.

