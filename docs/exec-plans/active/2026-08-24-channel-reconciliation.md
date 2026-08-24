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
- State: local discovery and read-only remote capture pending.
- Authority: reconciliation/read only.

## Validation

- Local ledger source hashes are unchanged before and after import.
- Every remote capture records source, collection time, scope, and SHA-256.
- Re-import is idempotent.
- Remote-only and local-only fixtures remain explicit rather than becoming
  inferred matches.
- No browser or provider action mutates remote state.
- Focused tests, isolated CLI smoke, lint, and full tests pass.

## Completion Criteria

- The formal local database contains all available reviewed local identities.
- The accessible remote inventory is captured and reconciled with an explicit
  completeness boundary.
- The report identifies every unresolved mismatch and recommended next action.
- Code, tests, docs, and validation are committed together and the plan is
  archived if no required reconciliation work remains.
