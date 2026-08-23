# Classic Listening Autonomous Foundation

## Goal

Create the rights, policy, audio-acceptance, lifecycle, authority, and event-ledger foundation required before Classic Listening can safely automate production or publishing.

## Scope

Included in this branch:

- Tracked series, audio-acceptance, and book-rights contracts.
- Strict `types -> schema -> repo -> service -> transport` implementation.
- An append-only, atomically written chapter event ledger with idempotent transitions.
- Fail-closed rights, release-gate, platform-evidence, and publishing-authority checks.
- A TTS provider protocol and blind-listening acceptance evaluator.
- Operator commands and focused tests.

Not included:

- Selecting or integrating a replacement TTS engine.
- Porting the unmerged Persuasion media pipeline.
- YouTube OAuth, upload, Studio automation, analytics ingestion, or public publishing.
- Raising authority above level 0.

## System Boundaries

- `configs/classics/`
- `apps/worker-py/worker/classics/`
- `apps/worker-py/tests/test_classics_*.py`
- `scripts/classics.py`
- `docs/classics/` and architecture/startup documentation

## Status

- Owner: Codex primary agent.
- Branch: `codex/classics-autonomous-foundation` from fetched `origin/main` at `0c245ec`.
- Last updated: 2026-08-23.
- State: accepted into the local unified intake at `9f4a7a3`; remote review and
  merge remain pending.
- The current Riley/VoxCPM2 narrator remains blocked by speech-coupled electronic texture. Its 16 kHz reference encoder makes reference upsampling irrelevant.

## Plan

1. Define and validate tracked policy, rights records, and audio acceptance cases.
2. Add domain types, immutable event persistence, guarded transitions, and authority checks.
3. Add operator CLI and provider boundary.
4. Test state replay, interruption safety, idempotency, rights rejection, audio rejection, and upload denial.
5. Run repository gates, update this status, commit, push, and open a draft PR if credentials permit.

## Validation

- Focused and full Python tests.
- CLI policy, status, transition, and idempotent-retry smoke tests.
- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`, with the project-local Python interpreter available in the worktree.
- No tracked credentials or runtime event files.

Completed on 2026-08-17:

- Full Python suite: 15 passed.
- Focused Classic Listening suite: 11 passed.
- CLI policy, empty status, transition, status replay, and idempotent retry passed.
- Encoding, documentation index, architecture, and full lint checks passed.
- Web, shared-types, and tooling tests passed.
- During unified intake, the API test harness no longer binds a port or connects
  to Redis as an import side effect. The full repository suite now passes:
  67 Python tests plus every Node workspace suite.

## Risks And Decisions

- Rights approval is territory-specific. A catalog record cannot advance when it does not cover every configured publication territory.
- Level 0 is the safe default and rejects upload, scheduling, and publishing.
- Runtime truth is reconstructed from immutable events, not generated-file presence.
- The ledger uses a per-chapter exclusive lock and atomic replacement. A future database adapter must preserve the same sequence, idempotency, and audit contracts.
- This branch intentionally does not depend on the unfinished Persuasion media branch.

## Archive Criteria

Move this plan to completed when this foundation is merged with all checks passing. Later TTS, production, publishing, analytics, experiment, and retrospective milestones will use separate plans and branches.
