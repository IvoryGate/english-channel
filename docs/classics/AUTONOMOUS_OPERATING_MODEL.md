# Classic Listening Autonomous Operating Model

## Product Charter

Classic Listening turns verified public-domain English books into warm, legible, chapter-based listening experiences for the English Listening Room audience. The primary audience is women aged 55 and over. The product promise is simple: faithful classic literature, a calm single narrator, readable synchronized English text, welcoming period imagery, and an obvious path into the next chapter.

The series is a continuing library, not a collection of unrelated one-off videos. A book is a season, a chapter is the canonical episode, the book playlist is the primary continuation surface, and a full-book compilation is a later derivative product after every chapter passes publication QC.

The operating goal is for an agent to maintain the series end to end: select eligible books, plan a season, produce chapters, verify and publish them, run controlled packaging experiments, collect performance data, write a retrospective, and choose the next action. External account authorization and explicit policy boundaries remain prerequisites for public publishing.

## Audience And Experience Principles

1. Design first for women aged 55 and over without excluding other listeners.
2. Favor brightness, warmth, emotional reassurance, familiar domestic detail, large serif typography, and stable reading time.
3. Night scenes remain honey-lit and inviting. Avoid murky black frames, horror lighting, tiny type, rapid motion, visual clutter, and emoji.
4. Use one mature female narrator for the book unless a future product decision explicitly creates a dramatized edition.
5. Subtitles reproduce the approved source text and follow the real speech. They are not summaries, vocabulary cards, or decorative captions.
6. Visuals support comprehension and emotional continuity. They must not compete with the narration or imply that the product is a film adaptation.
7. The chapter must be satisfying on its own while the playlist, end screen, description, and outro make continuation effortless.

## Canonical Product Units

### Chapter episode

- One complete source chapter.
- Expected duration normally 12-35 minutes; unusually long chapters may be split only at an edition-supported section boundary.
- One spoken intro, full narration, and a 5-20 second end-screen-safe outro.
- Word-aligned English subtitles.
- Eight to twelve plot-relevant scene beats for a typical 20-minute chapter, adjusted by narrative density rather than a fixed timer.
- Three thumbnail candidates and one publish title selected from a controlled packaging matrix.

### Book playlist

- Chapters ordered strictly by source order.
- Consistent title and thumbnail grammar across the season.
- Description identifies the edition, public-domain basis, narrator, and listening order.
- New chapters are added immediately after scheduling or publication.

### Full-book compilation

- Produced only after all chapters are published and their final masters are locked.
- Reuses chapter masters; it never introduces a second untraceable narration render.
- Uses chapter markers, a distinct full-book cover, and its own packaging experiment.
- Does not replace or unlist chapter episodes.

## Book Selection Portfolio

Every candidate receives a recorded score before resources are downloaded or generated.

| Dimension | Weight | Evidence |
| --- | ---: | --- |
| Rights certainty | Gate | Edition, author dates, publication year, source provider, jurisdiction note, SHA-256 |
| Audience fit | 25 | Emotional warmth, female readership, domestic or relationship themes, accessibility |
| Demand | 20 | Channel search terms, YouTube search demand, related-video traffic, prior book performance |
| Continuation potential | 15 | Chapter hooks, serial momentum, playlist suitability |
| Narrator fit | 15 | Natural match with the approved voice and delivery style |
| Visual richness | 10 | Distinct locations, characters, objects, and emotionally legible scenes |
| Production feasibility | 10 | Chapter count, chapter length, pronunciation risk, source cleanliness |
| Portfolio differentiation | 5 | Adds a new theme or era without confusing the channel promise |

Rights certainty is binary. A candidate with uncertain rights cannot be rescued by a high commercial score. Project Gutenberg status supports source selection but does not replace the stored jurisdiction and edition record.

Run one principal book at a time until the release process holds a three-chapter ready buffer. Start a second book only when the first book's production reliability and continuation data are stable.

## Season And Release Design

