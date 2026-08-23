# English Listening Room Autonomous Growth System

## Purpose

This document defines the product and operating system required for an agent to
maintain the English Listening Room dialogue portfolio end to end: research,
product planning, scripting, production, publication, experiments, analytics,
review, and the next planning cycle.

The objective is not maximum video output. It is maximum validated audience
learning per unit of production effort, while preserving quality, provenance,
platform safety, and user control over high-impact channel decisions.

## Current Baseline And Diagnosis

As of 2026-08-17, the local repository contains 21 completed episode workspaces
for each of Series A, B, and C: 63 dialogue videos in total. The production
system can validate scripts, generate visual assets, render resumable audio,
master, subtitle, compose, package, and verify a 2K video.

The signed-in YouTube Studio baseline now covers the channel and all three
dialogue podcasts. See
[`YOUTUBE_BASELINE_2026-08-17.md`](YOUTUBE_BASELINE_2026-08-17.md) for the
evidence and video-level diagnosis. In the 28 days ending 2026-08-16, the
channel received 2,618 views, 93.9 watch hours, and 58 subscribers from 80,547
impressions at 2.6% CTR. The dialogue portfolio contributed 1,647 views, 65.4
watch hours, and 41 subscribers.

YouTube contains 19 videos in each dialogue podcast playlist. Episodes 020 and
021 remain local and unpublished. The 2026-08-17 episode 019 batch also exposed
a publication identity failure: Polished English 019 was uploaded with the
correct-duration media but First Steps 019 title and description, producing two
public videos with the same `Fast English...` metadata.

The growth loop is incomplete:

- There is no publication ledger that maps an episode to a YouTube video ID,
  URL, publish time, playlist, privacy state, or experiment assignment.
- Studio can be read through the authorized signed-in browser, but there is no
  durable authenticated ingestion, immutable snapshot store, or scheduled sync.
- Impressions, CTR, retention, and subscriber conversion have been observed
  once but are not yet stored locally or reproducibly joined to episode IDs.
- Topic backlog state is not reconciled with the artifact inventory; each
  series has 21 completed episode videos, while only 15 topics are marked done.
- Search contributes only 3.1% of views; Suggested and Browse contribute 86.0%.
  The earlier search-led acquisition assumption is therefore rejected for the
  next cycle.
- First Steps is the measured reach leader; Daily Talk is the measured
  satisfaction leader; Polished English is a low-volume authority/conversion
  bet.
- Publication has no idempotent fingerprint gate, allowing metadata and media
  from different canonical episodes to be combined.
- Production can run autonomously, but publication and post-publication
  decisions cannot yet be audited or reproduced.

Therefore, do not produce episode 022 or later merely to maintain cadence. The
existing inventory is the experiment bank until the baseline is reconciled and
the first measured learning cycle is complete.

## Product Architecture

### Channel promise

**English for a real moment, with one line the learner can use today.**

Every dialogue episode must satisfy one job to be done and one observable
learner outcome. “Improve English”, “sound natural”, and “build confidence” are
not acceptable episode outcomes by themselves.

### Portfolio roles

| Series | Product role | Primary discovery mode | Default episode promise |
| --- | --- | --- | --- |
| B · First Steps · A2-B1 | Reach | Suggested and Browse; Search is secondary | Complete one common interaction without freezing |
| A · Daily Talk · B1-B2 | Satisfaction and core habit | Suggested, Browse, and future returning viewers | Handle one emotionally awkward everyday moment |
| C · Polished English · B2-C1 | Authority and conversion | Suggested niche clusters and future returning viewers | Navigate one nuanced social or workplace tension |

These roles are based on the 2026-08-17 baseline and remain provisional until a
complete 28-day measured release cycle supplies returning-viewer data. Classic
Listening is a separate product line and must not be included in dialogue-series
experiments unless the experiment explicitly tests cross-format audience overlap.

### Episode product contract

An episode is publishable only when it has:

1. One named audience moment.
2. One checkable spoken outcome.
3. A title and thumbnail that promise the same moment as the first 30 seconds.
4. A useful line within the first 45 seconds of programme content.
5. A first application or rehearsal within 90 seconds.
6. At least one changed-pressure example, not repeated explanation alone.
7. A concise recap and one next action.
8. Verified MP4, mastered WAV, subtitles, metadata, provenance, and QC reports.
9. An experiment assignment or an explicit `control` designation.

