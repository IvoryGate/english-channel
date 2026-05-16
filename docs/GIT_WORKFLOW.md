# Git Workflow

This repository uses trunk-based development. `main` is the trunk and must always remain buildable, testable, and deployable.

## Branch Lifecycle

1. Start from current trunk:
   - `git fetch --all --prune`
   - `git switch main`
   - `git pull --ff-only origin main`
2. Create a short-lived branch:
   - `feat/<short-topic>`
   - `fix/<short-topic>`
   - `chore/<short-topic>`
   - `docs/<short-topic>`
3. Keep the branch focused on one active plan or one small vertical slice.
4. Rebase or recreate from latest `main` when branch drift appears.
5. Delete merged branches after merge.

## Commit Rules

- Commit only coherent, reversible units.
- Each commit should preserve the repository's quality gates.
- Commit messages should explain intent and impact.
- Never include secrets, local credentials, generated model weights, or large audio artifacts.
- Do not mix unrelated plan work in one commit.

## Push And PR Timing

- Push after the first coherent slice is ready for CI.
- Open a PR immediately after the first push.
- Continue pushing follow-up commits to the same short-lived branch until the PR is ready.
- Do not wait for a large feature to be complete before opening a PR; use draft PRs when useful.

## CI/CD Merge Gate

A PR can merge only when:

- lint, type, test, architecture, and docs checks pass,
- required CI/CD jobs pass,
- the PR branch is current enough to avoid stale trunk assumptions,
- docs are updated for behavior or workflow changes,
- active execution plans touched by the PR are either still active or archived as completed.

If any required check fails, the agent fixes the branch and reruns CI before merge.

## Agent-Owned Git Operations

When a task authorizes repository operations, the agent should perform routine git work without asking for human judgment:

- inspect current branch and working tree,
- create a short-lived branch from latest `main`,
- stage relevant files,
- commit scoped changes,
- push the branch,
- open or update the PR,
- monitor CI/CD,
- fix deterministic failures,
- prepare merge once gates pass,
- delete the merged branch.

The agent must escalate only for:

- destructive operations (`reset --hard`, force push, branch deletion before merge),
- unclear product or security decisions,
- missing credentials or permissions,
- CI failures requiring human policy decisions,
- merge conflicts that cannot be resolved from repository context.

## Main Branch Protection

- No direct commits to `main`.
- No force-push to `main`.
- No bypassing required checks.
- No merging red CI.
- No long-lived feature branches.

## Execution Plan Archive Rule

Execution plans are stateful repository records:

- Work in progress lives in `docs/exec-plans/active/`.
- Completed work must be moved to `docs/exec-plans/completed/`.
- The archive move must happen in the same PR that completes the plan.
- If a plan is partially completed, leave it active and update its status.
- Completed plans should retain enough context for future agents to understand what changed and why.
