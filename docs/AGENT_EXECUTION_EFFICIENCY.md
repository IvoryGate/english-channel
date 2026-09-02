# Agent Execution Efficiency

## Purpose

Keep autonomous production fast, deterministic, and economical without
weakening the release gates that protect public quality or channel state.

## Default operating rule

Use the cheapest reliable mechanism that has already proved sufficient:

1. call a deterministic local script for stable transforms and checks;
2. reuse a fresh recorded result when its inputs and artifact hashes match;
3. call a language or image model only for genuinely creative judgment;
4. use browser control only when the API or stable script cannot complete or
   verify the operation.

Do not ask a model to recalculate schedules, assemble known metadata, validate
JSON, derive chapter timestamps, build standard descriptions, select fixed
voice settings, or repeat an unchanged preflight. Those operations belong in
versioned scripts and configuration.

## Proportional validation

Defensive programming is not a goal. Evidence is.

- Run one authoritative preflight at each state transition.
- Cache its input fingerprint, tool version, result, and timestamp.
- Re-run only when an input, dependency, remote state, or release requirement
  changed, or when the prior result is older than its defined freshness limit.
- Prefer one full check over several overlapping partial checks.
- Use sampling for low-risk visual or timing surveillance; use full scans only
  at final release, after repair, or for a known high-impact failure mode.
- Stop after an authoritative success signal. Do not confirm the same fact on
  multiple UI surfaces unless the signals conflict.
- Keep proven production concurrency and batch defaults. Do not lower them for
  hypothetical safety; require a measured memory, quality, or failure signal.
- On failure, diagnose the failing boundary once and retry only the affected
  stage. Do not restart the entire pipeline by default.

## Risk tiers

| Tier | Examples | Required verification |
| --- | --- | --- |
| Low | local planning, deterministic metadata, cached research parsing | schema/unit check once |
| Medium | script assembly, audio segment batch, thumbnail generation | focused gate plus sampled review |
| High | final render, captions, public upload, scheduling, identity mapping | complete release preflight and remote success reconciliation |
| Exceptional | deletion, credentials, copyright/policy response, monetization | explicit owner authority and full audit trail |

## Model-use budget

- One creative brief may receive one primary drafting call and one focused
  revision call. Additional calls require a named defect, not vague
  dissatisfaction.
- Batch independent briefs into one bounded planning pass when the same context
  applies.
- Store accepted prompts, structures, rubrics, and outputs so later stages use
  files rather than re-prompting.
- Never use an LLM as a loop controller, scheduler, checksum verifier, file
  copier, JSON formatter, upload client, or status poller.

## Browser-use budget

- Prefer authenticated API/CLI publication and analytics scripts.
- Open Studio only for missing fields, failed remote reconciliation, UI-only
  experiments, or platform changes.
- During a browser run, collect all due rows in one pass and close temporary
  tabs when finished.

## Completion discipline

Complete the requested production slice before proposing optional safeguards.
Block only on a real release, safety, authority, or data-integrity failure.
Record warnings without turning every warning into a stop condition.
