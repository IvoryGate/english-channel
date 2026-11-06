# Shorts Mobile Visual Refresh

## Goal

Improve phone readability, hook hierarchy and final CTA after the owner fixed
the v7 long-form treatment. Deliver a real-audio review candidate, not an upload.

## Scope

Shorts composition, safe areas, caption pacing, tests and docs. Reuse an existing
approved illustration and audio for preview only. No TTS, new image/model work,
 publication changes or long-form intro/outro. Owner now explicitly requests
 the accepted long-form spectrum unrolled into a horizontal lower audio band.

## System Boundaries

`src/shorts/`, `worker/shorts/render.py`, focused tests and Shorts docs.
Same coherent branding branch `codex/brand-motion-sound-v4`.

## Status

2026-10-18 Codex: inspected current upper caption card, oversized brand header,
bottom CTA near platform chrome and equal-duration caption pages. Implementing
a mobile editorial candidate with hook, compact brand and protected art area.
Implementation and local candidate complete; owner review pending. Reused
elr-s-207 art/audio, rendered 720x1280/30fps review only, 33.533333s with audio;
production remains 1080x1920. Inspected actual frames at 0s, 5s, 27s and 32s:
hook, compact captions, question countdown, answer and subscribe CTA. Faces
remain unobstructed. Source video/publication ledger unchanged. 59 combined
Python tests and TypeScript / encoding / architecture / docs gates passed.
Initial restricted renderer startup failed with an opaque ErrorEvent; same
local renderer succeeded with approved normal host execution. Preview uses the
already-installed headless shell; no browser/model download or account access.
An exact 2/3 preview scale is required, not a rounded decimal giving fractional
dimensions. Scoped PR integration and owner approval remain outstanding.

## Plan

1. Compact brand, safe margins, bold two-line caption hierarchy and clear CTA.
2. Preserve measured audio timeline; improve phrase-length page timing.
3. Render a real-audio candidate and representative phase stills; inspect.

## Owner Revision

V2 rejected: small left-aligned header/avatar, dark caption boxes, meaningless
progress and small low CTA. Read vibecut motion-art-direction, audiogram,
kinetic-typography and Remotion routing/reference skills. V3: enlarged centered
portrait and wordmark, centered unboxed type, full-size centered CTA, and a
horizontal audio-driven light spectrum with independent beads and particles.
No progress bar or dark backing cards. Motion language: calm-soft editorial,
350ms ease-out, 12px maximum text travel, one hero per phase; hold text still
while it is read. Offline FFT / smoothing stays bounded and deterministic.
Read the relevant skill references before implementation, inspected vibecut's
tools/research without copying its models or generated content. Existing
Remotion 4.0.504 is retained; newer skill-only interactive APIs are not assumed
to exist. Started one local Studio service and queued one app preview tab.
V3 actual-props stills at 0s/5s/32s were inspected before encoding. The first
end still revealed answer/header overlap; reduced only closing-answer type,
faded the format label during CTA, and re-inspected the corrected end still.
27 focused Shorts tests passed; TypeScript, encoding, architecture and docs
gates passed. Native 60Hz audio samples are frame-indexed in the 30fps Short,
with no random/realtime analyser or progress substitution. Full MP4 completed:
720x1280/30fps, 33.533333s, audio stream present. Inspected actual encoded
frames at 0s/5s/32s; closing answer/header collision fixed and CTA readable.
Candidate remains pending owner acceptance; published releases unchanged.

V4 spacing refinement requested by owner: reduce the overly white header to a
translucent cream gradient; move captions 60px and spectrum 70px lower, CTA
group to 53% height. Preserve all dimensions and avoid bottom-heavy stacking.
Review under workspace/branding/shorts-v4; source art/audio unchanged.
V4 stills at 0s/5s/32s completed; hook/end inspected for transparency and spacing.
Two focused layout/audio tests passed. Full 33.533333s review MP4 completed,
720x1280/30fps with audio, no source-release modification.
Owner accepted V4 on 2026-10-18. Promoted to approved future-Shorts policy and
the next week's weekly plan; no prior releases are rebuilt. PR integration
remains separate from the owner's creative approval.

## Validation

TypeScript, focused Python tests, 9:16 stream verification and actual render
inspection for hook / captions / prompt / answer / CTA.

## Risks And Decisions

Do not fake word-alignment karaoke from planned times. Keep 30fps vertical
production contract; long-form's 60fps spectrum is a separate adapter.
No generic gradient may replace the approved story illustration.

## Archive Criteria

Candidate delivered, owner review status explicit, scoped integration and
required CI/review complete before moving plan to completed.
