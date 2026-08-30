# Shorts Visual Research And Quality Method

## Audience And Objective

Shorts visuals are designed first for women aged 25-44 in the United States.
The objective is not to copy a competitor's artwork. It is to learn which
visual promises earn attention in the English-learning category, then create
original, channel-owned images with stronger clarity, warmth, and emotional
specificity.

## Required Research Before Each Cycle

Before briefs or images are approved, capture at least 30 public thumbnails
from relevant high-view cohorts. Use public YouTube metadata and thumbnail
images only; do not download or redistribute competitor video or audio. The
sample must include:

- direct English-listening and conversational-English competitors;
- adjacent learning, self-improvement, and women-led educational channels;
- recent high performers and durable evergreen high performers;
- both long-form and Shorts surfaces when their visual grammar differs.

Record channel, video URL/ID, publish date, views, age in days, views per day,
format, topic, and thumbnail source URL. Separate genuinely high-view examples
from merely old examples by ranking both total views and age-normalized views.
Store the immutable capture under `workspace/shorts/research/` and summarize
the findings in a tracked brief under `docs/shorts/research/` when they change
the production method.

The cycle portfolio must name the research artifact, sample size, target
market, primary audience, and confirm that a high-view cohort was reviewed.
Production cannot start without that evidence.

## What To Analyze

For each thumbnail, code observable properties rather than subjective praise:

- dominant subject and apparent gender/age;
- face count, face size, gaze, expression, and emotional tension;
- brightness, saturation, dominant hue, contrast, and background complexity;
- headline word count, hierarchy, font personality, outline, shadow, tilt, and
  placement;
- promise type: result, mistake, question, conflict, transformation, or story;
- mobile legibility at approximately 10% of source size;
- continuity with the first video frame and topic;
- likely audience signal, including whether it feels welcoming to US women
  aged 25-44;
- repeated archetypes and outliers worth testing.

Do not infer causality from a thumbnail alone. Views are affected by topic,
channel size, timing, and distribution. Research produces visual hypotheses,
not permission to reproduce another creator's composition or wording.

## Channel Visual Direction

The default Shorts direction is bright, high-quality anime illustration with
adult characters, expressive faces, lively but controlled color, and playful
flexible typography. Prefer warm coral, teal, sky blue, violet, cream, and
sunshine accents. Avoid muddy brown grading, generic dark podcast rooms,
technology gradients, stock-photo realism, or child-oriented classroom art.

The primary woman in a scene should have agency and a readable learning moment;
she should not be decorative background. American settings and props should
feel contemporary and plausible without relying on stereotypes. Other genders
remain welcome, but the visual must pass a first-person test for the primary
audience rather than defaulting to a generic male learner.

## Per-Short Originality Gates

Every Short in a cycle requires its own generated story background. Reusing
one background with different captions is prohibited. Renaming or lightly
cropping the same image does not make it original. The portfolio contract
allows one use per background path, and review must also reject near-duplicate
composition, character pose, lighting, or palette.

Each image must differ in at least three meaningful dimensions: setting,
character action/expression, camera framing, palette, visual metaphor, or time
of day. A connected weekly theme may share character design and brand colors;
it may not share the same staged scene.

## Automated And Human Gates

Automated packaging checks require:

- one unique background path per cycle;
- average luma of at least 125 on FFmpeg's 0-255 signal scale;
- average saturation of at least 22 on the same signal-statistics scale;
- the configured US market and women 25-44 audience signal in the manifest;
- a dedicated vertical thumbnail and all existing dimension/media checks.

These thresholds prevent obviously dark or muted batches; they do not replace
visual judgment. Before upload, review a contact sheet of the full cycle at
phone size. Reject any asset with repeated staging, weak emotion, illegible
text, accidental artifacts, incorrect anatomy, dark faces, or a mismatch
between the hook and the image.

## Release Rule

Visual gates are blocking. Schedule pressure, GPU availability, or completed
audio does not justify an exception. If a visual fails, keep the item private,
regenerate only the affected asset, rerun the cycle contact-sheet review, and
preserve the failed attempt for traceability. The already-uploaded
`weekly-2026-08-31` cycle has a single named legacy exception; it does not
apply to any later cycle.