## Release Strategy

### Baseline sprint

For the first two-week validation sprint:

- Publish three dialogue videos per week, never as a same-day batch.
- Keep at least 48 hours between channel uploads and seven days between two
  releases from the same series.
- Use one slot per series each week so all three product roles receive two
  comparable observations while the existing 020/021 bank is released.
- Schedule at 20:00 Asia/Shanghai until Studio has enough audience-online data
  to justify an hour change. Treat the hour as a controlled hypothesis.
- Use the versioned six-slot plan in
  `configs/channel_ops/release-plan-2026-08-18.json`: First Steps, Daily Talk,
  Polished English, then repeat the same order in week two.
- Keep at least seven days between videos assigned to the same cohort test when
  audience overlap would confound the comparison.

This cadence is a learning constraint, not a permanent editorial calendar.

### Publication state machine

```text
planned -> reserved -> scripted -> produced -> publish_ready
  -> uploaded_private -> validated_on_platform -> scheduled -> published
  -> measuring -> reviewed -> keep | repackage | follow_up | retire
```

Every transition records actor, timestamp, input fingerprint, output IDs, and
reason. File existence is never treated as proof of publication.

### Publication safety

- The canonical episode workspace is the media source of truth. Do not create a
  duplicate `H:\Youtube` package unless explicitly requested.
- Before any upload, bind the canonical series and episode to fingerprints for
  the MP4, thumbnail, subtitles, title, and description. Reject cross-series
  CEFR/title mismatches and duplicate titles with different media fingerprints.
- The same artifact fingerprint must resolve idempotently to one remote video
  ID. A retry must never create a second public upload.
- The first automated uploader must upload as private, attach metadata,
  thumbnail, subtitles, playlist, and disclosure fields, then verify processing.
- Public scheduling is enabled only after a one-time user-approved channel
  policy defines allowed weekdays, time windows, maximum cadence, playlists,
  and privacy defaults.
- Deletion, copyright disputes, policy appeals, monetization changes, channel
  renaming, credential changes, and uploads outside the approved policy always
  require the user.
- Credentials and refresh tokens never enter the repository or logs.

## Measurement Model

### North-star metric

**Qualified watch minutes per 1,000 registered impressions**

Use YouTube's “watch time from impressions” when available. Otherwise compute a
documented approximation from impression CTR and average view duration. This
metric joins packaging quality with content satisfaction and prevents optimizing
CTR alone.

### Portfolio metrics

| Layer | Metrics | Decision supported |
| --- | --- | --- |
| Reach | impressions, unique viewers, views/day, traffic-source mix | Is the topic being distributed? |
| Packaging | CTR by traffic source, native thumbnail-test watch-time share | Does the promise earn the click without clickbait? |
| Intro | 30-second retention, first-45-second retention | Does the opening fulfill the title and thumbnail? |
| Content | average view duration, average view percentage, retention curve, dips/spikes | Which structures and teaching beats hold attention? |
| Loyalty | returning viewers, regular viewers, playlist continuation | Is the series becoming a habit? |
| Conversion | subscribers gained per 1,000 views, end-screen/card actions | Does the episode lead to another relationship? |
| Efficiency | GPU minutes, intervention count, failed runs, cost per qualified watch hour | Is the system sustainable? |
| Safety | claims, policy flags, unresolved provenance, negative feedback | Should autonomy stop? |

Do not compare CTR across Search and Home without traffic-source context. A high
CTR on a narrow loyal audience is not automatically better than a lower CTR on
broader distribution.

### Measurement windows

- `T+0`: verify platform processing, subtitles, thumbnail, title, chapters,
  playlist, visibility, and disclosure settings.
- `T+24h`: anomaly check only; do not declare a winner.
- `T+7d`: packaging and intro review.
- `T+28d`: content, loyalty, and portfolio decision.
- Monthly: series allocation and backlog review.
- Quarterly: channel promise, portfolio structure, and autonomy-policy review.

## Experiment System

### Experiment registry

Every test records:

