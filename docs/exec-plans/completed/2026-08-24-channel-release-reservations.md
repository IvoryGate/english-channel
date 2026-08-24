# Channel Release Reservations

## Goal

Turn the tracked channel release policy into one transactional, auditable slot
reservation service so Dialogue, Shorts, and Classic Listening cannot plan
conflicting public releases or exceed channel capacity independently.

## Scope

- Parse and validate `configs/channel/release-policy.json` in the shared channel
  schema layer.
- Add versioned SQLite storage for append-preserving release reservations.
- Require canonical content identity, a declared program, and an idempotency
  key before a slot can be reserved.
- Enforce program product-line, status, date-window, and channel rolling
  seven-day capacity policy.
- Make cancellation auditable rather than deleting reservation history.
- Expose local-only reserve, cancel, and status commands.
- Update tests and channel operator documentation.

Excluded:

- Calling YouTube, uploading, scheduling, changing visibility, or editing
  metadata.
- Treating a local reservation as approval to schedule publicly.
- Choosing the portfolio or generating content.
- Experiment-cell reservations and generalized resource capacity.

## System Boundaries

- `configs/channel/release-policy.json`
- `apps/worker-py/worker/channel/` types, schema, repository, service,
  transport, and migration layers
- `apps/worker-py/tests/`
- `scripts/channel.py`
- shared architecture and operator documentation

## Status

- Branch: `codex/channel-release-reservations`.
- Owner: Codex primary agent.
- Last updated: 2026-08-24.
- State: completed and archived on 2026-08-24.
- Authority: local planning only; no remote mutation authority.

## Results

- Schema version 4 stores append-preserving release reservations.
- Canonical content, program status/product line/date window, timezone-aware
  future time, exact-slot uniqueness, active-content uniqueness, idempotency,
  and rolling seven-day capacity all fail closed.
- Cancellation retains the original row and reviewed reason.
- The formal runtime database migrated successfully and `release status`
  reports no active reservations and no remote scheduling authority.

## Plan

1. Define strict release-policy and reservation domain types.
2. Add migration and repository transactions with idempotent reserve and
   append-preserving cancel behavior.
3. Enforce program and rolling-capacity policy in the service.
4. Add CLI commands that always report the remote authority boundary.
5. Test identity, idempotency, conflicts, capacity, cancellation, and command
   behavior.
6. Update docs, run full gates, commit the slice, and archive this plan.

## Validation

- Migration is repeatable and preserved the formal reconciliation database
  while advancing it from schema version 3 to 4.
- Unknown identity, product-line mismatch, blocked program, date-window,
  timezone, exact-slot, active-content, and rolling-capacity paths fail closed.
- Identical idempotency retries return the original reservation; key reuse with
  different intent fails.
- Cancellation retains history and permits a reviewed replacement.
- CLI fixture exercised `reserve`, `status`, and `cancel`; every response
  denied public scheduling and remote mutation authority.
- Formal runtime smoke: `release status` completed with schema version 4 and no
  active reservations.
- Focused channel tests: 22 passed.
- `npm run lint`: passed.
- `npm test`: passed, including 134 Python tests.

## Risks And Decisions

- A reservation is internal planning state, not YouTube scheduling authority.
  The CLI must continue to report `remoteMutationAuthority: false`.
- Program status is a hard gate. Current `reconciliation_required` and
  `blocked_audio_acceptance` programs remain unable to reserve until tracked
  policy is deliberately changed.
- Timestamps must be timezone-aware. Policy date windows are evaluated in the
  configured channel timezone and stored as normalized UTC timestamps.
- Cancellation updates the active state but never deletes the original row.

## Archive Criteria

- The shared controller owns release reservation creation, conflict detection,
  listing, and cancellation.
- Every required policy and idempotency path is tested.
- Operator docs state that local reservation grants no YouTube authority.
- Full repository gates pass and no required work remains in this slice.

All archive criteria are satisfied. Activating a tracked release program and
executing a real reservation remain operator policy decisions, not unfinished
implementation in this slice.
