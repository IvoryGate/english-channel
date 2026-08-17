# 2026-08-17 Shorts autonomous pilot

## Goal

Deliver a production-ready vertical slice for English Listening Room Shorts: a
versioned product contract, a twelve-Short pilot portfolio, deterministic
workspace generation, 9:16 rendering, technical/content quality gates,
idempotent publication records, analytics ingestion, experiment evaluation,
and a weekly decision artifact. This creates the durable core needed for an
agent-run Shorts operating loop.

## Scope

- Define the Shorts product, format mix, publishing policy, metrics, experiment
  rules, and autonomy boundaries under `docs/shorts/`.
- Add a Python Shorts domain under `apps/worker-py/worker/shorts/`.
- Add a public `scripts/shorts.py` command for planning, validation, rendering,
  packaging, publication recording, analytics ingestion, status, and review.
- Add a data-driven Remotion 1080x1920 composition under `src/shorts/`.
- Seed the first twelve controlled pilot briefs.
- Add automated tests and run an offline end-to-end smoke workflow.

## Non-goals

- Publishing a public Short before the channel OAuth grant and YouTube API
  compliance audit are complete.
- Automating copyright disputes, account verification, policy appeals, or
  changes to channel identity.
- Reworking the existing 16:9 episode or audiobook media constants.
- Committing generated video, audio, model weights, OAuth tokens, or channel
  analytics exports.

## System Boundaries

- `apps/worker-py/worker/shorts/`: contracts, workspace, ledger, analytics,
  review, packaging, and command orchestration.
- `apps/worker-py/tests/`: Shorts unit and workflow tests.
- `scripts/shorts.py`: stable operator/automation entry point.
- `src/shorts/`: Remotion composition and schema-compatible input props.
- `configs/shorts/`: product policy and pilot portfolio.
- `docs/shorts/`: product and operating documentation.
- `workspace/shorts/`: ignored runtime state and generated artifacts.

## Status

- **State:** completed
- **Owner:** Codex
- **Branch:** `codex/shorts-pipeline-pilot`
- **Last update:** 2026-08-17

## Result

- Seeded and validated the twelve-item format-balanced pilot.
- Rendered `elr-s-001` end to end with VoxCPM2 speech, measured caption
  timings, a 1080x1920 Remotion composition, AAC audio, and passing media QC.
- Added private-only, duplicate-safe YouTube upload and analytics sync paths.
- Added deterministic experiment review output that carries winners, holds,
  and the 70/20/10 portfolio allocation into the next plan.
- Kept public publishing closed behind product policy, an environment gate,
  and an explicit command acknowledgement.

## Plan

1. Lock product, experiment, publishing, and quality contracts.
2. Implement validated manifests and canonical runtime workspaces.
3. Implement a data-driven 9:16 Remotion composition and render command.
4. Add packaging, file probing, content checks, and duplicate-safe publication
   ledger behavior.
5. Add analytics snapshots and deterministic weekly experiment decisions.
6. Seed and validate twelve pilot briefs.
7. Run unit, encoding, TypeScript, and offline end-to-end smoke checks.
8. Archive this plan when all in-scope checks pass. **Complete.**

## Validation

- All twelve pilot briefs validate against the same product contract.
- Re-running workspace creation is idempotent and preserves recorded state.
- Duplicate content keys and duplicate YouTube IDs are rejected.
- Invalid duration, captions, format allocation, metadata, and experiment
  definitions fail with actionable messages.
- The Remotion bundle compiles and renders a 1080x1920 smoke MP4.
- Analytics import produces a dated snapshot and a weekly review with explicit
  `scale`, `hold`, or `stop` decisions.
- `npm run check:encoding`, relevant Python tests, TypeScript checks, and the
  repository lint gates pass.

## Risks And Decisions

- The existing 16:9 episode renderer remains unchanged; Shorts are a separate
  product domain so vertical constants cannot leak into long-form output.
- Public upload remains disabled by default. YouTube API projects that have not
  passed audit can only upload private videos, and Related Video is managed in
  Studio rather than by a documented Data API field.
- Raw Shorts views are not the main experiment denominator. Reviews prefer
  engaged views, average percentage viewed, subscriber conversion, and
  long-form uplift.
- The current channel is small, so decisions use matched cohorts and rolling
  medians rather than claiming statistical significance from one upload.

## Archive Criteria

- Every scoped implementation item is complete.
- Required tests and smoke checks pass.
- User-facing docs describe production, publishing, recovery, and review.
- The plan is moved to `docs/exec-plans/completed/` in the finishing change.

All archive criteria are satisfied. The wider API integration suite still
requires the repository's Redis-backed test environment; Shorts-specific
Python tests, lint, encoding, TypeScript, Remotion version, and offline media
smoke checks pass independently.
