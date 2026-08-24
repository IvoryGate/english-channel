# Channel Resource Leases

## Goal

Replace the process-local heavy GPU mutex with a durable, visible channel
resource lease while preserving the proven 8 GB safety rule: only one VoxCPM,
Whisper, or NVENC-heavy job may run at a time across Dialogue, Shorts, and
Classic Listening.

## Scope

- Add tracked resource capacity and recovery policy.
- Add a versioned resource-lease SQLite migration.
- Add lease types, repository operations, process-liveness provider, policy
  service, and `scripts/channel.py resources status` transport.
- Preserve the existing `gpu_production_lock` API so accepted product entry
  points adopt the shared lease without renderer rewrites.
- Add lease heartbeat for long-running jobs and parent/child inheritance for
  existing production subprocesses.
- Mirror the active lease into the legacy lock file during transition so old
  status and cleanup tools remain conservative.
- Recover automatically only when a lease is expired and its owner PID is
  confirmed dead. A live owner is never preempted because a clock expired.
- Add focused concurrency, heartbeat, recovery, reentrancy, and adapter bridge
  tests plus operator documentation.

Excluded:

- CPU/RAM/disk/network/API-quota capacity scheduling, queues, priority aging,
  preemption, or job planning.
- Killing processes or deleting arbitrary lock files.
- Release-calendar reservations or any YouTube mutation.

## Status

- Branch: `codex/channel-resource-leases`.
- Owner: Codex primary agent.
- Last updated: 2026-08-24.
- State: implementation pending.
- Authority: local resource coordination only.

## Validation

- Two owners cannot hold `gpu_heavy` concurrently.
- Heartbeat extends a live lease.
- Expiry alone cannot evict a live PID.
- An expired lease with a confirmed dead owner is recovered with an audit
  reason.
- Nested same-process and live-parent subprocess entry remains safe.
- Dialogue, Shorts, and Classics continue using their accepted public entry
  points without GPU/model execution in tests.
- Isolated resource status smoke, lint, and full tests pass.

## Completion Criteria

- The database is authoritative for accepted heavy entry points.
- Compatibility lock state cannot permit work rejected by the database.
- Code, tests, docs, and validation are committed together and this plan is
  archived.
