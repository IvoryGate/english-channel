# Architecture

## Current Trunk

- `apps/web`: UI for TTS jobs and playback.
- `apps/api`: Fastify orchestration, validation, and queue boundary.
- `apps/worker-py`: local VoxCPM generation pipeline and tracked Dialogue voice
  profiles.
- Redis: asynchronous job queue.
- `artifacts/`: generated `chapter.wav` and `trace.json` job outputs.
- `.cursor/skills/`, `docs/shows/`, and `scripts/`: first-generation Dialogue /
  English Listening Room script, brand, packaging, and local episode-production
  workflows.

Current trunk does not yet provide a shared channel control plane. Later
Dialogue research and resumable operations, Shorts, Classic Listening, channel
operations, analytics, and experiment work exist on branches and worktrees
catalogued in [`BRANCH_RECONCILIATION.md`](BRANCH_RECONCILIATION.md). Do not
infer that an unmerged capability is available from trunk.

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

## Resource Safety Baseline

The local 8 GB GPU runs at most one heavy VoxCPM, Whisper, or NVENC job at a
time. Existing branches enforce this with a PID lock. The target control plane
replaces it with recoverable resource leases, queue priority, heartbeat,
capacity accounting, and visibility while preserving the one-heavy-GPU-job
safety limit initially.

## Change Rule

Cross-product behavior belongs in the shared channel domain. Product-specific
behavior remains in its adapter. If two adapters independently implement
publication identity, channel cadence, analytics availability, experiment
assignment, authority, or GPU ownership, treat that as a migration defect and
move the rule to the control plane with tests.
