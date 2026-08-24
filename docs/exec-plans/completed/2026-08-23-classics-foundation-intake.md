# Classic Listening Foundation Intake

## Goal

Absorb the clean Classic Listening rights, lifecycle, authority, audio
acceptance, and event-ledger foundation before salvaging the conflicting dirty
Persuasion implementation.

## Scope

Included:

- Integrate `codex/classics-autonomous-foundation` at `741b999`.
- Preserve strict `types -> schema -> repo -> service -> transport` layering and
  provider boundaries.
- Retain authority level 0, fail-closed rights/release gates, immutable events,
  and blind-listening audio acceptance.
- Reference the shared channel release policy without granting schedule or
  publication authority.
- Run focused and full gates, update intake records, and archive the source plan
  when the foundation is accepted locally.

Not included:

- Copying or modifying the dirty Persuasion source tree or generated assets.
- Choosing a replacement narrator/TTS provider.
- Uploading, scheduling, or publishing any Classic Listening item.
- Implementing analytics or the final shared channel database.

## System Boundaries

- `configs/classics/`
- `apps/worker-py/worker/classics/`
- `apps/worker-py/tests/test_classics_*.py`
- `scripts/classics.py`
- `docs/classics/`, `README.md`, and `docs/ARCHITECTURE.md`
- Shared `configs/channel/release-policy.json`

## Status

- Owner: Codex primary agent.
- Branch: `codex/classics-foundation-intake`.
- Parent: `codex/shorts-adapter-intake` at `24af3b0`.
- Intake source: `codex/classics-autonomous-foundation` at `741b999`.
- Last updated: 2026-08-23.
- State: completed locally at `9f4a7a3`; focused and full gates pass.
- Safety hold: Persuasion worktree and all branches/assets remain untouched.
- Publication hold: authority level 0 and channel public scheduling disabled.

## Plan

1. Merge the single clean foundation commit and reconcile shared docs/configs.
2. Bind Classic Listening release requests to channel policy while preserving
   product-specific cadence intent and authority level 0.
3. Run focused schema/operations tests, full lint/test, CLI smoke, secret,
   gitlink, untracked-cache, and diff checks.
4. Commit the intake, update the branch ledger, and archive this plan plus the
   completed source foundation plan.

## Validation

- Focused `test_classics_schema.py` and `test_classics_operations.py`.
- `npm run lint`
- `npm test`
- `npm run classics:ops -- --help`
- No runtime event file, credential, generated asset, or Persuasion worktree
  content enters the commit.
- Upload/schedule/public transitions remain rejected at authority level 0.

Completed on 2026-08-23:

- Focused Classic Listening suite: 12 passed.
- Full Python suite: 67 passed; all Node workspace suites passed.
- Encoding, shared-types build, TypeScript lint, architecture, documentation,
  and Python compile gates passed.
- Direct CLI help and `npm run classics:ops -- policy` passed.
- The tracked release request resolves to `classic-listening-baseline` in the
  shared channel policy, where audio acceptance is explicitly blocked.
- The Persuasion worktree, generated assets, runtime events, and credentials
  were not modified or added.

## Risks And Decisions

1. The clean foundation and dirty Persuasion worktree define competing
   `worker/classics` trees. This slice accepts the clean contracts first; the
   later salvage must port behavior semantically rather than overwrite them.
2. The current Riley/VoxCPM2 audio defect remains a product blocker.
3. Product cadence is a request. Only shared channel policy can reserve total
   release capacity or authorize public scheduling.

## Archive Criteria

Archive when the foundation is merged locally, all gates pass, authority remains
fail-closed, the shared policy reference is tested, the source plan is moved to
completed, and the Persuasion worktree remains intact.
