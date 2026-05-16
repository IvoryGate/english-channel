# AGENTS

This repository is agent-first. Human maintainers define goals and constraints; agents execute implementation.

## First Read

1. `README.md` for startup commands.
2. `docs/ARCHITECTURE.md` for system boundaries.
3. `docs/PLANS.md` for active execution plans.
4. `docs/QUALITY_SCORE.md` for release gates.
5. `docs/GIT_WORKFLOW.md` for trunk-based branch, PR, merge, and archive rules.
6. `docs/LOCAL_RUNTIME.md` for project-local Python env and model paths.
7. `docs/ENCODING.md` for UTF-8 and LF file rules.

## System Of Record

All durable engineering knowledge lives under `docs/`.
Do not embed long-form rules inside this file.

## File Encoding Invariants

- All repository text files must be UTF-8 without BOM.
- Line endings must be LF, not CRLF.
- UTF-16, UTF-16 LE/BE, null bytes, and stray Unicode carriage characters are forbidden in source and docs.
- PowerShell scripts are also UTF-8 LF. Do not use Windows PowerShell defaults that write UTF-16.
- Before introducing or rewriting text files, follow `docs/ENCODING.md`.

## Trunk-Based Git Protocol

- `main` is the only trunk and must remain deployable.
- All code changes happen on short-lived branches created from latest `main`.
- Merge back only through PR after CI/CD and required review automation pass.
- Do not commit directly to `main`.
- Follow the detailed protocol in `docs/GIT_WORKFLOW.md`.

## Agent Autonomy Rules For Git

- When authorized for repository operations, the agent owns routine git flow end to end.
- The agent creates branches, keeps them current, commits scoped work, pushes branches, opens PRs, responds to CI, prepares merges, and cleans up merged branches.
- The agent must block merge when CI fails, required checks are missing, branch drift is unresolved, or the PR scope no longer matches the active plan.
- Escalate only for policy conflicts, ambiguous requirements, credentials, destructive git operations, or missing permissions.

## Execution Plan Operating Rules

- Use `docs/exec-plans/` for durable, multi-step work that spans code, tests, docs, infrastructure, or model/runtime setup.
- Active plans live in `docs/exec-plans/active/`; completed plans live in `docs/exec-plans/completed/`.
- Before implementation, read active plans and either follow an existing plan or create a new active plan when the task is more than a small single-file change.
- Keep each plan tied to one branch or one coherent vertical slice. Do not mix unrelated plan work in one PR.
- Update the active plan when scope, status, checks, risks, or decisions change.
- Move the plan to `completed/` in the same PR that finishes its scope. Do not leave finished work in `active/`.
- If a PR only completes part of a plan, keep it active and record what remains.
- Do not use execution plans for local generated artifacts, model weights, scratch notes, or transient todo lists.

## Non-Negotiable Invariants

- Update code, tests, and docs in the same change.
- Keep API layering strict: `types -> schema -> repo -> service -> transport`.
- Route external dependencies via providers.
- Preserve traceability for all generated audio artifacts.
- Archive completed execution plans from `docs/exec-plans/active/` to `docs/exec-plans/completed/` in the same PR that completes the work.