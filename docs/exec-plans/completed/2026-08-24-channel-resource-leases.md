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
- State: completed locally at `71cbb14`. Implementation, compatibility bridge,
  focused tests, operator documentation, isolated smoke, and full repository
  gates pass.
- Authority: local resource coordination only.

## Validation

- Focused resource/adapter suite: 34 passed.
- Exclusive ownership: a second owner is rejected with the active lease
  identity.
- Heartbeat: renewal extends expiry and explicit release closes the active
  lease.
- Safe recovery: expiry alone cannot evict a live PID; an expired lease with a
  confirmed dead owner is closed with `expired_owner_dead` and replaced in one
  transaction.
- Compatibility: nested same-process acquisition retains the outer SQLite
  lease; the legacy lock file mirrors acquisition and disappears on release.
  Live-parent inheritance remains in the compatibility boundary.
- Product coverage: Shorts and Classics adapter tests pass through their
  accepted entry points without executing a real GPU/model workload. Dialogue
  uses the same preserved `gpu_production_lock` API.
- Isolated `init` and `resources status`: schema version 2, no active leases,
  and `remoteMutationAuthority: false`.
- `npm run lint`: passed, including encoding, TypeScript, Remotion,
  architecture, docs, and Python compilation checks.
- `npm test`: all Node suites and 125 Python tests passed outside the sandbox.

## Completion Criteria

- The database is authoritative for accepted heavy entry points.
- Compatibility lock state cannot permit work rejected by the database.
- Code, tests, docs, and validation are committed together and this plan is
  archived. Generalized capacity scheduling remains in the parent unification
  plan rather than this completed exclusive-GPU slice.
