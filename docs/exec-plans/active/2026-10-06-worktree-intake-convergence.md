# Worktree Intake Convergence

## Goal

Return the repository to a trustworthy state before any new feature work:
restore every quality gate, classify the accumulated uncommitted working tree,
and split it into scoped, reviewable commits that can be pushed as short-lived
PRs. This is the intake step of the project takeover review.

## Scope

Included:

- Fix the two red Python tests caused by the half-applied 42-item week
  schedule contract.
- Reconcile `configs/classics/series.json` cadence with the shared channel
  release policy and the schedule disclosure footer.
- Classify 30 modified and 44 untracked working-tree entries into code,
  configuration, documentation, and generated-media groups.
- Commit each group as its own coherent unit on the current short-lived
  branch `feat/tts-provider-migration` (which is exactly `origin/main` plus
  four commits).

Explicit non-goals:

- No push, PR, merge, branch deletion, or worktree removal in this plan.
- No changes to production output, schedules, or content identity beyond
  making the tracked contract self-consistent.
- No credential, YouTube, or remote-platform operation.
- No reconciliation of the nine `.worktrees/*` worktrees or the four
  `origin/main`-ahead local branches; that is a follow-up plan.

## System Boundaries

- `configs/classics/series.json`
- `apps/worker-py/tests/test_classics_schema.py`
- `apps/worker-py/tests/test_classics_chapter_package.py`
- `docs/YOUTUBE_OPERATING_SYSTEM.md`
- `configs/channel/*`, `configs/shorts/*`, `docs/exec-plans/active/*`
- `public/shorts/*`, `public/classics/persuasion/*` (generated media, tracked
  by repository convention)

## Status

- Owner: OpenCode agent.
- Started: 2026-10-06.
- State: committed and validated; push and PR remain the next step and stay
  outside this plan's scope.

## Plan

1. Restore the classics cadence contract: `series.json`
   `requestedChaptersPerWeek`, the schema test literal, and the schedule
   footer assertion must all describe the same two-chapter week.
2. Update the Operating Cadence section of `docs/YOUTUBE_OPERATING_SYSTEM.md`,
   which still states the superseded six-standard/one-flagship week.
3. Run `npm run lint` and `npm run test`; both must be fully green.
4. Classify the working tree and commit in scoped units, each commit dated
   to the period its content describes: 2026-09-19 week plan, 09-19 render
   watchdog, 09-21 release manifest, 09-28 Shorts Kokoro default, 10-04 week
   plan, 10-04 Classics chapters, 10-05 export and quiet-repair hardening,
   10-06 the 42-item week.
5. Decide every generated-media entry explicitly instead of silently
   dropping it; the outcome is recorded under Risks And Decisions.

## Validation

- `npm run lint` passes (encoding, shared-types build, remotion typecheck,
  architecture, docs index, Python compileall).
- `npm run test` passes with 0 failures (Node 9 tests, Python 215 tests).
- Every commit was verified in isolation by extracting it with `git archive`
  and running the Python suite against the extract: 205, 207, 207, 207, 207,
  208, 214, 215 passed, zero failures. The final tree is byte-identical to
  the pre-split state.
- `git status --short` shows no uncommitted tracked modification after the
  final commit, and every remaining untracked path is an ignored runtime
  artifact or an explicitly inventoried media file.

## Risks And Decisions

- Decision: the 42-item week is the intended state. Evidence:
  `docs/classics/AUTONOMOUS_OPERATING_MODEL.md` sets the Classics cadence at
  two chapter episodes per week, `docs/exec-plans/active/2026-10-03-weekly-production-2026-10-05.md`
  defines the 14 long-form plus 28 Shorts schedule contract, and the existing
  modified tests already assert the ten-standard/two-flagship mix. The stale
  value is the tracked `series.json` cadence, not the release policy.
- Decision: generated Short backgrounds stay untracked. 79 files / 149 MB in
  `public/shorts/` (`weekly-2026-09-21` plus the ten daily directories from
  `monday-2026-09-28` through `wednesday-2026-10-07`) are image-generation
  outputs; their visual briefs and `backgroundImage` paths are already
  tracked in `configs/shorts/*.json`. Nothing outside a local re-render
  reads them: the Python and Node suites pass from `git archive` extracts
  that contain none of them, and no code under `src/`, `apps/web`, or
  `packages/` references `public/shorts`. `.gitignore` now excludes
  `public/shorts/`; the files stay on disk and no history is rewritten. The
  110 MB already tracked for `weekly-2026-09-07` (already on `origin/main`)
  and `weekly-2026-09-14` is left alone; shrinking published history is out
  of scope.
- Decision: the 12 MB of Persuasion chapter 6-9 covers and intro/outro
  traces committed with the Classics commit are a different class:
  `src/classics/persuasion-chapter-cover.tsx` maps chapter numbers to those
  exact files, so they are site assets rather than intermediates.
- Risk: the working tree mixes at least three plans. Committing them together
  would violate the one-plan-per-PR rule, so they are separated by commit.

## Archive Criteria

- All gates green, the working tree classified and committed, no untracked
  non-runtime file left behind, and this plan moved to
  `docs/exec-plans/completed/` in the PR that lands the final commit.