The initial operating cadence is two chapter episodes per week with at least three verified episodes held in reserve. The cadence may change only from observed production capacity and audience behavior.

Use the following checkpoints:

- Before launch: three approved chapters and a complete book playlist shell.
- Early season: chapters 1-3 establish the voice, cover grammar, scene density, and publish-time baseline.
- Mid-season: one packaging variable may change at a time; narrative production rules stay stable.
- Final third: prepare the full-book compilation and next-book rights shortlist without interrupting the current schedule.
- Season close: publish the compilation, complete the book retrospective, and select the next book from the scored backlog.

Publish time is not permanently hard-coded. Begin with a consistent slot, then choose the slot from the target audience's actual active-time and first-24-hour data. Do not alternate times while a packaging test is running.

## End-To-End State Machine

```text
DISCOVERED
  -> RIGHTS_VERIFIED
  -> SOURCE_REGISTERED
  -> BOOK_PLANNED
  -> CHAPTER_READY
  -> AUDIO_RENDERING
  -> AUDIO_REVIEW
  -> VISUAL_RENDERING
  -> PACKAGE_VERIFYING
  -> READY_TO_UPLOAD
  -> UPLOADED_PRIVATE
  -> PLATFORM_CHECKS
  -> SCHEDULED
  -> PUBLISHED
  -> OBSERVING
  -> EXPERIMENT_DECIDED
  -> RETROSPECTIVE_COMPLETE
```

Every transition records the actor, timestamp, input fingerprints, outputs, checks, warnings, and next allowed actions. A failed gate transitions to `BLOCKED_<PHASE>` with a repair recommendation. File existence alone never advances state.

## Production Contract

### 1. Rights and source

- Register a stable book slug, exact edition, source URL, provider identifier, author dates, publication year, language, local file, MIME type, and SHA-256.
- Parse the EPUB spine and exclude navigation, front matter not meant for narration, and provider boilerplate.
- Preserve exact display text and trace every spoken-text pronunciation substitution.
- Reject source changes until the new fingerprint and edition record are reviewed.

### 2. Chapter planning

- Create semantic narration segments with complete ordered source coverage.
- Create a scene map from narrative beats, not arbitrary equal durations.
- Identify names, dates, archaic spellings, quotations, and fragile short lines before GPU work.
- Generate title hypotheses, thumbnail concepts, and description copy from the same approved chapter summary.

### 3. Audio

- Route every synthesis engine through a provider boundary and persist model, version, voice, reference, prompt, settings, seed where supported, and artifact hashes.
- Render resumable per-segment audio serially on the GPU.
- Never use mastering or denoising to hide a synthesis defect.
- Treat content errors, electronic/vocoder texture, unstable pronunciation, clipped words, and voice drift as generation failures.
- Compose and master only after every expected segment exists and strict QC passes.

The current VoxCPM2 checkpoint encodes reference audio at 16 kHz and produces output at 48 kHz. A higher-rate Riley file cannot change that encoder limit. The `Persuasion` rollout remains blocked until a voice path passes blind listening without the speech-coupled 7.5-8.8 kHz artifact. The durable solution should be a better synthesis provider/model or a demonstrably clean setting, not stronger broadband post-processing.

### 4. Subtitles

- Align actual generated speech at word level.
- Keep a complete source segment in one cue when it fits the two-line safe area.
- Split only at punctuation or semantic boundaries when the source is too long.
- Burned captions use body time; YouTube captions add the measured intro offset.
- Reject negative time, overlap, unreadably short holds, source mismatch, or excessive line length.

### 5. Visuals

- Generate text-free story images in bounded parallel waves.
- Maintain period accuracy, character continuity, warm older-audience lighting, subtitle-safe framing, and furnished middle/lower thirds.
- Use restrained 2-4 percent camera movement and sentence-boundary crossfades.
- Compose the avatar, logo, required text, and typography deterministically; do not ask image generation to spell required copy.
- Preserve a scene manifest containing segment range, prompt, generator, source path, review result, and hash.

