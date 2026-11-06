# Approved Centered Audio Editorial V4

Owner requested Shorts optimization after accepting the long-form v7 style.
Owner approved V4 on 2026-10-18 for all future Shorts, pinned in
`configs/branding/approved-shorts.json`. Previously published media stays intact.
Skills used from the owner's vibecut library:
motion-art-direction, audiogram, kinetic-typography, Remotion markup/captions.

- Retain full-screen story-specific anime art and restrained camera movement.
- Centered 208px portrait, 57px editorial serif channel name, warm cream header
  wash, and centered format/CEFR. Symmetric 100px margins; no tiny side logo.
  Header wash is translucent: alpha .78 at the top, .55 at 18%, .24 at 32%,
  transparent at 44%, preserving the illustration instead of whitening it out.
- Hook starts on frame zero; no static discovery-cover or long-form intro.
  Centered 82-86px white serif captions, restrained stroke/shadow for contrast,
  no dark backing card. Text is held still while read, not bounced per word.
- Caption pages target 42 characters, avoid orphan one-word last pages, and
  share measured turn duration in proportion to word count. These are estimates,
  not word alignment. Caption-compatible JSON carries null confidence/timestamp
  where word alignment is unavailable; no fake word-level emphasis.
- Question/answer states have clear labels; question countdown comes from actual
  reveal time. Answer never appears early. Same layout anchor across phases.
- Final single subscription CTA is centered in the actual frame, with a large
  560x132px red button, subtle press and particle burst, no backing box.
- The progress bar is removed. Lower audio visualization unrolls the accepted
  ring into a horizontal 64-column green/cyan/blue/violet light band, independent
  bead thread and outward particles. Offline PCM FFT + time-based smoothing
  at 60Hz are baked into props; global frame lookup makes out-of-order rendering
  deterministic. Silence decays, not a random animation or caption trigger.
- Shorts stay 1080x1920 / 30fps. Do not import the long-form intro/outro plates.
- Owner's spacing refinement: main caption anchor moves 60px down to y1010,
  closing answer to y710, CTA group to 53% height, audio band 70px lower with
  bottom=265. These are small shifts only; avatar, font/button sizes and motion
  remain unchanged, with visible audio elements above the lower UI zone.

Preview reuses elr-s-207's existing illustration and mastered audio only; its
canonical published files and publication ledger must not be modified.
