# Audio Quality Contract And Bounded Audition

## Goal

Execute the first audio repair from PRODUCT_REBUILD.md: spoken output,
captions and chapter metadata must share measured timing; applied performance
controls must match their trace and cache identity. Deliver a bounded blind
audition using installed models for owner listening, without public promotion.

## Scope

Variable pauses and mastered timing across composition/subtitles/chapters/QC;
validated per-turn provider controls; offline bounded audition runner and
review exports. Preserve existing productions and prepare repair evidence
separately. No published-video changes, new paid spend or model downloads.

## System Boundaries

`workspace/shows/tools/`, subtitle alignment helpers, `worker/tts/`, audition
CLI, focused tests and audio docs. Existing GPU lease remains mandatory.
Port only the reviewed checkpoint loader/visibility changes required for this
trial; do not merge the entire October checkpoint.

## Status

2026-11-07, Codex. Implementation scope complete on `codex/audio-quality-contract` from `009dfa0`
after foundation PR #22 passed and merged. Agents split timeline, provider/
audition and independent analytics work; analytics has its own branch/plan.

2026-11-07: implementation delivered in PR #23; analytics PR #24 passed and
merged separately, then was integrated without rewriting branch history.
Initial full checks passed 289 Python tests; staged-runtime changes passed
292 tests plus all Node/lint gates. Independent reviews cover timeline,
provider controls, loader/process visibility and recovery accounting.

Actual v2 trial failed with CUDA OOM on its first pair after 105.406 seconds,
with 2 attempts and no audio output. The v3 trial uses explicit staged CPU
offload for both arms, preserves FP32 weights, and carries prior time and
attempts into the same 30-minute/28-total-attempt ceiling. V3 then failed during
SciPy import with MemoryError, before loading the model. Cumulative accounting
is 4 attempts, 0 completed takes and 115.687 seconds. The repeated-failure stop
rule has halted this trial; no remaining candidates or full episodes are run.
Staged inference remains runtime-unverified despite passing code tests.
No source settings or old recordings were changed to hide the failed run.

A CUDA-hidden, import-only diagnostic subsequently succeeded in 22.54 seconds;
the v3 MemoryError was not reproduced and its cause is unresolved. No additional
generation followed. Host measurement corrected RAM inventory to approximately
32 GB; sampled device memory during failed imports is not model peak memory.
The implementation meets this plan's archive criterion by delivering code,
tests, measured A045 repair evidence and the exact retained trial blocker.
Sound acceptance and staged-runtime feasibility remain open in the product
roadmap. PR #23's integrated code head passed quality-gates and evaluate;
final documentation archival is part of the same PR.

## Plan

1. Implement one timeline contract, preserving legacy master evidence.
2. Wire supported controls into synthesis, traces and cache identity.
3. Implement bounded offline audition and measured matched-loudness pairs.
4. Run focused/full checks and review the production-diff regression.
5. Produce the short audition if existing model/reference/resource checks pass;
   stop on a real runtime failure or specified budget and retain partial evidence.
6. Push scoped PR, resolve checks and archive completed implementation scope.

## Validation

Variable-gap fixture; mastered-tempo chapter/subtitle regression; stale master
rejected; legacy report reconstruction; unsupported/invalid settings rejected;
effective settings change invalidates cache; audition budgets/resume/trace tests.
Real A045 packaging comparison read-only against E archive, outputs only on H.
Full repo gates; bounded real audition is evidence of production, not subjective
quality acceptance. Human blind review remains explicitly pending.

## Risks And Decisions

No stage-direction text is spoken. Existing settings stay default. No inference
that numerical exaggeration automatically matches editorial emotion. Runtime
leases perform normal writes to the existing resource system; no schema repair
or downgrade is authorized. Preserve 2-turn Chatterbox batches and a 5-minute
watchdog. Known schema drift must not trigger new migrations during the trial.

## Archive Criteria

Code/tests/docs and real timing evidence delivered through a passing scoped PR;
audition outputs or exact runtime blocker recorded; listening approval is a
subsequent product decision and cannot be fabricated.