### 6. Assembly and package

- Assemble `intro -> body -> outro` on a reset, verified timestamp timeline.
- Produce native 2560x1440 H.264 video with 48 kHz AAC, a 2560x1440 thumbnail, SRT, title, description, tags, timestamps, experiment variants, and verification report.
- Scan for black frames, audio/video drift, corrupt timestamps, missing scenes, subtitle clipping, and end-screen conflicts.
- Promote an `.incomplete` package atomically only after all checks pass.

## Quality Gates

### Binary release gates

- Rights and edition record complete.
- Exact source coverage and hashes pass.
- No missing, extra, stale, or orphaned narration segment.
- ASR/content checks pass or have a recorded accepted pronunciation exception.
- Voice has no unresolved electronic texture, clipping, missing word, or identity drift.
- Master loudness and peak targets pass.
- Subtitle sync sampling and full structural validation pass.
- All scenes pass content, period, anatomy, text, and watermark review.
- Final video is native 2K and contains valid continuous audio/video streams.
- Metadata, timestamps, playlist target, and next-chapter destination are valid.
- Platform copyright/check status is clear before public scheduling.

### Quality scorecards

Automated scores are diagnostic, not substitutes for binary gates. Store separate scores for source fidelity, audio texture, content recovery, subtitle timing, visual consistency, packaging completeness, and media integrity. A high aggregate score cannot override a failed audio or rights gate.

## Packaging System

Each chapter receives candidates from controlled, reusable archetypes.

### Thumbnail archetypes

1. **Warm character** — Anne or another central woman in a bright domestic setting with a clear emotional expression.
2. **Relationship tension** — two or three characters with readable distance, disagreement, departure, or recognition.
3. **Story object** — a letter, family book, carriage, estate, flowers, tea setting, or other chapter-specific object with a strong human context.

All candidates retain the same book identity, chapter number, high-contrast serif hierarchy, and older-viewer legibility. The experiment changes the hook, not the brand system.

### Title grammar

- Lead with book and chapter identity for search continuity.
- Add one truthful chapter hook.
- End with author or full-audiobook context only when the 100-character limit permits.
- Never change title and thumbnail simultaneously in a test intended to attribute cause.

### Description and continuation

- First two lines: calm benefit statement and chapter-specific premise.
- Then timestamps, book/source record, playlist link, next-chapter link when available, subscription cue, and restrained hashtags.
- The last 5-20 seconds remain visually stable for YouTube end-screen elements. YouTube currently permits up to four end-screen elements on standard 16:9 videos.

## Experiment System

Every experiment has a durable record:

```text
experimentId
videoId
hypothesis
single changed variable
control and variants
audience and eligibility
start and planned end
primary metric
guardrail metrics
minimum evidence rule
platform result
agent interpretation
decision
reusable learning
```

### Thumbnail tests

Use YouTube Studio's native Test & Compare for up to three thumbnails. It is a concurrent test and chooses results from watch-time share rather than click-through rate alone. Results may take several days or up to two weeks. Accept YouTube's `Winner`, record `Preferred` as directional evidence, and record `None` or insufficient impressions without forcing a winner.

The public YouTube APIs do not currently expose the full native thumbnail experiment workflow. Until a verified Studio automation is reliable, starting the test and reading its platform result remain a permissioned browser action with screenshots and an audit record.

### Title tests

YouTube does not provide an equivalent concurrent native title test. Do not alternate titles sequentially and call the result causal. Test title grammar across randomized or matched chapter cohorts while holding thumbnail archetype, publish slot, book stage, and duration as stable as practical.

### Content tests

Do not upload duplicate full chapters solely to test intro, pacing, or subtitle styles. Use pre-publication listening panels for audio, then test one production policy across matched future chapters. Examples include scene density, intro length, and subtitle size. Protect source fidelity and voice identity as non-experimental constants.

### Decision windows

