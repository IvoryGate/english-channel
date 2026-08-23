# Shorts Adapter Intake

## Goal

Absorb the proven Shorts discovery pipeline onto the unified ELR baseline while
keeping Shorts media specialization and moving channel-wide release capacity
out of the product adapter.

## Scope

Included:

- Integrate Shorts contracts, production, rendering, QC, packaging, private
  upload boundary, analytics snapshots, review logic, configs, tests, and docs
  from `codex/shorts-pipeline-pilot` at `fb25a62`.
- Preserve the newer ELR research, `channel_ops`, production safeguards, and
  unified operating-system documents already present on this branch.
- Introduce tracked channel release-capacity policy under `configs/channel/`.
- Replace Shorts-owned total-channel upload limits with a reference and a
  bounded product request evaluated by channel policy.
- Reconcile the accelerated-pilot plan with the historical 2026-08 release
  state without performing any YouTube mutation.

Not included:

- Publishing or scheduling Shorts.
- Deleting the existing Shorts branch, worktree, ledger, media, or analytics.
- Absorbing Classics or the dirty Persuasion implementation.
- Implementing the final shared SQLite control plane or resource scheduler.

## System Boundaries

- `apps/worker-py/worker/shorts/` and focused tests.
- `configs/shorts/` product and portfolio contracts.
- `configs/channel/` shared release-capacity contract.
- `docs/shorts/` and execution-plan state.
- `scripts/shorts.py` and local ignored `workspace/shorts/` state.
- Shared `package.json`, lockfile, runtime docs, voice profiles, and branding.

## Status

- Owner: Codex primary agent.
- Branch: `codex/shorts-adapter-intake`.
- Parent: `codex/elr-dialogue-intake` at `ceef2f2`.
- Intake source: `codex/shorts-pipeline-pilot` at `fb25a62`.
- Last updated: 2026-08-23.
- State: complete locally at merge commit `8e39d68`. Architecture is reconciled,
  channel release capacity is centralized, all local gates pass, and the source
  worktree remains intact. PR review and trunk merge await explicit remote
  approval.
- Publication hold: no remote YouTube write is authorized.
- Cleanup hold: no branch, worktree, generated media, or runtime state deletion.

## Plan

1. Merge the Shorts source history without replacing newer ELR shared files.
2. Resolve package, documentation, runtime, and voice-profile conflicts.
3. Add shared release-capacity policy and update Shorts contracts/tests/docs to
   treat cadence as a channel-approved request.
4. Reconcile the accelerated-pilot plan against current historical dates and
   keep unresolved OAuth/Studio dependencies explicit.
5. Run focused Shorts tests, complete lint/test gates, CLI smoke, secret scan,
   gitlink scan, and diff checks.
6. Commit the intake, update the reconciliation ledger, and archive this plan.

## Validation

- `npm run lint`
- `npm test`
- Focused `apps/worker-py/tests/test_shorts_pipeline.py`
- `scripts/shorts.py --help`
- No remote mutation during tests or smoke checks.
- No product config can set the total channel upload ceiling.
- No unmerged entry, gitlink, secret signature, generated cache, or whitespace
  error enters the commit.

Validation record, 2026-08-23:

- Focused Shorts tests: 13 passed.
- `npm run lint`: passed.
- `npm test`: passed, including 55 Python tests.
- `scripts/shorts.py --help`: passed without a remote mutation.
- Credential scan found only the expected code-level `refresh_token` attribute
  check; no credential value or private key signature was present.

## Risks And Decisions

1. The Shorts branch contains an older ELR baseline. Merge only Shorts-specific
   behavior and resolve shared files in favor of the maintained ELR intake.
2. Twice-daily cadence was a time-bounded experiment, not permanent channel
   policy. Preserve its evidence while requiring channel-level approval.
3. Shorts publication and analytics ledgers remain migration inputs until the
   shared channel store lands.
4. Related-video routing and private-upload idempotency are valuable adapter
   behavior and must not be weakened during centralization.

## Archive Criteria

Archive this plan in the finishing intake commit when Shorts code/tests/docs are
present, channel release capacity is centralized, all gates pass, the source
worktree remains intact, and the branch ledger records the intake commit.
