# Classic Listening Autonomous Operating Model

## Product Contract

Classic Listening is a continuing library of public-domain English classics for an audience led by women aged 55 and over. A book is a season, a chapter is the canonical episode, the playlist is the continuation surface, and a full-book edition is created only from locked chapter masters.

The listening experience uses one mature female narrator, source-faithful subtitles, large readable English text, restrained transitions, and eight to twelve plot-relevant scenes per typical chapter. Visuals are bright, warm, period-aware, text-free backgrounds; night scenes remain inviting rather than dark. Emoji and presentation-card layouts are not part of the format.

## Operating Loop

1. Score a candidate book and record public-domain evidence for every configured publication territory.
2. Lock the exact source edition and digest.
3. Plan the season, chapter packaging hypotheses, and production schedule.
4. Generate narration, word-aligned subtitles, scenes, motion, intro, outro, thumbnails, and upload metadata.
5. Apply rights, source, audio, subtitle, visual, media, and packaging gates.
6. Upload privately, reconcile platform processing, captions, playlist membership, and copyright checks.
7. Schedule or publish only within the configured authority level.
8. Collect analytics at 6, 24, and 72 hours and 7, 14, and 28 days.
9. Decide experiments from declared evidence rules, write retrospectives, and select the next permitted action.

## Product Units And Cadence

- Initial cadence: two chapters per week.
- Ready buffer: three complete chapters.
- Each eligible chapter receives three thumbnail candidates using warm-character, relationship-tension, and story-object archetypes.
- Native concurrent thumbnail testing is preferred. Sequential title comparisons are treated as matched-cohort evidence, not laboratory causality.
- End-screen-safe outros reserve a stable final 5-20 seconds for continuation and subscription actions.

## Lifecycle

The canonical state chain is:

`DISCOVERED -> RIGHTS_VERIFIED -> SOURCE_LOCKED -> PLANNED -> PRODUCING -> READY_TO_UPLOAD -> UPLOADED_PRIVATE -> PLATFORM_CHECKED -> SCHEDULED -> PUBLISHED -> OBSERVING -> EXPERIMENT_DECIDED -> RETROSPECTIVE_COMPLETE`

`PRODUCING -> QC_FAILED -> PRODUCING` is the repair loop. Every transition appends an immutable event with actor, time, reason, idempotency key, intent hash, and evidence. File existence never proves completion.

## Hard Release Gates

- Rights: verified status, review date, evidence links, and coverage of every configured publication territory.
- Source: exact edition, source URL, SHA-256, chapter inventory, and boilerplate exclusion.
- Audio: all acceptance cases present, ASR similarity at or above threshold, no clipping, peak within target, no detected electronic texture, and required blind-listening approval.
- Subtitles: approved source text only, actual word timing, two-line split only when necessary, and sampled sync approval.
- Visuals: scene-manifest coverage, period and character continuity, warm older-audience lighting, no accidental text or watermarks.
- Media: native 2560x1440, valid timestamps, 48 kHz delivery audio, no black interval or missing program section.
- Packaging: title, description, source attribution, playlist, thumbnail set, and next-chapter action.

Any failed or missing gate stops publication. Denoising, upsampling, or mastering cannot convert a failed narrator into an approved narrator.

## Metrics And Decisions

Snapshots store impressions, click-through rate, views, watch time, average view duration, average percentage viewed, retention curve, traffic source, playlist continuation, subscribers, and available demographic aggregates. Missing, delayed, privacy-suppressed, and zero values are distinct states.

Examples of permitted diagnoses:

- Low click-through rate with healthy retention: change packaging, not the episode format.
- Strong click-through rate with an early retention cliff: inspect title promise, intro duration, audio onset, and first subtitle cues.
- Healthy chapter retention with weak continuation: repair playlist, end screen, description, and outro action.
- Repeated audio objections: block the provider and run the acceptance set; do not scale generation.

Seven-day reviews may adjust packaging and repair obvious continuation failures. Twenty-eight-day reviews may update book scores, archetype rankings, cadence, and scene-density ranges when evidence is sufficient.

## Authority Levels

- Level 0, package only: generate and validate local upload packages; no account mutation.
- Level 1, private upload: create private videos and reconcile platform state.
- Level 2, schedule: schedule approved private videos after platform checks.
- Level 3, autonomous: publish, run bounded experiments, collect data, and plan routine next actions.

Authority is tracked policy, never inferred from credentials being present. Deletion, unlisting, rights ambiguity, account/security events, unexplained quality failures, and materially new product formats always require escalation.

## Platform References

- YouTube video upload: <https://developers.google.com/youtube/v3/docs/videos/insert>
- YouTube Analytics metrics: <https://developers.google.com/youtube/analytics/metrics>
- YouTube Analytics channel reports: <https://developers.google.com/youtube/analytics/channel_reports>
- Thumbnail Test and Compare: <https://support.google.com/youtube/answer/13861714>
- End screens: <https://support.google.com/youtube/answer/6388789>