- 6 hours: ingestion and platform-health check only.
- 24 hours: early anomaly detection; no strategic winner.
- 72 hours: early packaging and retention diagnosis.
- 7 days: operational decision if evidence is sufficient.
- 14 days: native thumbnail result or formal inconclusive result.
- 28 days: long-tail search, playlist, and demographic retrospective.

Use rolling channel and book-stage baselines rather than generic industry benchmarks. Small samples produce `INSUFFICIENT_EVIDENCE`, not optimistic conclusions.

## Analytics Contract

Collect immutable snapshots and derived reports at the decision windows. The YouTube Analytics and Reporting APIs support targeted queries and bulk reports; the Data API supplies video, playlist, and publication state.

### Reach

- Thumbnail impressions and impressions click-through rate.
- Traffic source and search terms where available.
- Browse, suggested, search, playlist, notification, external, and end-screen contribution.

### Consumption

- Views and engaged views.
- Estimated minutes watched.
- Average view duration and average view percentage.
- `audienceWatchRatio` and `relativeRetentionPerformance` by `elapsedVideoTimeRatio`.
- Retention at intro end, 30 seconds, 25 percent, 50 percent, 75 percent, outro entry, and final frame.

### Continuation

- Playlist starts, playlist views, views per playlist start, and playlist watch time.
- End-screen impressions, clicks, and click rate where the authorized report exposes them.
- Next-chapter views attributed to end screen, playlist, related video, and description links.

### Audience and growth

- Subscribers gained and lost per video.
- Likes, comments, and shares as secondary signals.
- Age-group and gender distribution when privacy thresholds allow reporting.
- Female 55-64 and 65+ watch share as a product-fit diagnostic, never as an exclusion rule.

### Derived diagnosis

| Pattern | Likely issue | Default response |
| --- | --- | --- |
| Low CTR, healthy retention | Packaging | Run or revise thumbnail hypothesis |
| Healthy CTR, sharp intro drop | Promise mismatch, intro, or audio | Inspect first 30 seconds and comments; hold next publish if audio-related |
| Stable intro, body cliffs | Scene pacing, chapter structure, or playback defect | Map retention cliffs to exact program time and production trace |
| Healthy completion, weak continuation | Outro, end screen, playlist, or schedule gap | Repair continuation surfaces |
| Strong search, weak suggested traffic | Metadata/series linkage | Strengthen playlist and related-video graph |
| Strong broad metrics, weak target demographic | Product positioning | Test warmer packaging without changing the book text |

## Retrospective And Next-Action Engine

After each 7-day and 28-day window, generate a short evidence-backed decision record:

1. What happened relative to the correct baseline?
2. Which hypothesis was tested?
3. Was the evidence sufficient?
4. What can be attributed to the changed variable?
5. Which production or packaging rule changes?
6. What remains uncertain?
7. What is the next single experiment?

The decision engine may autonomously:

- Promote a native thumbnail `Winner`.
- Keep the control when the result is `None`.
- Create the next thumbnail variants from an approved archetype.
- Adjust scene-density targets within an approved range.
- Adjust release time after enough matched observations.
- Prioritize repair work when retention cliffs map to technical defects.
- Select the next chapter and maintain the production buffer.
- Rank the next public-domain book shortlist.

It may not autonomously weaken a quality gate, reinterpret uncertain rights, change the established narrator identity, delete or unlist published videos, respond publicly to sensitive comments, or make a new public account connection.

## Publishing Authority Model

### Level 0 — package only

The agent produces and verifies upload packages. A human uploads and publishes.

### Level 1 — private upload

With OAuth authorization, the agent uploads privately, adds metadata, captions, and playlist membership, then waits for platform checks and human approval.

### Level 2 — scheduled release

After a stable run of approved uploads, the agent may schedule videos inside a pre-approved cadence and content policy. Copyright claims, failed checks, missing end screens, or quality warnings stop the transition.

### Level 3 — autonomous series operation

