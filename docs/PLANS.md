# Plans Index

- Active plans live in `docs/exec-plans/active/`.
- Completed plans live in `docs/exec-plans/completed/`.
- A plan must move from active to completed in the same PR that completes its scope.
- If a PR only finishes part of a plan, keep the plan active and update its status.
- Do not leave completed work in `active/`; stale active plans mislead future agents.

## Purpose

Execution plans are durable repository records for agent work. They explain the target outcome, affected system boundaries, decisions already made, validation required, and the current state of the work.

Use an execution plan when work is multi-step, crosses app/package boundaries, changes workflow rules, adds infrastructure, modifies runtime/model setup, or needs follow-up across more than one session. Do not use plans for one-off edits that are obvious from the commit, local generated artifacts, downloaded model weights, scratch notes, or chat-only todos.

## Plan Lifecycle

1. Create a plan in `docs/exec-plans/active/` before substantive implementation begins.
2. Keep the plan focused on one branch or one coherent vertical slice.
3. Update the plan whenever scope, status, assumptions, decisions, validation, or remaining work changes.
4. Leave the plan active if only part of the scope ships.
5. Move the plan to `docs/exec-plans/completed/` in the same PR that finishes the scope.

## File Naming

- Use kebab-case Markdown names: `YYYY-MM-DD-short-topic.md`.
- Prefer names that match the branch or PR topic.
- Do not overwrite completed plans. If a new phase begins, create a new active plan and reference the completed predecessor.

## Required Sections

Each plan should include:

- `Goal`: the outcome and why it matters.
- `Scope`: included work and explicit non-goals.
- `System Boundaries`: files, packages, services, or docs expected to change.
- `Status`: current state, owner agent, and last update.
- `Plan`: ordered implementation steps.
- `Validation`: checks, tests, smoke runs, or review gates required before merge.
- `Risks And Decisions`: known trade-offs, constraints, and decisions made.
- `Archive Criteria`: what must be true before moving the plan to `completed/`.

## Agent Responsibilities

- Read active plans before starting implementation.
- Create an active plan for substantial work if no suitable plan exists.
- Keep plan status aligned with code, tests, and docs.
- Archive completed plans without waiting for human prompting.
- Link completed plans from PR descriptions when they explain the change.
