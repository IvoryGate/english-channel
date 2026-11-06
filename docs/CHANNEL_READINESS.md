# Local Channel Readiness Diagnostics

`readiness` reports the evidence currently available on disk. It is not a
publication preflight, release approval, scheduler, or live YouTube query.
No result grants remote authority or resumes paused automations.

```powershell
.\.conda-env\python.exe scripts/channel.py readiness --as-of 2026-11-06T10:00:00+08:00
```

An explicit timezone-aware timestamp makes age calculations reproducible.
`--database` and `--release-policy` may override the inputs; place these options
before `readiness`. The command does not need `control-plane.json` and never
calls the normal repository's initialize, migration, or seed methods.

## Output And Exit Status

- Exit 0: the diagnostic report was produced. Findings may include missing,
  malformed, stale, or incomplete evidence. This is not a healthy-release code.
- Exit 2: invalid command arguments, including an absent timezone in `--as-of`.
- `releaseApproval` and `remoteMutationAuthority` are always false.
- Database table counts are local recorded rows. Absent tables yield null;
  an empty table yields zero. Neither is evidence of zero audience activity.
- Applied migration version/name pairs absent from this checkout are reported.
  The command does not migrate, downgrade, repair, or delete the database.
- Remote captures retain their provider, scope, item count, and recorded
  timestamp. At most the latest 20 stored capture rows are inspected. Complete
  current account coverage remains unverified, even for a recent capture.
- Active release programs are checked against their inclusive date window in
  the release policy timezone. Being in that window is not publication approval.
- Community reports deduplicate recorded comment IDs, distinguish explicitly
  verified status from merely published status, and expose partial inventories.
  Comment and schedule totals are null when their supported readable records
  are unavailable; explicitly present, valid empty arrays yield zero. Per-domain
  `evidenceCoverage` distinguishes unavailable, partial, and available local
  evidence. Partial counts cover only readable records, not the full catalogue.
  Only published records with a comment/post ID can refresh the latest
  observation. Timestamp ordering uses full precision, including timezone offsets.
  Scheduled dates are not publication observations. Local automation status
  claims cannot establish the current state of app automations.
- Active-plan filenames supply creation dates only. File modification time,
  filename date, and directory placement do not establish last activity,
  completion, or whether a plan should be archived.

The seven-day freshness threshold is a diagnostic convention, not a revised
release policy. Dates come from recorded fields, never filesystem modification
times. Date-only records keep date precision; their age is the UTC calendar-day
difference, so near midnight they cannot prove hour-level freshness. Future or
invalid publication observations cannot become the latest valid observation.

## Boundaries

The evidence repository opens SQLite with `mode=ro` and a consistent read
transaction. Missing databases and parent directories are not created. A WAL-mode
database without both existing `-wal` and `-shm` files is reported as
`wal_snapshot_unavailable` before SQLite opens it, because even read-only SQLite
can create those absent sidecars. Leave it unchanged; obtain a controlled
database backup outside this diagnostic if an offline snapshot is needed.
`immutable=1` is intentionally avoided so a live WAL is not silently ignored.
The command writes no reports or logical database data. Live WAL reads can use
and update existing shared-memory coordination locks; this is not a promise
that the `-shm` bytes remain unchanged. SQLite access failures are reported
instead of retrying with write permissions. Tests verify main-database hashes
remain unchanged and an idle WAL database does not gain sidecar files. Do not
remove or replace sidecars concurrently with diagnostics; the header/sidecar
precheck is not a lock against external filesystem changes.

Community inputs are the existing versioned JSON shapes under
`workspace/community/`, with a two-megabyte per-file bound. Missing
`operations.json`, unreadable/corrupt JSON, unsupported schemas, invalid row
shapes, and invalid timestamps remain visible as findings. Unknown schemas
are not interpreted. Dated historical records are local evidence, not a fresh
remote verification. The report omits post/comment copy and credentials.

This first slice does not prove research freshness, hardware capacity, media
quality, full publication coverage, live community delivery, or autonomous
growth. It makes a subset of existing evidence gaps inspectable before those
capabilities are built. Source layers are `readiness_types.py`,
`readiness_schema.py`, `readiness_repo.py`, `readiness_service.py`, and the
existing channel CLI transport. No model or browser is required.

## Validation

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONPATH = "apps/worker-py"
node packages/tooling/scripts/run-python.mjs -m pytest apps/worker-py/tests/test_channel_readiness.py -q
```

Fixtures cover read-only/missing database behavior, unknown migration versions,
unknown versus zero counts, policy timezone/day boundaries, stale/future/invalid
community evidence, partial captures, malformed input, expired buffers, and
plan-date semantics. They do not load models or contact external services.
