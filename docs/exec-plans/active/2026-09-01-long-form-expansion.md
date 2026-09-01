# Long-Form Expansion And Topic Portfolio

## Goal

Recover long-form discovery and watch time by turning the missing 40-minute
format into a real production lane, broadening the dialogue shows beyond
language mechanics, and making current demand evidence a required input to
weekly programming.

## Branch

`codex/long-form-expansion`

## System Boundaries

- Channel strategy and release contracts: `configs/channel/`.
- Script and editorial standards: `docs/shows/`.
- Durable plan state: `docs/exec-plans/active/`.
- Configuration regression checks: `apps/worker-py/tests/`.

## Evidence baseline

- YouTube Studio, 2026-08-04 through 2026-08-31: long-form views 1,710
  (`-33%` versus the previous 28 days), impressions 48,786 (`-37%`), CTR
  `2.5%`, and average view duration `2:19`.
- The three videos scheduled as Deep Practice for 2026-09-03 through
  2026-09-05 are only `14:46`, `14:44`, and `13:31`. Duration therefore did
  not satisfy the recorded 25–35 minute contract.
- Channel-specific Studio Trends identifies high search volume for
  `how to stop overthinking` and `overthinking motivational video`, medium
  volume for `stoicism philosophy podcast` and `stoicism philosophy
  audiobook`, and current demand for real-conversation listening.
- United States Google Trends, YouTube Search, trailing 90 days gives the
  compared-term averages: `english conversation` 19, `english listening` 10,
  `self improvement` 23, `overthinking` 31, and `stoicism` 35. These are
  normalized relative-interest values, not absolute search volumes.

## Scope

- Write a dated market and channel diagnosis with traceable sources.
- Add a 35–45 minute flagship format with a target runtime of 38–42 minutes.
- Keep three 10–15 minute episodes per week, but diversify their subject
  engines across practical English, everyday life, relationships, psychology,
  resilience, and philosophy.
- Use the remaining three dialogue slots for one flagship and two 18–25 minute
  extended episodes during the recovery phase.
- Add a weekly trend-research contract and a dated 2026-09-07 production plan.
- Add tests that prevent a future weekly plan from calling a sub-35-minute
  target a flagship.

## Non-goals

- Do not change the fixed publishing hours before the scheduled review.
- Do not copy competitor scripts, titles, thumbnails, voices, or attributed
  speeches.
- Do not turn the channel into generic self-help. English listening remains
  the delivery promise and every episode must provide comprehensible input,
  useful language, or guided participation.
- Do not make medical, therapeutic, or historical claims without evidence and
  editorial review.

## Plan

1. Record the current Studio diagnosis, competitor cohort, and trend evidence.
2. Define standard, extended, and flagship runtime/quality contracts.
3. Create the 2026-09-07 weekly plan with one 40-minute flagship and a broad
   topic portfolio across all three dialogue series.
4. Add configuration invariants and automated tests.
5. Run JSON, pytest, encoding, and repository quality checks.

## Validation

- Parse every changed JSON document.
- Run the long-form programming tests and the existing worker test suite.
- Run repository encoding and quality gates required by `docs/QUALITY_SCORE.md`.
- Inspect the diff for stale Deep Practice claims and schedule drift.

## Release gates

- Flagship script has 5,200–6,200 spoken words or an equivalent measured
  narration plan and a projected runtime of 38–42 minutes.
- Rendered media duration must be 35–45 minutes before it may carry the
  `flagship_40` format label.
- A new stimulus, scene, question, speaker goal, or participation mode appears
  at least every four minutes.
- First useful idea or line arrives inside 90 seconds; first 30 seconds contain
  a concrete human stake.
- Psychology and philosophy episodes pass factual-attribution and harmful-
  advice review.
- YouTube package has three native thumbnail/title test variants before upload.

## Status

- Owner: primary Codex agent.
- Last updated: 2026-09-01.
- Current channel data collected: complete.
- Current trend and competitor evidence collected: complete.
- Runtime and portfolio contract: complete.
- Weekly plan and configuration tests: complete.
- Validation: JSON parse, encoding, docs, architecture, Python compile, and all
  175 Python tests pass. The local TypeScript test processes cannot start
  because Windows returns `ENOMEM` from `uv_os_get_passwd`; tooling smoke tests
  still pass. Remote CI is required before merge.
- PR: pending.

## Risks And Decisions

- Longer runtime cannot compensate for weak retention. The first flagship is
  one controlled weekly treatment, not an immediate conversion of all six
  dialogue slots.
- Broad topics can confuse channel identity. Each treatment retains an English
  listening/participation job and is assigned to a clear series level.
- Trend tools expose relative demand and can contain false-intent collisions.
  Candidate scoring and editorial review remain mandatory.
- Current uploaded Deep Practice assets are kept; the repository records them
  honestly as standard-length results instead of deleting or relabeling media.

## Archive Criteria

Move this plan to `completed/` only when the research report, programming
contract, dated weekly plan, stale-state correction, tests, and validation all
ship in the same merged PR. Actual episode production remains tracked by the
dated weekly plan rather than this engineering plan.
