# ELR production orchestrator stabilization

## Goal

Turn the current Series A/B/C episode process into one reproducible, observable,
resume-safe command that always derives canonical paths and only publishes a
verified complete package.

## Branch

`feat/elr-series-scriptwriting-pipeline`

## Scope

- Put the production tools under version control instead of leaving executable
  source inside the ignored runtime workspace.
- Enforce canonical show/episode paths and preflight gates before GPU work.
- Add one CLI for `preflight`, `produce`, `status`, and `resume`.
- Stream child-process output and persist phase, heartbeat, PID, command, and
  failure details in a machine-readable run state.
- Keep A/B/C serial, default VoxCPM batch size 20, and reuse completed turn WAVs.
- Publish through an incomplete directory and rename only after media/package
  verification succeeds.
- Consolidate operator guidance into a repository-local production Skill.

## Non-goals

- A new browser console or API queue.
- Automatic YouTube upload.
- Generating new episode content or replacing approved visual assets.
- Parallel GPU rendering.

## Milestones

1. **Source and contracts** — track show tools; add canonical path helpers,
   manifest coverage checks, metadata scaffolding, and tests.
2. **Observable runner** — implement the single CLI and durable run state with
   streamed logs and resume semantics.
3. **Atomic delivery** — stage exports, validate required files and MP4 media,
   then promote the completed directory atomically.
4. **Workflow consolidation** — add the production Skill, update docs/defaults,
   run release gates, and archive this plan.

## Release gates

- Encoding and documentation checks pass.
- Focused Python tests cover path derivation, preflight failures, metadata
  scaffolding, state transitions, resume selection, and atomic promotion.
- `elr.py preflight` reports actionable failures without loading VoxCPM.
- `elr.py produce --episode 16 --series all --dry-run` resolves only the three
  canonical episode workspaces and shows serial commands with batch size 20.
- `elr.py status --episode 16` reads the persisted state without scanning opaque
  terminal output.
- No final export directory is created or replaced before verification passes.

## Risks and decisions

- The current `workspace/` ignore rule also hides executable production tools.
  Only `workspace/shows/tools/**` will be unignored; generated episode data stays
  ignored.
- Existing low-level scripts keep their legacy arguments for compatibility. The
  new public entry point does not accept a free-form workspace path.
- One GPU lock covers the serial A/B/C run. A failed phase stops the run and is
  resumable from existing artifacts.

## Status

- [x] Current working state committed and pushed as baseline `5cbec47`.
- [x] Source and contracts complete.
- [ ] Observable runner complete.
- [ ] Atomic delivery complete.
- [ ] Skill/docs/release validation complete.
