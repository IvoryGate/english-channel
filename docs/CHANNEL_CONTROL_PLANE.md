# Channel Control Plane Foundation

## Purpose

The shared channel domain gives Dialogue, Shorts, and Classic Listening one
canonical identity store. It is the first implemented slice of the target
control plane; it is not yet the portfolio planner, resource scheduler,
publication coordinator, analytics system, or experiment engine.

The foundation is deliberately local-only. It reads tracked policy and legacy
local ledgers, writes `workspace/channel/channel.sqlite`, and has no YouTube,
Studio, credential, upload, scheduling, deletion, or public mutation provider.
It also owns the first shared resource lease: one exclusive heavy GPU job.

## Tracked And Runtime Truth

- `configs/channel/control-plane.json` declares the stable channel,
  product-line, and series IDs.
- `apps/worker-py/worker/channel/migrations/` is the tracked database schema.
- `workspace/channel/channel.sqlite` is the ignored transactional identity
  store.
- Dialogue `workspace/channel_ops/publications.json`, Shorts
  `workspace/shorts/operations/publication_ledger.json`, and Classic Listening
  `workspace/classics/operations/**/events.jsonl` remain read-only migration
  inputs until their imports are reviewed.

Titles, paths, and folder names do not define identity. Canonical content IDs
use the declared series plus the adapter's stable local ID:

```text
content:series_b:episode_020
content:shorts_main:short_001
content:classic_listening:persuasion_chapter_001
```

## Commands

Use the project-local Python runtime:

```powershell
$py = ".\.conda-env\python.exe"

& $py scripts/channel.py init
& $py scripts/channel.py status
& $py scripts/channel.py inventory
& $py scripts/channel.py collisions
& $py scripts/channel.py resources status
& $py scripts/channel.py resources status --all

& $py scripts/channel.py import-dialogue `
  --source workspace/channel_ops/publications.json

& $py scripts/channel.py import-shorts `
  --source workspace/shorts/operations/publication_ledger.json

& $py scripts/channel.py import-classics `
  --source workspace/classics/operations
```

Global `--policy` and `--database` overrides must appear before the subcommand.
They are intended for tests, isolated rehearsals, and recovery inspection.

`init` applies ordered migrations and seeds policy identities. Import commands
also initialize safely, so a missing database is not a prerequisite failure.
`status` and `inventory` are read-only. `collisions` returns exit code 1 while
unresolved collisions exist. An import also returns 1 if any incoming item was
blocked by a collision and 2 for invalid input or repository failure.

`resources status` reads the authoritative lease table. `--all` includes
released and recovered history. Product controllers acquire leases through the
backward-compatible `gpu_production_lock` API; operators do not manually insert
or delete lease rows.

## Import Guarantees

Each import creates a durable `import_run` containing source system, absolute
source locator, SHA-256, collection time, and outcome counts. Every source item
retains both its normalized identity fields and exact source payload in the
database.

The importer is idempotent:

- the first accepted identity is `inserted`;
- a changed mutable title or source status is `updated`;
- an identical re-import is `unchanged` and does not duplicate canonical rows;
- a conflicting identity is `collision` and does not modify canonical tables.

The following conditions fail closed per incoming item:

- one source alias resolving to two canonical content items;
- canonical content attributes disagreeing with stored identity;
- one media SHA-256 resolving to two content items;
- one YouTube video ID resolving to two content items.

All detected conditions are written to `identity_collisions`. If one item has
both a media and remote-ID conflict, both facts are retained while the item is
counted once as collided. Other non-conflicting items in the same import may be
accepted.

The current CLI intentionally has no collision-resolution command. Resolution
requires reviewing the legacy sources and deciding which identity is correct;
adding an audited resolution event is a later slice. Do not edit database rows
manually to make a report disappear.

## Schema Boundaries

The initial migration owns:

- policy identities: `channels`, `product_lines`, `series`;
- canonical identity: `content_items`, `source_aliases`;
- duplicate prevention: `artifacts`, `publications`;
- provenance and review: `import_runs`, `import_records`,
  `identity_collisions`.
- resource coordination: append-preserving `resource_leases` with one partial
  unique active lease per resource.

Legacy lifecycle and publication statuses are retained as source facts. They
are not silently promoted into one current lifecycle, because the three
adapters use different state machines. A later migration will add the shared
append-only lifecycle after imported identity collisions are resolved.

## Recovery

Before a real migration, preserve the three source ledgers and copy
`workspace/channel/channel.sqlite` to an operator-approved backup location.
SQLite foreign keys are enabled for every connection; an import is one
transaction, so interruption rolls back that import rather than leaving half
its records canonicalized.

If initialization fails, keep the database and source files for diagnosis.
Do not delete a database merely because a migration reports an error. Restore
from the reviewed backup or use a new explicit `--database` path for an
isolated rehearsal. Legacy input files are never written by the importer and
remain the recovery source.

## Next Control-Plane Slices

1. Review real local imports and add audited collision resolution plus shared
   lifecycle events.
2. Extend the initial heavy-GPU lease into CPU, RAM, disk, network, quota, and
   human-review capacity with priority aging and reservations.
3. Add channel release reservations and authority policy.
4. Add provider-based private publication and immutable analytics snapshots.
5. Add experiments, retrospectives, evidence-linked decisions, and portfolio
   feedback.

## Heavy GPU Lease Recovery

`configs/channel/resources.json` fixes `gpu_heavy` capacity at one, a 120-second
TTL, and a 30-second heartbeat. Long-running accepted entry points refresh the
lease in a daemon thread. A contender cannot evict a live process even if its
heartbeat is late. Automatic recovery requires both expiry and a confirmed
dead owner PID; the old lease is closed with `expired_owner_dead` before the
replacement is inserted in the same transaction.

`logs/gpu_production.lock` remains a compatibility mirror for older status
tools. Deleting that file does not release the authoritative SQLite lease and
cannot permit overlapping GPU work. Use `scripts/channel.py resources status`
to diagnose ownership. Process termination remains an explicit operator action.
