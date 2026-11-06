# Brand Motion And Sound V4

## Goal

Deliver an engaging, short ELR intro and a useful outro with audible,
frame-aligned sound design, reusing suitable vibecut craft rather than models.

## Scope

Independent 3.5-second intro and 20-second end-screen candidate; reusable
Remotion props, original CPU-generated stereo sonic identity, rendered MP4s,
measured audio checks and visual review. Preserve existing production plates
and all previously published episodes. No model downloads or weight copies.

## System Boundaries

`src/brand/`, `scripts/build_brand_audio.py`, focused tests, and
`docs/shows/BRAND_MOTION_SOUND.md`. Generated previews live only in
`workspace/branding/v4/`; generated WAVs in ignored `public/branding/v4/`.

## Status

2026-10-18, Codex. Branch `codex/brand-motion-sound-v4` created from refreshed
origin/main. Existing unrelated dirty files preserved. Audited vibecut skills
youtube-intro-outro, motion-art-direction and beat-sync-editing; its MusicGen
CLI, SOUND.md and existing ELR compositions.

Candidate implementation and local media verification complete: independent
intro/outro MP4s in `workspace/branding/v4/`, measured 3.500/20.000 seconds,
1080p30 H.264 plus 48 kHz stereo AAC. Encoded peaks -5.2 dBFS, no clipping.
Frame 24 impact, intro hold 70 and outro hold 90 inspected. Focused synthesis
test, TypeScript, encoding and docs checks passed. Exact evidence/hashes in
`workspace/branding/v4/review.json`. Owner listening review and promotion are
pending; legacy assets remain untouched. Scoped commit/PR still to be prepared;
no GitHub CLI is installed in this runtime.

Owner revision: initial click rejected and intro requested more animated with
spoken welcome. Root cause measured: the cosine impact jumps from zero to
0.50116 full scale at 0.8 seconds despite no clipping. Replace with zero-start
18ms-attack chime, reduce filtered air, add sample-step regression checks.
Revise candidate to five seconds with orbit/light accents and CPU Kokoro
welcome. Re-render corrected outro audio too; no public/default changes.

Revision 2 delivered locally as `intro-r2.mp4` (5.000s) and `outro-r2.mp4`
(20.000s), both 1080p30 with stereo AAC. Welcome is 3.8s from 0.4s, Kokoro
Heart on CPU with existing offline cache. Regression test passes; quantized
reveal boundary step is 0.0, encoded peaks -5.4/-11.2 dBFS. Actual exported
frame inspected. Evidence: `workspace/branding/v4/review-r2.json` and voice
trace. Owner subjective review remains pending; do not reuse v1 as latest.

Revision 3 requested: add invitation and SUBSCRIBE press/rebound/particle
animation in lower middle, center avatar caption precisely. Preserve the
approved welcome, palette and five-second duration. Implemented with frame
72 entrance / 112 press / 118 particles; pending rendered review.

Revision 3 rendered and checked: `intro-r3.mp4`, 5.000 seconds, 1080p30
stereo, encoded peak -5.4 dBFS. Press still 113 and actual exported particle
frame 126 inspected. Both text lines beneath the avatar share its horizontal
center. Focused audio regression, TypeScript, encoding and docs checks pass.
Evidence in `workspace/branding/v4/review-r3.json`; awaiting owner review.

Owner accepted other details and requested replacing the hand-drawn cursor.
Revision 4 uses the official Lucide mouse-pointer-2 path with local ISC notice;
only its appearance changes, preserving the rest of the approved sequence.

Revision 4 delivered as `intro-r4.mp4` (5.000s, 1080p30, stereo AAC). Audio
stream copied unchanged from r3. Actual export frame 113 inspected; SVG XML,
TypeScript, encoding and docs checks passed. Evidence: review-r4.json.

Next owner request: improve outro to match the accepted intro. Add short CPU
Kokoro Heart thank-you / subscribe / next-listen narration, reuse the Lucide
cursor/button burst on the left, and retain a quiet native end-screen hold.
No intro media or production defaults are changed by this revision.

Outro revision 3 delivered: `outro-r3.mp4`, 20.000 seconds, 1080p30 stereo,
peak -5.9 dBFS. CPU Kokoro voice 5.4s from 0.4s; smooth bed recovery at 7-8.5s.
Press frame126 and actual exported 10s hold inspected; right native overlay
zones clear. TypeScript, audio regression, encoding/docs checks pass. Local
renderer needed approved elevation after sandbox browser connection failure.
Evidence: `workspace/branding/v4/review-outro-r3.json`. Owner review pending.

Owner rejected the empty native end-screen layout. Replace it with a complete
8-second thank-you/subscribe close, matching the intro portrait card. Remove
both empty overlay zones and all next-video wording, regenerate only closing
speech, keep the approved Lucide button effect. Intro remains unchanged.

Complete close delivered: `outro-complete.mp4`, 8.000 seconds, 1080p30 stereo
AAC, peak -5.4 dBFS. New narration 4.9s, no next-video wording. Both empty
zones removed. Actual frame150 inspected; existing focused tests and gates
pass. Evidence: `workspace/branding/v4/review-outro-complete.json`.

## Plan

1. Define warm editorial motion, timing, sound cues and license boundaries.
2. Build original stereo audio with reproducible provenance and QC.
3. Add candidate compositions without replacing production defaults.
4. Inspect critical frames, encode both MP4s, verify sound and duration.
5. Deliver candidates for owner review; promotion is a separate recorded step.

## Validation

Focused audio generator tests; TypeScript check; encoded duration, audio
presence, peak/tail checks; inspect intro impact/hold and end-screen zones.
Do not claim subjective sound approval or retention improvement from QC.

## Risks And Decisions

MusicGen stereo-small weights are CC-BY-NC-4.0; excluded from this public-use
candidate. Local third-party SFX have no per-asset license evidence in the
inspected files; do not copy them. Original synthesis has no external samples.
Skill retention/CTR assertions are hypotheses, not measured channel results.
YouTube supports end screens in the final 5-20 seconds; 20 seconds is a design
choice, not a platform minimum. End-screen overlays require Studio setup.

## Archive Criteria

Candidate source, tests, documentation and verified rendered samples delivered
in a scoped PR. Owner approval and default promotion may follow separately.
