# ELR Motion And Sonic Identity

## Candidate V4

Warm editorial rather than trailer-like: cream paper, deep teal, copper,
existing channel avatar, restrained aperture reveal and one clear sonic hit.
Reusable principles adapted from the owner's `F:/桌面/vibecut` skills
`youtube-intro-outro`, `motion-art-direction`, `beat-sync-editing`, and the
peak-alignment method in `workdir/promo-vibecut/SOUND.md`. No third-party
skill code or samples are vendored. The local source project remains intact.

Revision 2: 150 frames at 30 fps, per owner request for more animation and a
spoken welcome. Orbit trails and small sparkles gather around the avatar,
followed by layered type. A short CPU Kokoro Heart welcome begins at frame 12:
"Hi, welcome to English Listening Room. Let's begin!" Three quiet tine notes
punctuate listen/notice/speak at frames 36/45/54. No subscription demand before
the lesson; speech takes priority over SFX. Keep the introduction within five
seconds, adjusting only if measured narration cannot fit without clipping.

Revision 3, explicitly requested by the owner: a lower-middle subscription
invitation enters at frame 72, the animated cursor presses at 112 and one
particle burst starts at 118. Phrase: "Join us. Make English a daily habit."
Keep the button labelled SUBSCRIBE (a rendered invitation, not a live action).
A quiet zero-start press tone is under the voice. Avatar caption and image
share the same local center (57 + 354/2 pixels); compensate the final glyph's
letter-spacing so the visible lettering is optically centered too.
The footer below the avatar card is also centered on the full card's center
(283 + 470/2 pixels), not on the canvas or an arbitrary left margin.

Revision 4 replaces the hand-drawn cursor with Lucide `mouse-pointer-2`.
Original upstream path is preserved in `public/branding/icons/`; only fill,
stroke color and thickness are adapted. The ISC notice and source URL ship
alongside the icon. Pointer trajectory, click, particles, voice and duration
remain unchanged. No icon-library dependency is installed for one SVG.

Outro: 600 frames at 30 fps. Entrance settles in the first second; one next
video and a subscribe target have quiet reserved space on the right. Labels
are not fake clickable buttons. `showGuides` is for layout review only. Real
end-screen elements must be positioned separately in Studio. Their permissible
window is the final 5-20 seconds, not a mandatory 20-second outro.
Shorts must not receive this 20-second plate.

Outro revision 3 matches the approved intro: one subscribe press and particle
burst, using the same Lucide cursor, appears on the left below the thank-you.
Kokoro Heart speaks a brief thank-you, subscribe invitation and next-listen
prompt. Music stays below that voice, then settles into a quiet end-screen
hold. Right-side video/circle overlay zones remain clear; no repeated cursor,
flashes or particle loops compete with choosing the next video.

## Audio And Rights

`scripts/build_brand_audio.py` synthesizes stereo air, a soft impact, pitched
tines and a low-level harmonic bed from deterministic oscillators/noise.
There are no sampled tracks or cloned voices. The welcome uses the existing
pinned local Kokoro model on CPU, without weight copying or downloading. PCM
WAVs and a trace include settings, event frames, hashes, peak and final-tail
RMS. Audio and visuals share `configs/branding/motion-v4.json` for timing.
The light ambient outro decays toward the end; no loud logo boom or ongoing
music is added beneath the actual English lesson.

The first version had no clipping but its cosine impact jumped from zero to
0.50116 full scale at 0.8 seconds, producing a click. Revision 2 removes that
impact, gives the reveal chime an 18ms zero-start attack, softens the noise
sweep and tests sample discontinuities as well as peaks. Never use a peak-only
check to declare that a listener-reported sound defect is absent.

The inspected MusicGen model is not selected because its weights are
CC-BY-NC-4.0: <https://huggingface.co/facebook/musicgen-stereo-small>.
Existing vibecut SFX are not copied without per-asset rights evidence.
Native end-screen reference: <https://support.google.com/youtube/answer/6388789>.

## Reproduce And Review

1. `.conda-env/python.exe scripts/build_brand_audio.py`
2. `npx remotion still src/brand/index.ts EnglishListeningRoomIntroV4 workspace/branding/v4/intro-impact.png --frame=24`
3. `npx remotion still src/brand/index.ts EnglishListeningRoomIntroV4 workspace/branding/v4/intro-hold.png --frame=70`
4. `npx remotion still src/brand/index.ts EnglishListeningRoomOutroV4 workspace/branding/v4/outro-hold.png --frame=90`
5. Render these compositions to `workspace/branding/v4/intro.mp4` and `outro.mp4`.

Inspect actual exported files, not only source. Verify audio streams and
duration; check logo, mobile-readable text, safe margins and the sound landing
on the reveal. Loudness/peak checks do not substitute for owner listening.
No retention or CTR win is claimed before matched release evidence exists.

## Deployment Boundary

Current owner decision supersedes earlier native end-screen variants: use a
complete thank-you / subscribe outro, with no empty avatar/video zones and no
"choose your next listen" text or narration. Duration is eight seconds, not
twenty. Intro-matched portrait card on the left, thank-you and one subscribe
invitation on the right. One cursor press/burst, then a short hold and fade.
No Studio end-screen setup is required for the rendered design to look finished.

Owner approved intro-r4 and outro-complete on 2026-10-18. Their canonical
paths/hashes are pinned in `configs/branding/approved-longform.json`. They are
the default for all future non-Shorts: dialogue, lessons, flagship long videos
and novels. Persuasion chapter 12 onward and other future books use shared
plates plus the approved body-v7 style.
Chapter offsets derive from actual duration. Chapters 1-11, existing released
videos and Shorts are unchanged. See `BODY_VISUAL_STYLE.md` for adapter scope.
