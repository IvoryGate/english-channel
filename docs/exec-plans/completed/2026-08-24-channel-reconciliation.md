# Channel Inventory Reconciliation

## Goal

Reconcile available local production ledgers with the real YouTube channel in
read-only mode, create the reviewed formal local channel database, and produce
an auditable report of matched, missing, duplicate, and unresolved identities.

## Scope

- Preserve and fingerprint every local ledger before import.
- Create a timestamped backup when a formal channel database already exists.
- Import available Dialogue, Shorts, and Classic Listening runtime ledgers into
  `workspace/channel/channel.sqlite` without modifying their sources.
- Capture remote YouTube inventory through a read-only provider or signed-in UI
  inspection when no connector/API is available.
- Store the remote capture immutably under `workspace/channel/raw/` and retain
  collection time, source, and capture fingerprint.
- Add a remote-inventory import/reconciliation service and CLI report.
- Match by canonical remote video ID first; titles are evidence, never identity.
- Report local-only, remote-only, duplicate remote ID, media collision, and
  metadata disagreement without silently resolving them.
- Update tests and operator documentation.

Excluded:

- Uploading, scheduling, editing, deleting, unlisting, or changing any YouTube
  content or channel setting.
- Treating a visual UI subset as a complete remote inventory without recording
  its pagination/filter boundary.
- Inventing missing Shorts or Classics ledgers.
- Manual SQL edits to suppress a collision.

## Status

- Branch: `codex/channel-reconciliation`.
- Owner: Codex primary agent.
- Last updated: 2026-08-24.
- State: completed and archived on 2026-08-24.
- Authority: reconciliation/read only.

## Results

- Formal database: `workspace/channel/channel.sqlite`, schema version 3.
- Local imports: 11 Dialogue plus four Shorts publications; no Classics
  operations ledger was available.
- Remote capture: 15 recent public RSS items with immutable source SHA-256 and
  explicit `public_rss_recent_max_15_no_private_unlisted` scope.
- Reconciliation: 15 matched, zero remote-only, zero local-outside-capture,
  zero title disagreements, and zero unresolved collisions.
- Evidence report: `docs/CHANNEL_RECONCILIATION_2026-08-24.md`.
- Remote mutations: none.

## Validation

- Local ledger source hashes were unchanged before and after import.
- The remote capture records source, collection time, explicit scope, and
  SHA-256.
- Re-import idempotency is covered by tests.
- Remote-only, local-only, and title-disagreement fixtures remain explicit
  rather than becoming inferred matches.
- No browser or provider action mutated remote state.
- Focused channel tests: 18 passed.
- Isolated CLI smoke: schema v3 initialized, all three ledgers plus RSS
  imported, and 15 of 15 remote IDs reconciled with exit code 0.
- `npm run lint`: passed.
- `npm test`: passed, including 130 Python tests.

## Completion Criteria

- The formal local database contains all available reviewed local identities.
- The accessible remote inventory is captured and reconciled with an explicit
  completeness boundary.
- The report identifies every unresolved mismatch and recommended next action.
- Code, tests, docs, and validation are committed together and the plan is
  archived if no required reconciliation work remains.

All completion criteria are satisfied for the declared public RSS boundary.
Credentialed Studio/provider inventory is intentionally deferred as a later
slice because it expands the evidence source, not because an item inside this
capture remains unresolved.
