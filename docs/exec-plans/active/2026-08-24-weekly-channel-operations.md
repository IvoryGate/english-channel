# Weekly Channel Operations — 2026-08-24

## Goal

Turn the reviewed channel baseline and completed episode bank into an auditable
operating plan for 2026-08-24 through 2026-08-30, with local release
reservations, measurement tasks, and explicit remote-write gates.

## Scope

- Reconcile the stale six-slot Dialogue plan against the 2026-08-24 public
  inventory capture.
- Validate the packaged 020/021 candidates and preserve 021 as next-week
  inventory rather than skipping unpublished 020 episodes.
- Add a time-bounded active Dialogue validation program to channel policy.
- Register the six unpublished candidates in the canonical local identity
  store with real artifact fingerprints.
- Reserve the three 020 release slots for this week and define the measurement
  and review cadence.
- Produce one durable weekly operating brief.

Excluded:

- Uploading, scheduling, editing, or publishing on YouTube.
- Claiming current Studio analytics when only the 2026-08-17 signed-in baseline
  and 2026-08-24 public capture are available.
- Producing episode 022 or activating the blocked Shorts/Classics programs.

## Status

- Branch: `codex/weekly-ops-2026-08-24`.
- Owner: Codex primary agent.
- State: planning and evidence checks in progress.
- Authority: local planning and reservation only.

## Plan

1. Verify all six candidate packages and fingerprints.
2. Shift 020 releases to August 25/27/30 and 021 to September 1/3/6.
3. Add and validate the Dialogue program policy.
4. Import canonical unpublished candidate identities.
5. Reserve this week's three slots transactionally.
6. Write the weekly brief, run repository gates, commit, push, and archive this
   plan if no local planning work remains.

## Validation

- The legacy publication preflight accepts all six packages.
- The shared release controller accepts the three 020 reservations without
  spacing, identity, program, or rolling-capacity conflict.
- Every candidate source and MP4 fingerprint is retained.
- No YouTube mutation occurs.
- Encoding, docs, focused tests, lint, and full tests pass as appropriate.

## Risks And Decisions

- The August 18/20/23 plan was not executed according to the public capture;
  publishing 021 first would break canonical sequence and invalidate the test.
- The 2026-08-17 Studio baseline is useful but stale. Monday's first operating
  task is an immutable analytics refresh; decisions remain provisional until
  it lands.
- Publication remains behind explicit approval and a future private-upload
  provider even after a local reservation succeeds.

## Archive Criteria

- The tracked weekly plan, program policy, local candidate identities, and
  three reservations agree.
- The weekly brief names owners, gates, metrics, and stop conditions.
- Validation passes and the branch is pushed for audit.
