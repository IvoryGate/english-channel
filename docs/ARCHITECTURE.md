# Architecture

## Current Implementation

- `apps/web`: UI for TTS jobs and playback.
- `apps/api`: Fastify orchestration and validation. The API process owns the
  Redis/BullMQ consumer and launches the Python VoxCPM runner for each claimed
  job; Python does not consume a separate RQ queue.
- `apps/worker-py`: local VoxCPM generation pipeline and tracked Dialogue voice
  profiles.
- `artifacts/`: generated `chapter.wav` and `trace.json` outputs. API job records
  persist under `artifacts/jobs.json` by default and can be moved with
  `JOB_STORE_PATH`.
- `.cursor/skills/`, `docs/shows/`, `scripts/`, and
  `workspace/shows/tools/`: Dialogue / English Listening Room research, script,
  brand, resumable production, QC, packaging, and local operations workflows.
- `apps/worker-py/worker/channel/`: the implemented shared identity foundation,
  versioned SQLite repository, legacy-ledger adapters, collision reporting,
  immutable public-remote inventory imports, read-only reconciliation,
  exclusive heavy-resource leases, channel release reservations, and a
  local-only channel CLI. It does not yet implement shared lifecycle,
  generalized resource capacity planning, publication mutations, analytics,
  experiment, or decision services.
- `apps/worker-py/worker/channel_ops/`: the Dialogue-era publication identity
  and release-preflight prototype retained as a migration input.
- `apps/worker-py/worker/shorts/`: Shorts product contracts, workspace,
  publication ledger, private-upload boundary, analytics snapshots, QC, and
  review decisions.
- `apps/worker-py/worker/classics/`: Classic Listening rights, policy,
  append-only lifecycle, authority, audio-acceptance foundation, and protected
  Persuasion production adapter for source ingestion, aligned subtitles,
  multi-scene proofing, QC, and package construction.
- `src/shorts/`: data-driven Remotion 9:16 compositions. Generated audio and
  video remain in ignored `workspace/shorts/`.

The current implementation provides identity, public-capture reconciliation,
the first durable resource lease, and transactional channel release-slot
reservations. General resource scheduling, remote publication, analytics,
experiments, decisions, and progressive authority remain future slices. Do not
infer remote mutation authority or complete Studio visibility from the
presence of `scripts/channel.py`.

## Target System

The repository is evolving into one AI-operated YouTube channel system with a
shared control plane over specialized product adapters:

```text
shared channel control plane
  identity + lifecycle + portfolio planning + resource scheduling
  publication + analytics + experiments + decisions + authority
        |
        +-- dialogue long-form adapter
        +-- Shorts adapter
        +-- Classic Listening adapter
        |
        +-- provider boundaries for YouTube, Studio, TTS, ASR, image,
            rendering, hardware, secrets, notifications, filesystem, and clock
```

The control plane owns channel truth and cross-product constraints. Adapters
own media-specific contracts and rendering. The complete product, data,
measurement, resource, and autonomy design is defined in
[`YOUTUBE_OPERATING_SYSTEM.md`](YOUTUBE_OPERATING_SYSTEM.md).

## Layering And Dependency Rules

Every API or Python domain follows:

```text
types -> schema -> repo -> service -> transport
                                  -> providers
```

- Types have no infrastructure dependencies.
- Schemas validate versioned external and persisted contracts.
- Repositories own durable reads, transactions, migrations, and atomic writes.
- Services own lifecycle, policy, idempotency, and decision rules.
- Transports expose CLI, HTTP, queue, or scheduled-task inputs.
- Providers isolate YouTube, browser, model, hardware, filesystem, secret,
  notification, and time dependencies.
- Product adapters may depend on shared channel contracts; the shared channel
  domain may not import a concrete product renderer.

## Sources Of Truth

| Concern | Tracked truth | Runtime truth |
| --- | --- | --- |
| engineering/product rules | `docs/`, versioned configs, schemas, migrations | none |
| local job state today | code and job schema | `artifacts/` |
| target channel state | channel schemas and migrations | `workspace/channel/channel.sqlite` |
| raw analytics | import/query contracts | immutable `workspace/channel/raw/` snapshots |
| generated media | artifact contracts and fingerprints | ignored product workspaces and export roots |
| credentials | secret references and provider config | approved external/local secret store only |

During migration, legacy JSON ledgers are inputs, not competing permanent
sources of truth. Import must report collisions and preserve provenance.
The implemented migration contract and operator commands are documented in
[`CHANNEL_CONTROL_PLANE.md`](CHANNEL_CONTROL_PLANE.md).
The reviewed public inventory boundary is documented in
[`CHANNEL_RECONCILIATION_2026-08-24.md`](CHANNEL_RECONCILIATION_2026-08-24.md).

## Resource Safety Baseline

The local 8 GB GPU runs at most one heavy VoxCPM, Whisper, or NVENC job at a
time. The control plane now enforces this with an exclusive SQLite lease,
30-second heartbeat, expiry-plus-dead-owner recovery, and lease history.
`logs/gpu_production.lock` is a conservative compatibility mirror, not the
source of truth. Queue priority, aging, reservations, and generalized CPU,
RAM, disk, network, quota, and human-review capacity remain future work.

## Release Capacity Baseline

`configs/channel/release-policy.json` defines one channel timezone, rolling
seven-day capacity, program status, and date boundaries. Schema-version-4
`release_reservations` stores local plans with canonical content IDs,
idempotency keys, normalized UTC times, intent fingerprints, and
append-preserving cancellation. Exact-time, duplicate-content, and rolling
capacity conflicts fail inside one immediate transaction. These rows are not
YouTube schedules and carry no remote authority.

## Change Rule

Cross-product behavior belongs in the shared channel domain. Product-specific
behavior remains in its adapter. If two adapters independently implement
publication identity, channel cadence, analytics availability, experiment
assignment, authority, or GPU ownership, treat that as a migration defect and
move the rule to the control plane with tests.

Shorts keep a separate vertical media domain. Existing 16:9 episode and
audiobook layout constants must not be imported into `src/shorts` or the Shorts
quality contract.

## Classic Listening Foundation

Classic Listening autonomous operations follow the same strict dependency order:

- `worker/classics/types.py`: domain values only.
- `worker/classics/schema.py`: tracked config and persisted-event validation.
- `worker/classics/repo.py`: rights catalog and append-only operation ledger.
- `worker/classics/service.py`: transition, authority, evidence, and audio-acceptance policy.
- `worker/classics/transport.py`: operator command boundary.
- `worker/classics/providers/`: protocols for TTS, publishing, analytics, and other external systems.

Tracked policy is stored under `configs/classics/`. Runtime event history is stored under `workspace/classics/operations/`; current lifecycle state is always reconstructed from events rather than inferred from generated files.

The product config references the shared channel release policy and submits a
cadence request. It does not own total upload capacity or public scheduling
authority. Authority level 0 remains fail-closed for upload, scheduling, and
publishing.

The production adapter adds book config, EPUB ingestion, canonical paths,
resume state, render/QC helpers, and Remotion compositions without replacing
the lifecycle types, schema, repository, service, or transport. Heavy commands
enter through the hardware provider and share the channel `gpu_heavy` resource
lease with ELR and Shorts. The legacy lock path remains mirrored during the
transition for older inspection tools.
