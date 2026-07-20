# 2026-06-28 Dialogue Podcast Script Skill

## Goal

Create a project-level skill for writing two-person English dialogue podcast scripts, backed by a reusable local YouTube research corpus from high-performing videos in the requested channels.

## Scope

Included:

- A `.cursor/skills/dialogue-podcast-scriptwriting/` skill package with workflow, research, template, and QC guidance.
- Python scripts for collecting YouTube metadata/descriptions/transcripts with `yt-dlp`, analyzing the local corpus, and generating a Markdown report.
- Local artifact layout under `workspace/dialogue_podcast_research/youtube_corpus/`.
- Focused smoke/test coverage for local parsing and analysis helpers.

Non-goals:

- Downloading YouTube video or audio files.
- Committing generated transcript corpora or other large local research artifacts.
- Building the audio rendering side of the podcast pipeline.
- Copying transcript passages into reusable templates.

## System Boundaries

- `.cursor/skills/dialogue-podcast-scriptwriting/`
- `.cursor/skills/dialogue-podcast-scriptwriting/scripts/`
- `apps/worker-py/requirements.txt`
- `apps/worker-py/tests/`
- `docs/exec-plans/completed/`

## Status

Completed. The dialogue podcast scriptwriting skill, YouTube corpus collector, analyzer, report generator, offline top-N selector, script validator, and focused tests are implemented.

## Plan

1. Add the active execution plan for the dialogue podcast scriptwriting vertical slice.
2. Add `yt-dlp` as the collection dependency.
3. Implement a resumable YouTube collector that archives metadata, descriptions, and available captions/transcripts for the configured channels.
4. Implement corpus analysis and Markdown report generation.
5. Create the project skill and supporting docs from the analysis workflow and existing project skill conventions.
6. Add focused tests for helper behavior and analysis output.
7. Run encoding, Python compile, tests, and targeted script smoke checks.

## Validation

- Passed: Python compile check for the new skill scripts.
- Passed: `.\.conda-env\python.exe apps/worker-py/scripts/run_tests.py apps/worker-py/tests/test_dialogue_podcast_research.py`
- Passed: collector smoke mode against one item per channel.
- Passed: full collection for the configured channels, followed by local top-20 selection per channel.
- Passed: analyzer and report generator against collected local data.
- Known existing failure: `npm run check:encoding` still reports CRLF in unrelated audiobook files that predated this slice.

## Risks And Decisions

- YouTube captions and metadata availability can vary; collection records explicit status fields and continues on per-video failures.
- `yt-dlp` can break when YouTube changes; scripts are resumable and keep dependency use isolated.
- Full transcripts are generated local research artifacts and should stay out of git by default.
- The skill uses aggregate patterns and short original examples, not copied transcript text.
- Current working tree contains unrelated audiobook changes, so this slice avoided modifying or reverting those files.
- A second collector rerun stalled while rescanning YouTube; the process was stopped and local metadata was used to rebuild the top-20 selection list.

## Archive Criteria

- Completed: The project skill and supporting scripts are implemented.
- Completed: Validation passed except for documented pre-existing encoding failures.
- Completed: The active plan was moved to `docs/exec-plans/completed/`.
