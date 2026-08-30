# Cross-Platform Python Runner — 2026-08-30

## Goal

Make npm quality gates use the project-local Python runtime on production
Windows hosts and the configured Python runtime on Linux CI.

## Scope

- Add one Node-based Python command resolver.
- Route npm Python scripts through the resolver.
- Route child-process temporary files to the ignored project workspace.
- Test override, local-environment, and platform-fallback behavior.
- Document the selection order in the local runtime guide.

## Status

- Owner: Codex primary agent.
- State: complete; PR #8 exposed the Windows-only npm command path on Linux
  CI, and npm now resolves Python and temporary storage per host.

## Validation

- Five tooling tests pass, including explicit override, project environment,
  platform fallback, and project-local temporary storage.
- `npm run lint` passes locally.
- `npm test` passes locally, including all Node workspace tests and 164 Python
  tests.
- The corrected checkpoint is pushed to PR #8 to rerun Ubuntu quality gates.

## Archive Criteria

The resolver is documented and tested, local checks pass, and the corrected
branch has been pushed to PR #8.