- experiment ID, hypothesis, owner, start and stop rules;
- eligible series, audience, traffic surface, and publication window;
- control and variants, with asset fingerprints;
- exactly one primary variable;
- primary metric, guardrails, minimum evidence, and decision;
- invalidation reason when the test is contaminated.

### Test types

1. **Thumbnail test:** use YouTube Studio Test & Compare with up to three
   thumbnails. Treat YouTube's final watch-time-share result as the primary
   decision. Candidate families:
   - emotional reaction;
   - concrete outcome or line;
   - situational tension.
2. **Title cohort test:** compare matched videos across multiple releases. Do
   not repeatedly swap titles on one live video and call the result causal.
   Candidate families:
   - situation first;
   - learner outcome first;
   - tension plus repair.
3. **Intro cohort test:** test hook architecture while holding topic class,
   duration band, series, and packaging family as constant as practical.
4. **Format test:** episode duration, rehearsal density, chapter placement, or
   recap length. Run only after packaging is stable.
5. **Portfolio test:** cadence and series allocation. Evaluate over at least one
   28-day audience cycle.

### Decision rules

- Native thumbnail tests run until YouTube finalizes the result or the defined
  maximum window expires; the platform notes this may take days or up to two
  weeks.
- Cohort tests require at least four eligible videos per arm and a full 28-day
  window unless an explicit safety guardrail stops them earlier.
- Low-volume tests remain `inconclusive`; they do not manufacture a winner.
- A variant scales only if the primary metric improves without a material loss
  in average view duration, intro retention, or negative-feedback guardrails.
- After a win, run one confirmation test before changing the series template.
- Never change title, thumbnail, intro, duration, and cadence in the same test.

## Data And Automation Architecture

### Proposed public controller

```powershell
$py = ".\.conda-env\python.exe"
& $py scripts/channel_ops.py reconcile
& $py scripts/channel_ops.py sync-analytics
& $py scripts/channel_ops.py plan --horizon 28d
& $py scripts/channel_ops.py produce --next
& $py scripts/channel_ops.py upload --episode <id> --privacy private
& $py scripts/channel_ops.py schedule --approved-policy
& $py scripts/channel_ops.py analyze --window 7d
& $py scripts/channel_ops.py review --monthly
& $py scripts/channel_ops.py status
```

### Durable data model

Runtime data lives under `workspace/channel_ops/` and is not committed when it
contains private channel data. Tracked schemas, rules, and migrations live in
the normal application/code roots.

Minimum entities:

- `episodes`: canonical series/episode identity and artifact fingerprints;
- `publications`: video ID, URL, playlist, visibility, timestamps, and status;
- `metric_snapshots`: raw and normalized T+24h/T+7d/T+28d observations;
- `retention_points`: per-video elapsed ratio and retention measurements;
- `experiments`, `variants`, and `assignments`;
- `decisions`: evidence, rule version, action, confidence, and rollback;
- `production_runs`: duration, retries, failures, GPU use, and QC outcome;
- `policy`: approved cadence, write permissions, escalation rules, and limits.

Raw API or Studio captures are immutable. Derived tables can be rebuilt. Every
recommendation cites the snapshot IDs and rule version that produced it.

### Integration boundaries

- YouTube Data API: private upload, metadata, playlists, captions, custom
  thumbnail, and publication status.
- YouTube Analytics/Reporting APIs: views, watch time, average duration and
  percentage, subscribers, traffic sources, and retention curves.
- YouTube Studio: impressions/CTR reports and native Thumbnail Test & Compare.
  These Studio-only workflows may use the signed-in in-app browser after the
  user authorizes the account connection and the automation policy.
- Local ELR pipeline: scripts, images, audio, QC, mastering, subtitles, and MP4.

An unverified YouTube API project may be restricted to private uploads. The
system must detect this and treat private upload plus human/Studio scheduling as
the supported path until the API project passes the required audit.

## Autonomous Decision Loop

```text
observe -> diagnose -> propose hypothesis -> select experiment
  -> reserve topic -> produce variants -> quality gate -> publish safely
  -> collect evidence -> decide -> update priors/templates/backlog -> repeat
```

The planner scores topic candidates on demand evidence, learner pain, series
fit, novelty, teachability, visual tension, follow-up potential, and production
cost. It must also reserve a control percentage so the system can distinguish
real improvement from audience or season changes.

