# Workspace-Only Episode Production

## Goal

Allow the public ELR production controller to complete verified episode assets in
the canonical episode workspace without duplicating them into `H:\Youtube`.

## Scope

- Propagate `--skip-export` from `scripts/elr.py` through the production monitor.
- Keep optional external export available when the flag is omitted.
- Make the repository production skill use workspace-only delivery by default.
- Cover command construction with unit tests and update pipeline documentation.
- Resume episodes 019-021 with workspace-only delivery after verification.
- Remove the Windows command-length limit from large episode audio concatenation.

## Status

- [x] Confirm the existing packer already supports `--skip-export`.
- [x] Implement public-controller propagation.
- [x] Update tests and documentation.
- [x] Run focused tests and encoding checks.
- [x] Resume and verify episodes 019-021. All nine requested Series A/B/C
  workspaces contain MP4, mastered WAV, and subtitle artifacts. Episode 021
  Series C completed after the concat command-length fix.

## Decisions

- Do not delete or overwrite existing `H:\Youtube` packages.
- Keep `--youtube-root` for explicitly requested external exports.
- A workspace-only run is complete when the canonical workspace MP4 and its
  packaging/QC artifacts pass the existing pack verification steps.

## Verification

- Focused Python tests: 8 passed.
- Repository encoding check: passed.
- `git diff --check`: passed.
- Episode artifacts: 9/9 Series A/B/C episode 019-021 workspaces verified.
