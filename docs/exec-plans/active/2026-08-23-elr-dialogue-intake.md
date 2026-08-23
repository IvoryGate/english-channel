# ELR Dialogue Pipeline Intake

## Goal

Absorb the maintained English Listening Room dialogue pipeline onto the unified
YouTube operating-system baseline without regressing branch protections,
publication safeguards, execution-plan history, or future adapter boundaries.

## Scope

Included:

- Integrate the unique commits from `feat/elr-series-scriptwriting-pipeline`.
- Retain the unified channel mission, architecture, reconciliation ledger, and
  active operating-system plan already established on the parent branch.
- Remove the accidental `.worktrees/shorts-pipeline-pilot` gitlink while
  preserving the actual Shorts worktree and branch.
- Reconcile active and completed ELR plans with the code that lands.
- Validate the complete JavaScript/TypeScript and Python quality gates plus
  focused ELR tests.
- Record the accepted ELR head and resulting intake commit in the branch ledger.

Not included:

- Porting Shorts or Classic Listening code.
- Salvaging or modifying the dirty Persuasion worktree.
- Introducing the shared SQLite control plane or resource scheduler.
- Publishing, scheduling, editing, or deleting YouTube content.
- Deleting any branch, worktree, generated asset, or local operations state.

## System Boundaries

- `.cursor/skills/`: Dialogue research, script, and production instructions.
- `apps/api/`: queue execution boundary used by local production.
- `apps/worker-py/worker/channel_ops/`: ELR publication-preflight prototype to
  retain as an adapter-era input to the future shared channel domain.
- `apps/worker-py/worker/youtube_podcast_research/`: research provider and
  workspace implementation.
- `scripts/` and `workspace/shows/tools/`: resumable production, QC, packaging,
  mastering, and topic-selection commands.
- `docs/shows/` and `docs/exec-plans/`: product contracts and durable plan state.
- `package.json`, `package-lock.json`, and runtime documentation.

## Status

- Owner: Codex primary agent.
- Branch: `codex/elr-dialogue-intake`.
- Parent: `codex/youtube-operating-system-foundation` at `7487393`.
- Intake source: `feat/elr-series-scriptwriting-pipeline` at `d965773`.
- Last updated: 2026-08-23.
- State: source history merged; expected documentation conflicts are resolved,
  the accidental Shorts gitlink is removed from the index, plans are
  reconciled, and all required local gates pass. Merge commit pending.
- Safety hold: no worktree, branch, runtime file, or generated asset cleanup.
- Publication hold: this plan grants no remote YouTube write authority.

## Plan

1. Read the source branch's active plans and inspect unique commits, gitlinks,
   package changes, and publication boundaries.
2. Integrate the source history without treating it as a replacement tree.
3. Resolve shared documentation and policy conflicts in favor of the unified
   control-plane contract while retaining proven ELR behavior.
4. Remove the accidental worktree gitlink from the Git tree and confirm the
   real Shorts worktree remains untouched.
5. Reconcile plan lifecycle state and update the branch intake ledger.
6. Run encoding, docs, architecture, lint, tests, focused ELR tests, and a
   publication-safe CLI smoke check.
7. Commit a coherent local intake slice and prepare it for review.

## Validation

- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- `npm test`
- Focused tests for channel operations, ELR preflight/orchestration, production
  run state, atomic delivery, packaging, and topic selection.
- `git diff --check`
- No tracked entry exists below `.worktrees/`.
- No command in validation performs a remote YouTube mutation.

Validation record, 2026-08-23:

- `npm run lint`: passed.
- `npm test`: passed, including 42 Python tests.
- API tests use explicit fake providers and no longer bind port 4000 or connect
  to Redis when importing the server builder.
- `scripts/elr.py --help` and `scripts/channel_ops.py --help`: passed without a
  remote mutation.
- Index checks found no unmerged entries, gitlinks, credential signatures, or
  whitespace errors.

## Risks And Decisions

1. The source branch diverges before the current trunk merge commit. Intake
   must preserve content and behavior rather than assuming a fast-forward.
2. The source tracks a local Shorts worktree as a gitlink. It is explicitly
   excluded from the accepted tree; removing the Git entry does not authorize
   deleting its directory or branch.
3. The ELR `channel_ops` ledger remains a migration input, not the final shared
   source of truth. This slice preserves it so later migration can be tested.
4. The source includes a Persuasion plan but not the dirty Persuasion code.
   Preserve plan history while treating the dirty worktree as authoritative for
   its unfinished implementation.
5. Local publication credentials do not grant authority. Tests and smoke checks
   stop before any remote mutation.

## Archive Criteria

Move this plan to `completed/` in the finishing intake commit only when:

- all accepted ELR code, tests, configs, skills, and docs are present;
- the accidental worktree gitlink is absent;
- plan states accurately describe landed and remaining work;
- required quality gates pass;
- the reconciliation ledger records the intake result; and
- the branch is ready for PR review without generated media, secrets, or local
  runtime state.
