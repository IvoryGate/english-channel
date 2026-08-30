# Shorts Visual Quality — 2026-09-07 Cycle

## Goal

Prevent the next Shorts cycle from repeating dark or duplicated visual assets,
and build an evidence-led image system for women aged 25-44 in the United
States without sacrificing originality or production traceability.

## Scope

Included:

- Capture and code at least 30 public high-view thumbnails from direct and
  adjacent competitors before the next content briefs are approved.
- Produce one original generated background for every Short.
- Enforce audience, uniqueness, brightness, saturation, and phone-size review
  gates in the Shorts production contract.
- Preserve the approved bright anime direction, expressive adult women, lively
  color, and playful flexible typography.
- Record research evidence and generated-image provenance for every asset.

Excluded:

- Retrofitting the already-uploaded `weekly-2026-08-31` Shorts.
- Copying competitor wording, characters, layouts, or protected artwork.
- Treating raw view count as proof that one thumbnail element caused success.

## System Boundaries

- `configs/shorts/product-weekly-scale.json`
- the next weekly Shorts portfolio config
- `apps/worker-py/worker/shorts/contracts.py`
- `apps/worker-py/worker/shorts/qc.py`
- `apps/worker-py/worker/shorts/packaging.py`
- `apps/worker-py/tests/test_shorts_pipeline.py`
- `docs/shorts/VISUAL_RESEARCH_METHOD.md`
- runtime research under `workspace/shorts/research/`

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-30 Asia/Shanghai.
- State: quality contract, exact legacy exception, automated luma/saturation
  checks, US women audience contract, and research method are implemented.
  The live high-view reference capture and next-cycle image generation remain
  pending until the next weekly portfolio is planned.

## Plan

1. Capture at least 30 public thumbnails with views, age, and views-per-day.
2. Code observable layout, character, color, emotion, typography, and promise
   patterns; separate direct competitors from adjacent women-led education.
3. Write original visual hypotheses and assign one unique scene to each Short.
4. Generate each background independently with recorded prompt and provenance.
5. Run path uniqueness and pixel gates, then render the full cycle.
6. Review a phone-size contact sheet for repeated staging, dark faces,
   artifacts, weak emotion, and US-women audience mismatch.
7. Regenerate failed assets only; do not waive visual gates for schedule speed.

## Validation

- The next portfolio fails without a named 30-image high-view research artifact.
- The next portfolio fails if any background path is used more than once.
- Packaging fails below average luma 125 or average saturation 22.
- Every manifest records `United States` and `women 25-44` as the primary
  audience signal.
- Human contact-sheet review approves all assets at phone size.
- Focused Shorts tests, encoding, docs, and architecture checks pass.

## Risks And Decisions

- Pixel thresholds block obviously dark batches but cannot judge emotional or
  cultural fit; human contact-sheet review remains mandatory.
- High-view examples contain topic and channel-size confounds. They inform
  hypotheses rather than authorizing imitation.
- Character consistency may be shared across a cycle, but scene staging,
  action, framing, and background cannot be reused.
- The current uploaded cycle has a single exact exception because the owner
  chose not to rework it. No date range or wildcard exception exists.

## Archive Criteria

- The next weekly portfolio includes a valid research artifact.
- Every Short uses independently generated, traceable art.
- Automated and contact-sheet gates pass with no exception.
- The accepted visual hypotheses and failures are recorded for the next review.
