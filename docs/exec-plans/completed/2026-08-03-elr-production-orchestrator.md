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

## System Boundaries

- Public controller and state: `scripts/elr.py`, `scripts/elr_production.py`,
  `scripts/elr_run_state.py`.
- Internal render/pack/export tools: `scripts/monitor_episode_*.py` and
  `workspace/shows/tools/`.
- Media composition: `.cursor/skills/audiobook-chapter-tts/scripts/media/`.
- Operator contract: `.cursor/skills/elr-episode-production/`, `README.md`, and
  `docs/shows/`.
- Runtime outputs remain ignored under `workspace/` and `logs/`; only reusable
  show tools and approved branding assets are versioned.

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
- [x] Observable runner complete.
- [x] Atomic delivery complete.
- [x] Skill/docs/release validation complete.

**State:** completed by the primary agent on 2026-08-03.

## Validation

- `npm run check:encoding` passed.
- Architecture and docs-index checks passed.
- `npm run build` passed for API, web, and shared types.
- Full Python suite passed: 29 tests.
- `elr-episode-production` passed `quick_validate.py`.
- Episode 016 all-series dry-run resolved exactly three canonical workspaces and
  batch size 20.
- Real Series A 016 preflight verified CUDA, VoxCPM files, 20.2 GiB available
  memory, disk, branding, paths, and 99.1% manifest coverage; it correctly
  rejected the historical 1708-word script against the new 1800-word minimum.

## Archive Criteria

- [x] All four milestones are implemented and tested.
- [x] Public workflow documentation points to one controller.
- [x] No final MP4 or export directory is promoted before verification.
- [x] Plan moved to `completed/` with the finishing change.
