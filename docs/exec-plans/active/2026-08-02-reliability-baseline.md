# 2026-08-02 Reliability Baseline

## Goal

Restore a trustworthy local quality baseline for the English Listening Room production workflow and resolve the highest-impact correctness defects identified in the project review.

## Scope

- Repair Python test discovery and add regression coverage for voice-profile reference selection.
- Normalize repository-owned text files to UTF-8 without BOM and LF line endings.
- Keep generated logs, render outputs, and temporary prompt files outside source-control quality gates.
- Correct the Series A host reference-audio mapping.
- Assess and begin a compatible, durable API-to-worker job execution path.

Non-goals:

- Regenerating audio or video artifacts.
- Rewriting the complete content-production pipeline.
- Publishing or uploading any YouTube material.

## System Boundaries

- `apps/worker-py/`
- `apps/api/`
- `.gitignore`, `packages/tooling/`, and repository quality scripts
- `docs/`

## Status

- **State:** active
- **Owner:** Codex
- **Last update:** 2026-08-02 — source-only snapshot created; test-path and Series A voice-profile fixes in progress.

## Plan

1. Create a source-only safety snapshot and preserve generated artifacts locally.
2. Fix the broken test import path and Series A reference-audio mapping; add focused coverage.
3. Define generated-artifact ignore rules and normalize tracked text files.
4. Run encoding, static, and unit-test gates; fix deterministic failures.
5. Implement and test the selected API-to-worker job path, including durable job-state handling.
6. Update operational documentation, rerun all feasible gates, and archive this plan when complete.

## Validation

- `npm run check:encoding`
- `npm run lint`
- `npm test`
- `./.conda-env/python.exe apps/worker-py/scripts/run_tests.py`
- Targeted API job-path test without a live GPU model.

## Risks And Decisions

- The current Node API uses BullMQ while the Python worker uses RQ; they cannot consume one another's Redis job representations. The job-path design must use one compatible ownership model before async delivery can be claimed.
- The local host has recently reported low-memory failures in Node test startup. Diagnose environment limits separately from application failures.
- Existing generated artifacts are intentionally preserved locally and must not be deleted or committed.

## Archive Criteria

- The listed correctness and quality-gate failures are resolved or explicitly documented with reproducible environment evidence.
- A compatible job execution path has automated coverage.
- Documentation describes the operational configuration accurately.