The agent selects from the rights-verified backlog, maintains the ready buffer, schedules chapters, runs approved experiments, collects analytics, and writes retrospectives. It sends exceptions rather than routine approvals to the user.

Public upload automation requires a configured YouTube OAuth connection. Unverified API projects created after July 2020 may be restricted to private uploads until Google's compliance audit is completed. Native thumbnail tests and some Studio-only elements may still require permissioned browser automation even after API upload is available.

## Fail-Closed Rules

Stop publication when any of the following occurs:

- Rights or edition ambiguity.
- Source hash drift.
- Missing text, ASR content anomaly, or subtitle mismatch.
- Audible synthesis artifact or voice identity drift.
- Broken timestamp, black-frame, resolution, or media-stream check.
- Thumbnail text error, malformed image, misleading hook, or policy concern.
- Platform copyright claim or failed upload check.
- Analytics data is missing while an automated decision depends on it.
- An experiment changes more than one causal variable.
- A requested external action exceeds the currently granted publishing authority.

## Operating Cadence

### Per chapter

1. Prepare source, segment plan, scene map, and packaging hypotheses.
2. Render audio and visuals with resume-safe parallelism where appropriate.
3. Complete strict QC and package verification.
4. Upload privately, wait for checks, attach captions, playlist, and continuation elements.
5. Schedule or publish within the approved slot.
6. Start one eligible experiment.
7. Collect 6-hour, 24-hour, 72-hour, 7-day, 14-day, and 28-day snapshots.
8. Apply the recorded decision to the next eligible chapter.

### Weekly

- Verify the three-chapter production buffer.
- Review blocked quality items and platform exceptions.
- Compare book-level reach, consumption, continuation, and target-audience fit.
- Permit no more than one new causal production-policy experiment at a time.

### Monthly or season close

- Review narrator quality and complaint signals.
- Refresh the rights-verified book backlog and demand evidence.
- Reassess release cadence and playlist architecture.
- Consolidate durable learnings into the product configuration.
- Select the next book only after the current season's evidence is recorded.

## Required System Components

Implement external dependencies behind providers and preserve the repository layering `types -> schema -> repo -> service -> transport`.

- **Catalog and rights service** — book candidates, editions, rights evidence, source fingerprints, scoring.
- **Production orchestrator** — state machine, leases, heartbeats, retries, fingerprints, GPU serialization, repair queue.
- **Quality service** — source, audio, ASR, subtitle, visual, media, and package gates.
- **Packaging service** — metadata, three thumbnail variants, playlists, captions, end-screen plan.
- **YouTube provider** — private upload, metadata, captions, playlists, schedule, status, and IDs.
- **Studio interaction provider** — audited browser-only actions such as native thumbnail tests and end-screen setup when no supported API exists.
- **Analytics provider** — immutable API snapshots, retention curves, demographics, traffic sources, and playlist reports.
- **Experiment service** — hypotheses, assignment, evidence windows, results, and promotion decisions.
- **Retrospective service** — evidence-backed diagnosis and next-action proposal.
- **Policy engine** — authority level, stop conditions, schedules, experiment limits, and notification rules.

Expected tracked configuration lives under `configs/classics/`. Runtime media, OAuth tokens, analytics snapshots, and generated reports remain outside version control. Credentials must use the established secret mechanism and never appear in manifests or logs.

## Official Platform References

- [YouTube native thumbnail Test & Compare](https://support.google.com/youtube/answer/13861714)
- [YouTube Data API video upload](https://developers.google.com/youtube/v3/docs/videos/insert)
- [YouTube Analytics metrics](https://developers.google.com/youtube/analytics/metrics)
- [YouTube Analytics dimensions](https://developers.google.com/youtube/analytics/dimensions)
- [YouTube Analytics channel reports and retention](https://developers.google.com/youtube/analytics/channel_reports)
- [YouTube end-screen rules](https://support.google.com/youtube/answer/6388789)

