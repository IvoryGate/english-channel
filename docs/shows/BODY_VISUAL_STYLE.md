# Body Visual Style And Approved Plates

Owner approved the five-second intro-r4 and eight-second outro-complete on
2026-10-18. `configs/branding/approved-longform.json` references those canonical
workspace files; do not copy them into a second archive. Dialogue composition
uses them by default. Persuasion chapter 12 onward selects the same plates;
chapters 1-11 retain original files and caption offsets. Classic concatenation
normalizes all inputs to 2560x1440. Shared files are never render targets, even
with `force`. No chapter-specific brand TTS is generated for shared plates.

## Approved Non-Shorts Standard

Owner approved body-v7 on 2026-10-18 for ALL future non-Shorts: dialogue,
ten-minute lessons, forty-minute flagship videos and novels. The policy is
`configs/branding/approved-longform.json`; the following geometry/motion is
the default, not a candidate. No future series silently falls back to old art.

- 96 short radial light pulses, mirrored frequency distribution, driven by real
  audio FFT and absolute RMS. Silence settles toward minimum bars; it does not
  trigger fake music animation. Existing avatar in the center.
- Owner revision: 800x800 transparent overlay at (880,90) in the 2560x1440
  layout. Following the owner's three reference frames, a connected colored
  ring carries dense 6px pulses, restrained glow and small peak dots. Extension
  is capped near 42px, preserving short pulses rather than long rays.
  The central avatar is 360px across. A 70ms audio window and nonlinear
  peak emphasis preserve local variation instead of boosting every bar at once;
  silence decays without fake motion. Owner then explicitly requested color:
  green at the top transitions through cyan and blue to violet at the bottom,
  with matching colored bloom. Keep the existing background, not the starfield.
- Inner beads follow independent inward deformation (up to 30px). Rising local
  spectral peaks emit independent particles from bar tips: outward velocity,
  0.6s lifetime, fading and shrinking, with per-band cooldown. Particles keep
  flying after the source bar drops; no fixed dots pretending to be emission.

- The inner thread is 2px with 6.4px beads. Bar roots remain fixed at radius
  248px. The thread has its own fast attack / slower release, visibly separating
  from the columns without crossing the avatar. Outward particles launch from
  the fixed-root column tips and are slightly larger than in the prior preview.
- Stable phrase cards: up to ten words / 76 characters, at most two manually
  balanced lines, punctuation and long pauses as phrase boundaries. White text,
  warm-gold current word, translucent dark rounded plate and speaker label.
- Source narration, aligned word timestamps and downloadable SRT are unchanged.
  Do not claim word timing is more accurate merely because the visual changed.
  Existing alignment may itself be script-timed.

`media/radial_waveform.py` streams 70ms audio windows with constant-size frame
buffers rather than loading a whole 40-minute episode into memory.
Owner revised delivery to native30fps on2026-10-19 for production throughput;
dialogue and both Classic adapters normalize output to30fps. The approved
geometry, colors and motion remain. Neighboring bands blend lightly; critically damped,
time-based position/velocity smoothing replaces abrupt per-frame catch-up for
both columns and the independent inner thread. Particle birth fades in over
65ms, then continues outward and fades out. Geometry, color and 30px maximum
thread displacement are unchanged. Peak emission uses velocity per second so
frame-rate changes do not suppress accents. Do not use abrupt frame-based
catch-up or duplicate frames to claim higher fidelity.
The renderer caches immutable antialiased core artwork, palette, band geometry
and the prepared avatar. Dynamic lights supersample only one-channel alpha,
then apply the shared color palette at output resolution. Do not redraw and
downsample supersampled RGBA artwork every frame. Motion itself remains driven
by this video's real audio, not a looped prerecorded animation.
After a real libx264 allocation failure in the first 2K preview, the compositor
uses two encoder threads and one filter-complex thread. The explicit
`waveform_mov` argument now means reuse that existing pre-rendered overlay;
without it, production builds the radial overlay from the current audio.

## Preview And Boundary

Production overlays checkpoint verified30-second lossless chunks inside the
canonical episode workspace. Each chunk stores exact bar/thread velocity,
particle state and numeric precision. Resume restores that state rather than
resetting motion or repeating completed chunks. Input audio, avatar, geometry,
FPS and renderer/engine hashes must match. Completed overlays are reused only
after frame/geometry/codec and checksum verification. Chunk media are removed
only after the canonical overlay is verified. Progress is emitted every15seconds
and after each committed chunk, with no per-frame chat output. The approved
geometry/colors and dynamics are unchanged; delivery is now30fps. No second finished video is
exported to H:\Youtube.

Run `.conda-env/python.exe scripts/preview_body_refresh.py --seconds 16` for an
isolated real-audio excerpt from series_a episode_039. Outputs stay in
`workspace/branding/body-v7/`; no source episode is overwritten. The preview
uses the actual production renderer at 2K, not a separate mockup.

Dialogue and both Classic body adapters use the approved visuals. Multi-scene
novels retain their scene transitions, source text and original downloadable
SRT. Cue-only sources use the same phrase-card layout without invented word
highlight timing. Existing Persuasion chapters1-11 retain their old output;
other future books default to shared plates and style from chapter1. Existing
rendered/published content is not rebuilt just to change the style.
Shorts have their own mobile style. Native end-screen configuration is not required for the
approved complete outro. Existing final videos are never retroactively rebuilt.