The system writes a weekly decision memo containing:

1. What changed in the data.
2. Which hypothesis is most plausible and which alternatives remain.
3. What will be tested next.
4. What will not be changed, to preserve causal clarity.
5. Stop conditions and rollback.

## Autonomy Ladder

| Level | Capability | Exit criteria |
| --- | --- | --- |
| 0 · Reconcile | Build publication ledger and analytics baseline; no channel writes | 100% published-video mapping and 28-day baseline |
| 1 · Recommend | Produce weekly plan and experiment proposals | Four weeks of decisions accepted without material correction |
| 2 · Prepare | Autonomously research, script, produce, and upload private | Eight consecutive packages pass QC and platform validation |
| 3 · Schedule | Schedule inside approved cadence and experiment policy | Eight scheduled releases with no policy breach and reliable rollback |
| 4 · Closed loop | Choose next topics/variants and reallocate cadence within limits | Two stable 28-day cycles with audit-complete decisions |

Autonomy advances one level at a time and automatically drops one level after a
policy breach, unexplained metric anomaly, repeated production failure, missing
data, or provenance uncertainty.

## Immediate 30-Day Product Plan

### Week 1: truth and reconciliation

- Preserve the read-only Studio baseline in a durable snapshot and map all 57
  published dialogue videos to canonical episodes.
- Backfill title, thumbnail, URL, video ID, publish date, playlist, and current
  visibility.
- Reconcile backlog status with the 63 local completed videos.
- Verify the Polished English 019 media fingerprint. After explicit approval
  for a channel write, correct its copied First Steps metadata in place.
- Import at least 90 days of available video and channel analytics.
- Segment results by series, topic class, duration band, traffic source, and
  packaging family.

### Week 2: baseline and positioning decision

- Turn the initial scorecard into reproducible 7-day and 28-day snapshots.
- Implement the current diagnosis: First Steps for reach, Daily Talk for
  satisfaction, and Polished English at low cadence for authority/conversion.
- Add publication-identity preflight and idempotency tests before releasing 020.

### Week 3: controlled packaging tests

- Generate three thumbnail variants for `Talk Out Loud When Nobody Is
  Listening` and an exploratory set for `Switching Languages All Day Is
  Exhausting`.
- Start native Test & Compare in Studio.
- Assign the next four release candidates to a title cohort test.
- Do not make structural script changes in the same cohort.

### Week 4: first measured release and review

- Publish/schedule from the existing bank under the approved two-slot cadence.
- Collect T+24h and T+7d observations.
- Write the first evidence-linked decision memo.
- Approve, reject, or revise the next 28-day plan.

## Stop And Escalation Rules

Stop automatic publication and notify the user when:

- required analytics or publication state is missing or contradictory;
- a scheduled item falls outside policy;
- copyright, impersonation, synthetic-media disclosure, or provenance is
  uncertain;
- a platform warning, strike, claim, or authentication change appears;
- two consecutive releases breach a quality or negative-feedback guardrail;
- production fingerprints do not match the reviewed package;
- a proposed change alters the channel promise or removes a series.

The agent may pause cadence, repackage an existing video, or select a control
episode within policy. It may not delete content, concede a claim, change
monetization, spend money, or make a major brand repositioning without the user.

## Official Platform Constraints Used By This Plan

- YouTube Data API supports video upload and custom-thumbnail operations, but
  unverified projects can be restricted to private uploads.
- YouTube Analytics/Reporting APIs expose watch time, average duration and
  percentage, traffic sources, subscribers, and audience-retention curves.
- Impressions and impression CTR require Studio-level reporting for the full
  workflow; analyze them with traffic-source context, not in isolation.
- Native Thumbnail Test & Compare supports up to three concurrent thumbnails
  and optimizes using watch-time share; final results may take up to two weeks.
- Synthetic-media disclosure is policy-dependent. Non-realistic artwork and
  production assistance are generally treated differently from realistic
  fabricated scenes or another person's cloned voice. Preserve voice and image
  provenance and evaluate the disclosure field for every upload.

These constraints must be rechecked against current official documentation when
the integrations are implemented.
