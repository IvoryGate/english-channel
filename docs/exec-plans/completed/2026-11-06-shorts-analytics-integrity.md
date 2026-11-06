# Shorts Analytics Evidence Integrity

## Goal

Prevent absent analytics from becoming measured zero or supporting growth
decisions. Preserve explicit zero and expose incomplete and legacy evidence.

## Scope

Version-two Shorts snapshots, nullable numeric/derived metrics, API absence
semantics, conservative review decisions, tests and operator documentation.
No remote requests, OAuth setup, policy changes or historical snapshot rewrite.

## System Boundaries

`worker/shorts/analytics.py`, `youtube.py`, `review.py`, focused tests and
`docs/shorts/README.md`. Preserve the current scoring weights and thresholds.

## Status

2026-11-07, agent metrics_integrity. Implementation and review correction complete on
`codex/analytics-missing-evidence` from trunk `009dfa0`, in the isolated
`.worktrees/rebuild-metrics` checkout.

Delivered v2 field-availability contracts and content-addressed captures;
legacy values retained separately but excluded from decisions; API absence and
unsupported attribution are explicit; score/scale/format changes require
complete evidence without reweighting. Original v1 snapshots remain untouched.
Review distinguishes recorded rows, rows with observations and complete scores.

Validation: 43 focused tests passed (22 new analytics-integrity cases and 21
existing Shorts pipeline cases). Encoding, docs, architecture and diff checks
passed. No live API calls, authentication changes or root-worktree edits.
Root validation: all 271 Python tests passed on the normal Windows host.
Independent re-review passed the API-recovery fix and all 22 new integrity
tests. Commit and remote CI/PR are handled by the root agent.

Independent review found that an API recovery to an earlier identical payload
reused the first capture timestamp, leaving a later missing capture selected.
Corrected by including capture time in live collection identity while preserving
immutable file-import deduplication. An observed -> missing -> recovered API
regression verifies three distinct immutable captures and recovery selection.

## Plan

1. Define v2 field availability and explicit legacy semantics.
2. Preserve missing API/CSV values and unsupported attribution.
3. Require complete evidence before scoring, scaling or reallocating formats.
4. Test real zero, missing/invalid values, API absence and legacy snapshots.
5. Document limitations, validate and archive the implementation scope.

## Validation

Focused analytics and existing Shorts tests; encoding, docs and architecture
gates. Fixtures must prove complete evidence still supports existing decisions
while missing evidence cannot manufacture a winner or a numeric score.

## Risks And Decisions

- V1 has already lost missing-vs-zero provenance. Keep original files and
  expose legacy-unverified values; require original-source reimport for scores.
- A zero denominator cannot yield a measured zero ratio.
- No silent metric reweighting: API-only snapshots lack long-form attribution
  and cannot satisfy the existing complete composite-score contract.
- Current host has neither configured OAuth client/token environment variables
  nor the default token file. This is a present access gap, not an API failure.
- Window matching, publication age, identity inventory and live data ingestion
  are separate slices; this change does not certify experimental causality.

## Archive Criteria

Implementation, focused regression coverage and docs complete with validation
recorded. Root agent owns commit, PR, full gates and merge review.
