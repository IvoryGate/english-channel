# Persuasion Caption And Media Recovery

## Goal

Repair the published `Persuasion` chapter 2 media timeline, restore selectable
English captions for chapters 1 and 2, and prevent another chapter from passing
release checks with incompatible stream time bases, frozen video, or captions
that omit the intro offset.

## Scope

Included:

- Replace the legacy stream-copy chapter composition with timestamp-reset,
  normalized H.264/AAC composition.
- Generate YouTube SRT cues on the final-video timeline, including intro offset.
- Add automated media-integrity gates and focused regression tests.
- Recompose chapter 2 from protected existing audio, subtitles, scenes, intro,
  and outro without regenerating the narrator.
- Verify audio, burned subtitles, selectable captions, frame progression, and
  duration at the beginning, middle, and end.
- Upload a corrected chapter 2 privately, attach captions and existing approved
  packaging, pass platform checks, then replace the public listing and retire
  the defective upload.
- Reconcile the chapter 1 selectable English caption track without replacing
  its synchronized video.

Excluded:

- Changing narration voice, source text, thumbnail experiment, or chapter
  content.
- Deleting protected source media.
- Publishing later chapters before the new release gates pass.

## System Boundaries

- `apps/worker-py/worker/classics/chapter_package.py`
- `apps/worker-py/worker/classics/v2_chapter.py`
- `apps/worker-py/tests/test_classics_chapter_package.py`
- `apps/worker-py/tests/test_classics_v2_proof.py`
- `docs/classics/AUTONOMOUS_OPERATING_MODEL.md`
- Runtime media under the protected Persuasion workspace and YouTube exports.
- YouTube video IDs `EkAVjpGf1_Q` and `tdTlhg49vTk` plus the corrected private
  upload created by this recovery.

## Status

- Owner: Codex primary agent.
- Branch: `codex/persuasion-caption-recovery`.
- State: recovery implemented and remotely verified; PR preparation in progress.
- Confirmed incident: chapter 2 used `-c copy` across `1/90000` intro/outro
  video and a `1/15360` body stream. The final video advances body frames too
  quickly and then freezes while audio continues. Its packaged SRT also omits
  the 10.048-second intro offset. Chapter 1 media is synchronized, but its
  public player exposes no selectable captions.

## Plan

1. Add regression tests for normalized concat and intro-shifted YouTube SRT.
2. Implement shared timestamp-reset composition and media-integrity validation.
3. Update Classic Listening documentation and release gates.
4. Recompose chapter 2 from the existing approved assets and generate a fresh
   YouTube caption file.
5. Run focused tests, repository gates, ffprobe checks, frame-progress checks,
   and sampled ASR-to-caption comparisons.
6. Upload corrected chapter 2 privately, attach captions/thumbnail/playlist,
   wait for processing and platform checks, then publish and retire the broken
   upload.
7. Restore chapter 1 selectable captions and verify both public players.
8. Commit, push, open a PR, and archive this plan when all code and remote work
   are complete.

## Validation

- Intro, body, and outro timestamps are reset before concat and the output is
  fully re-encoded.
- Final audio/video duration drift is at most 100 ms.
- Frames sampled across the body progress instead of repeating or freezing.
- Burned captions match sampled audio at the start, middle, and end.
- YouTube SRT first cue equals body cue start plus measured intro duration.
- Public chapter 1 and corrected chapter 2 players expose English CC.
- Focused Python tests and required repository checks pass.

## Risks And Decisions

- YouTube cannot replace the media file of an existing video. Chapter 2 must be
  uploaded as a new private video before the defective upload is retired.
- The existing defective chapter 2 has very low traffic, so a controlled
  replacement is less harmful than leaving a broken eleven-minute experience
  public.
- Chapter 1 does not need a duplicate upload; only its remote caption state is
  reconciled.
- Protected source and generated media remain intact throughout recovery.

## Recovery Evidence

- Corrected chapter 2 video: `vGlh8DYpLP4`, public, platform checks passed.
- Defective chapter 2 video: `tdTlhg49vTk`, retained as unlisted.
- Chapter 1 video: `EkAVjpGf1_Q`, authored English captions published.
- Public transcript export for both chapters reports language `en`, authored or
  unspecified captions, and the expected first cue at `0:10`.
- Corrected chapter 2 local timeline gate: 65 ms audio/video duration drift,
  0.334 ms input/output duration drift, and 66.666 ms maximum video packet gap.
- Four ASR-to-caption samples at 20, 120, 300, and 600 seconds passed with
  similarities from 0.9707 to 0.9929.
- The complete Python worker suite passes: 168 tests.
- `npm run lint` passes all encoding, TypeScript, architecture, documentation,
  Remotion, and Python compile checks. Local `tsx` test workers could not start
  because Windows returned `uv_os_get_passwd ENOMEM`; web and tooling tests
  passed, and the clean PR CI environment remains the required Node test gate.

## Archive Criteria

- Code, tests, and docs are merged through a passing PR.
- Corrected chapter 2 is public and verified; the defective upload is no longer
  the canonical public chapter.
- Chapter 1 and corrected chapter 2 expose selectable English captions.
- Runtime verification records contain hashes, probes, sampled sync evidence,
  and remote video/caption IDs.
