# Audiobook Opt-In Workflows And SRT

## Goal

Document selective segment operations as explicit user-triggered steps, and add SRT generation aligned to finalized segment WAV timings and compose silence rules.

## Scope

Included:

- Skill and workflow policy updates for opt-in rerender, compose-only, inspect, and external trim flows.
- `generate_chapter_srt.py` and `SUBTITLES.md`.
- Shared timeline helpers in `audiobook_workspace.py`.

Not included:

- Automatic subtitle generation after every render.
- Forced segment rerenders or WAV trimming in scripts.

## Status

- State: in progress
- Branch: `feat/audiobook-skill-opt-in-srt`

## Validation

- `generate_chapter_srt.py` runs on `workspace/pride_and_prejudice/chapter_001`
- `npm run check:encoding`

## Archive Criteria

- PR merged with skill docs, SRT script, and plan archived to `completed/`.
