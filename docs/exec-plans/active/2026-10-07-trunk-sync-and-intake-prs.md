# Trunk Sync And Intake Pull Requests

## Goal

Land the intake convergence on `main` through reviewable, CI-gated pull
requests, and record the branch, worktree, and PR inventory that the
follow-up reconciliation plan will act on.

## Scope

Included:

- Fast-forward the local `main` branch to `origin/main`.
- Open PR-A for the four pre-existing commits already pushed on
  `feat/tts-provider-migration` (the TTS provider migration plan).
- After PR-A merges, push and open PR-B for the nine intake commits plus
  this plan.
- Monitor the `ci-pr` quality gates and fix deterministic failures.
- Inventory, without acting on, every local branch and `.worktrees/*`
  checkout that is ahead of or behind `origin/main`.

Explicit non-goals:

- No merge while any required check is red; no force push; no direct
  commits to `main`.
- No branch deletion and no worktree removal in this plan.
- No history rewrite; the 237 MB of `public/` blobs already published stay.
- No YouTube, credential, or remote-platform operation.
- Branch and worktree reconciliation itself is the next plan and follows
  `docs/BRANCH_RECONCILIATION.md`.

## System Boundaries

- `.gitignore`, `docs/exec-plans/active/*`
- Local refs `main`, `feat/tts-provider-migration`
- Remote refs on `origin` and pull requests against `main`
- `.github/workflows/ci-pr.yml` (the merge gate)

## Status

- Owner: OpenCode agent.
- Started: 2026-10-07.
- State: in progress.

## Plan

1. Fast-forward local `main` after proving it holds no unique commit.
2. Prove the PR-A candidate `2831e11` in isolation: `git archive` extract
   plus the Python suite must be green before any PR is opened.
3. Open PR-A with `main` as base so `ci-pr` runs, and leave its branch
   untouched until the PR merges.
4. Open PR-B from the intake branch once PR-A has merged, so PR-B carries
   exactly the nine intake commits.
5. Record the inventory below and hand branch/worktree reconciliation to a
   separate plan.

## Validation

- Local `main` equals `origin/main` with zero unique commits.
- The PR-A head is green in isolation before the PR exists; PR-A and PR-B
  each show green `quality-gates` before merge.
- PR-B's file and commit list contains only the intake work.

## Risks And Decisions

- Decision: two sequential PRs instead of one or a stacked pair. The nine
  intake commits touch 22 files that the four pre-existing commits also
  touch, and they build on the Kokoro support those commits introduce, so
  they cannot be rebased onto `origin/main`. A stacked PR with a non-`main`
  base is excluded because `ci-pr` only triggers for `pull_request` against
  `main`.
- Decision: PR-A uses the branch exactly as pushed (`2831e11`), so no
  history is rewritten for work that is already on the remote.
- Inventory of local branches against `origin/main` (`27b17a7`), 2026-10-07.
  Fully contained (ahead 0), candidates for the reconciliation plan:
  `codex/weekly-production-2026-09-07` (0/0),
  `codex/channel-release-reservations` (41 behind), `codex/channel-reconciliation`
  (44), `codex/channel-resource-leases` (46), `codex/channel-control-plane-foundation`
  (49), `codex/legacy-pipeline-parity` (52), `codex/persuasion-pilot-intake` (55),
  `codex/classics-foundation-intake` (59), `codex/shorts-adapter-intake` (63),
  `codex/elr-dialogue-intake` (72), `feat/elr-series-scriptwriting-pipeline` (77),
  `codex/classics-autonomous-foundation` (91), `codex/youtube-operating-system-foundation`
  (91), `codex/weekly-ops-2026-08-24` (20), `agent/bootstrap-voxcpm-workflow` (99).
- Inventory, unmerged (ahead of `origin/main`): `feat/tts-provider-migration`
  13 ahead / 0 behind (main worktree, this plan), `codex/shorts-pipeline-pilot`
  4 ahead / 71 behind, `codex/long-form-expansion` 3 ahead / 14 behind,
  `feat/weekly-analytics-loop` 2 ahead / 0 behind, `feat/audiobook-skill-opt-in-srt`
  5 ahead / 99 behind, `feat/youtube-research-topic-selection` 4 ahead /
  99 behind, `codex/classics-persuasion-pilot` 1 ahead / 92 behind (open PR #5),
  `codex/channel-wide-youtube-ab` 1 ahead / 15 behind,
  `codex/shorts-rapid-3x3-2026-08-30` 1 ahead / 16 behind,
  `codex/douyin-migration` 1 ahead / 0 behind, `feat/episode-audio-mastering`
  1 ahead / 99 behind, plus the local-only rollback ref `intake-backup-20261006`.
- Inventory, pull requests: #1, #2, #3, #4, #6, #7, #8, #9, #10 are merged
  (2026-07-20 through 2026-08-31); #5 (`codex/classics-persuasion-pilot`,
  opened 2026-08-24) is open and stale at one commit ahead and 92 behind;
  #11 is the PR-A opened by this plan. `main` carries no branch protection
  and no required status checks, so the merge gate is the `ci-pr` result
  plus this plan's own rule.
- Risk: `deploy-staging` has never passed. It is not part of `ci-pr`, so it
  does not block these PRs, but its history must be diagnosed before any
  merge that expects a deployment.

## Archive Criteria

- PR-A and PR-B merged with green quality gates, this inventory recorded,
  and this plan moved to `docs/exec-plans/completed/` in PR-B.
