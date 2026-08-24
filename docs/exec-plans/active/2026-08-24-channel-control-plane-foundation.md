# Channel Control Plane Foundation

## Goal

Create the first Phase 2 vertical slice of the unified YouTube operating
system: one canonical channel identity model and one versioned SQLite source of
truth that can safely absorb the Dialogue, Shorts, and Classic Listening local
ledgers.

## Status

- Branch: `codex/channel-control-plane-foundation`.
- Owner: Codex primary agent.
- Last updated: 2026-08-24.
- State: implementation and focused tests complete; documentation, isolated CLI
  smoke test, full repository gates, and completion archival remain.
- Authority: local state only; no remote mutations are implemented or granted.

## Scope

Included:

- Add tracked channel, product-line, and series identity policy.
- Add `worker/channel/` using the repository layer order
  `types -> schema -> repo -> service -> transport`.
- Add versioned SQLite migrations for policy identities, content items, source
  aliases, artifact fingerprints, publications, imports, and collisions.
- Normalize the three legacy ledger shapes without modifying their source
  files.
- Retain the exact imported source payload, source locator, collection time,
  and source fingerprint.
- Fail closed per item when a source alias, canonical identity, media
  fingerprint, or YouTube video ID disagrees with existing state.
- Add a canonical `scripts/channel.py` surface for database initialization,
  imports, inventory, status, and collision reports.
- Document migration and recovery behavior and add focused tests.

Excluded:

- YouTube reads or writes, publishing, scheduling, account access, or browser
  automation.
- Resource leases, portfolio planning, analytics, experiments, and decisions;
  those remain later control-plane slices.
- Deleting or rewriting the legacy JSON/JSONL ledgers.
- Declaring migration complete for real runtime ledgers before an operator
  reviews all collision reports.

## Design Decisions

1. Policy owns stable channel, product-line, and series IDs. Importers may only
   reference identities declared by policy.
2. A canonical content ID is derived from the declared series and the adapter's
   stable local identity, never from a mutable title or folder name.
3. Every import run is durable even when every item collides. Raw payloads are
   retained in SQLite so the decision can be replayed.
4. A collision blocks only the incoming item. It never silently overwrites the
   existing identity and never chooses one source as authoritative.
5. One SHA-256 media fingerprint and one YouTube video ID may each resolve to
   only one content item channel-wide.
6. Re-importing an identical source is idempotent and produces an auditable
   skipped outcome rather than duplicate canonical rows.
7. SQLite transactions and foreign keys are mandatory. Migrations are applied
   in order and recorded in `schema_migrations`.
8. Authority remains read/local-state only. This plan grants no remote account
   mutation permission.

## Deliverables

- `configs/channel/control-plane.json`
- `apps/worker-py/worker/channel/`
- `apps/worker-py/worker/channel/migrations/`
- `apps/worker-py/tests/test_channel_*.py`
- `scripts/channel.py`
- `docs/CHANNEL_CONTROL_PLANE.md`
- Architecture, operating-system, README, and active-plan updates

## Validation

- Focused channel tests cover migration, all three import formats,
  idempotency, collision isolation, provenance retention, and inventory.
- A fixture import proves the same YouTube ID and media SHA cannot map to two
  content items.
- `scripts/channel.py --help` and an isolated `init/status` smoke test pass.
- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- `npm test`

## Completion Criteria

- All deliverables are implemented and validated.
- Legacy source files remain byte-for-byte untouched by imports.
- The plan is moved to `completed/` in the same change that records validation.
- Phase 2 remains active until real local and remote inventory has been
  reconciled and each identity resolves without an unreviewed collision.
