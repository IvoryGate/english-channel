# Plans Index

- Active plans live in `docs/exec-plans/active/`.
- Completed plans live in `docs/exec-plans/completed/`.
- A plan must move from active to completed in the same PR that completes its scope.
- If a PR only finishes part of a plan, keep the plan active and update its status.
- Do not leave completed work in `active/`; stale active plans mislead future agents.

## Agent Responsibilities

- Read active plans before starting implementation.
- Keep plan status aligned with code, tests, and docs.
- Archive completed plans without waiting for human prompting.
- Link completed plans from PR descriptions when they explain the change.
