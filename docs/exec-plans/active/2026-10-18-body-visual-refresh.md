# Body Visual Refresh And Approved Branding

## Goal

Use the owner-approved five-second intro and eight-second complete outro for
future long-form production. Replace dialogue body bars with an audio-driven
radial spectrum, and deliver a readable phrase-caption candidate.

## Scope

Shared branding selection, dialogue waveform and subtitle adapters, regression
tests, documented defaults, and a preview using existing real episode audio.
Do not re-render published content, copy models, duplicate release videos, or
change Shorts. Classic narration keeps its source-specific body adapter;
route shared plates without destroying chapter identity/timestamp metadata.

## System Boundaries

`configs/branding/`, `workspace/shows/tools/compose_episode_video.py`,
`.cursor/skills/audiobook-chapter-tts/scripts/media/`, focused Python tests,
and production docs. Preview artifacts under `workspace/branding/body-v1/`.

## Status

2026-10-18 Codex, branch `codex/brand-motion-sound-v4`. Owner approved intro-r4
and outro-complete. Inspected existing fixed 2K layout, linear spectrum,
five-word karaoke, chapter-offset resolution and Classic adapter boundaries.
Unrelated dirty changes preserved.

Implemented dialogue radial/phrase-card rendering and approved plate binding.
Classic provider preserves chapters1-11 and routes chapter12+ to shared plates;
the chapter composer normalizes mixed input resolutions. Focused initial media
tests:15 passed after isolating environment plugins/temp directory. First 2K
preview failed a real libx264 allocation; capped encoder/filter concurrency and
reused completed spectrum overlay for recovery. The 16-second real-audio 2K
preview completed and frames at 3s and 8s were visually inspected. Focused
media, chapter-package and production tests: 27 passed. Encoding, architecture,
documentation checks and diff whitespace checks passed. Local candidate ready;
scoped PR integration remains pending on the existing branding branch.

Owner requested a larger, bolder white spectrum and larger avatar. Revised
overlay to 600px, avatar to 324px and bars to seven pixels with dark edging.
Second preview is isolated under body-v2; subtitles and source audio unchanged.
The 12-second 2560x1440 revision completed, the actual 3s frame was inspected
for contrast and subtitle separation, and ten focused tests passed.

Third owner revision rejects outlined ticks: use a 720px field of 48 thick white
light beams with soft bloom, 14px cores, longer extension and faster audio
response. Preserve the 324px avatar and caption layout. Preview under body-v3;
no source audio regeneration or published-content replacement.
The corrected white-alpha bloom passed eleven focused tests. An eight-second
2K real-audio preview completed and its actual 3s frame was visually checked.
Glow is white RGB with blurred alpha, not RGBA blurred toward black. Preview
overlay reuse is now explicitly opt-in for recovery, avoiding stale styles.

Owner supplied three reference frames and rejected exaggerated rays. Fourth
revision uses a fine connected ring, 96 short dense pulses, restrained glow,
local deformation and small peak dots. Keep white color, avatar and background;
do not copy reference screenshots, starfield, UI or watermarks. Cap extensions
near 32px and remove global amplitude boosting. Preview isolated under body-v4.
Owner subsequently explicitly requested color. Supersede the white-only choice
with green/cyan/blue/violet gradient and matching colored bloom. Stop the
superseded white preview and render only the updated candidate.
Owner clarified reference motion: inner-thread beads retreat inward at local
peaks; separate peak particles must fly outward beyond the short bars. Added
bounded audio-triggered particle state with cooldown, outward velocity and
fade/lifetime, without moving the avatar or adding unrelated background stars.
Colored reference-motion preview completed: 8 seconds at 2560x1440, actual
3s frame inspected. Thirteen focused tests passed, including local emission,
outward travel, expiry, short-pulse bounds, gradient and silence behavior.

Fifth owner revision: improve visibility moderately, not exaggerated rays.
Increase field to 800px, columns to 6px and beads to 6.4px. Decouple the thread
from fixed column roots: up to 60px inward displacement and independent temporal
response. The avatar is 360px. Preview uses body-v5; source audio unchanged.
The eight-second 2K preview completed and its actual 3s frame was inspected.
Fourteen focused tests passed, including independent thread displacement while
columns are settled, emission, decay and conservative pulse bounds.

Owner accepted the fifth revision's size and requested exactly half the inner
thread displacement. Reduce the coefficient .075 to .0375 (60px to 30px at
800px); retain field, avatar, columns, timing, palette and particles unchanged.
Preview under body-v6.
Fourteen focused tests passed; eight-second 2560x1440 preview completed.

Owner accepted smoothing proposal after 30fps / abrupt 70%-85% per-frame catch-up
was diagnosed. Seventh revision uses native 60fps through the compositor,
neighbor-band smoothing, critically damped position/velocity integration for
columns and independent thread, and soft particle birth. Preserve approved
geometry, gradient and half-amplitude thread. Particle triggers are time-based.
Preview under body-v7. No ASR/TTS or published-video work.
Fifteen focused tests passed, including 30/60fps time equivalence, gradual
onset, decay, particle fade-in and compositor FPS. The 2K eight-second preview
completed; final stream verified 60fps, 479 frames / 7.983333 seconds.

Owner approved v7 as the fixed standard for ALL future non-Shorts. Expanded
policy and both Classic body adapters to shared cards/radial spectrum, retaining
multi-scene transitions and original SRT. Cue-only narration does not invent
word-alignment highlights. Existing Persuasion1-11 / rendered videos stay intact.
Also begin a separate mobile Shorts candidate, without long-form plates/ring.
Approved-policy, shared cue cards, new-series episode1 branding, and multi-scene
60fps/overlay wiring are covered by tests. 59 combined media / Classic / Shorts
tests passed; TypeScript, encoding, architecture, docs and whitespace gates pass.

## Plan

1. Record approved canonical plate paths/hashes and future-use boundary.
2. Implement bounded-memory radial spectrum and stable two-line captions.
3. Update renderer selection and tests without changing source alignments.
4. Render and inspect a short real-audio preview; report exact adapter scope.

## Validation

Focused media/branding tests; silent/audio-changing radial frames; speaker,
line-break and gap-caption cases; final 2K preview audio/video verification;
inspect actual frames. No ASR/TTS/model call needed for the existing body clip.

## Risks And Decisions

Preserve narration and word times; subtitle styling is not an excuse to invent
alignment precision. Missing approved media fails closed. Chapter offsets must
come from actual plate durations. Do not silently claim Classic/Shorts adapters
were migrated when only dialogue body rendering changed.

## Archive Criteria

Implementation, tests, docs and inspected candidate are delivered in a scoped
PR, and adapter migration/review status is explicit.
