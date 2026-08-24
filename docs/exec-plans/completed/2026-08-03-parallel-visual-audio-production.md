# Parallel Visual And Audio Production

## Goal

Let approved episode scripts begin VoxCPM turn rendering while the remote cover
and video-background images are still being generated. Preserve the full visual
gate before packaging so no episode can be composed or exported with missing
assets.

## Scope

- Add a public audio-first command to `scripts/elr.py`.
- Add an internal turns-only mode to the render monitor.
- Split audio-ready checks from pack-ready visual checks.
- Document the concurrent agent workflow and durable state phases.
- Add focused unit tests and CLI smoke checks.

Non-goals: concurrent VoxCPM jobs, repository-driven image generation, and
removing any final thumbnail/background/QC/export gate.

## System Boundaries

- `scripts/elr.py`
- `scripts/elr_production.py`
- `scripts/monitor_episode_render.py`
- `apps/worker-py/tests/`
- `README.md`
- `docs/shows/EPISODE_PIPELINE.md`
- `.cursor/skills/elr-episode-production/SKILL.md`

## Status

- State: completed
- Owner: Codex
- Last updated: 2026-08-03

## Plan

1. Completed: introduced audio-only preflight without weakening formal pack preflight.
2. Completed: added resumable `render-audio` orchestration and turns-only monitoring.
3. Completed: covered command construction, preflight boundaries, and state behavior in tests.
4. Completed: updated operator and Skill documentation.
5. Completed: ran targeted quality gates and prepared the plan for archive.

## Validation

- Focused Python tests for ELR preflight/orchestration/render monitor.
- `scripts/elr.py render-audio --help` and a dry run against episode 017.
- Encoding check.
- Existing ELR test slice.

## Risks And Decisions

- Only remote image generation and local audio rendering may overlap. VoxCPM
  jobs remain serialized behind the global GPU lock.
- Audio-first mode renders turn WAVs only. Formal `produce`/`resume` still owns
  QC, mastering, subtitles, composition, packaging, verification, and export.
- Missing visuals remain a hard error in formal production.

## Archive Criteria

The public command, tests, documentation, and Skill instructions agree on the
same workflow; all targeted checks pass; the plan moves to `completed/` in the
finishing commit.
