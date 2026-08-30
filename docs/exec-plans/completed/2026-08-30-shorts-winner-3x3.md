# Shorts Winner 3×3 Rapid Experiment — 2026-08-30 to 2026-08-31

## Goal

Turn three clearly stronger channel Shorts into nine controlled iterations,
publish the complete experiment by the end of 2026-08-31 Asia/Shanghai, and
track which topic and interaction form produces the strongest repeatable
viewer response.

## Authority

The channel owner authorized all nine items to be produced, uploaded, and
published within 2026-08-30 and 2026-08-31 after checks pass, without per-item
confirmation. Failed QC, identity collisions, incomplete processing, or a
schedule that has already elapsed blocks only the affected item.

## Scope

Included:

- Analyze `What Does “I'm Good” Mean Here?`, `The Coffee Shop Order That
  Sounds Natural`, and `Can You Catch the Polite Refusal?` against the channel
  baseline.
- Create three original iterations per winner: adjacent phrase transfer,
  interactive context choice, and socially meaningful repair or consequence.
- Generate nine unique bright anime backgrounds for US women aged 25-44.
- Produce, check, upload, and publish all nine Shorts with notifications off.
- Capture public baselines and 6-hour, 24-hour, 72-hour, 7-day, and 14-day
  follow-up snapshots; request authenticated retention evidence when needed.

Excluded:

- Reuploading or editing the three source Shorts.
- Treating public view count alone as proof of causality.
- Reusing one background, composition, or title promise across the experiment.

## System Boundaries

- `configs/shorts/product-winner-3x3.json`
- `configs/shorts/winner-3x3-2026-08-30.json`
- `configs/channel/youtube-release-shorts-winner-3x3-2026-08-30.json`
- `apps/worker-py/worker/shorts/`
- `scripts/shorts.py` and `scripts/youtube.py`
- `docs/shorts/research/`
- ignored runtime media and analytics under `workspace/shorts/`

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-30 22:50 Asia/Shanghai.
- State: completed. All nine packages passed local and YouTube checks; two
  elapsed slots were published immediately and seven items were scheduled.
  The recurring 6-hour analytics heartbeat is active.

## Baseline

Public channel-page observations at approximately 2026-08-30 12:00 +08:00:

| Source Short | Video ID | Public views | Visible likes | Runtime |
| --- | --- | ---: | ---: | ---: |
| `What Does “I'm Good” Mean Here?` | `l9SW9N4QmCY` | 572 | 11 | 39 sec |
| `The Coffee Shop Order That Sounds Natural` | `FB2ZKgGJbNM` | 342 | 5 | 36 sec |
| `Can You Catch the Polite Refusal?` | `Hyn7mOh2FFw` | 296 | 9 | 54 sec |

The next-best visible recent Short had 115 views; most visible peers had
16–45. The three winners all teach pragmatic real-life English through a
specific social moment, reveal an interpretation or natural alternative, and
use dialogue rather than detached explanation. This supports replication, not
yet a causal conclusion about any single element.

## Plan

1. Capture a 30-thumbnail public reference cohort and the complete visible
   channel baseline.
2. Freeze nine hypotheses and one primary variable per iteration.
3. Generate and contact-sheet review nine unique mobile-first backgrounds.
4. Bootstrap manifests; render audio, video, and dedicated covers.
5. Pass content, uniqueness, brightness, saturation, media, and package QC.
6. Upload privately, verify processing and settings, then publish three items
   on August 30 and six on August 31 in a balanced sequence.
7. Record real video IDs and immutable baseline fingerprints.
8. Run scheduled data snapshots and make keep/iterate/stop decisions only
   after comparable windows.

## Validation

- The portfolio names a real 30-item research artifact.
- Nine distinct content keys and nine distinct generated backgrounds exist.
- Every package passes with no visual-gate exception.
- Every remote video ID is unique, public at its approved time, made-for-kids
  false, and notifications off.
- Snapshot comparisons normalize by hours live and report views, visible like
  rate, comments, shares/subscribers when available, and retention evidence
  rather than raw views alone.

## Risks And Decisions

- Nine releases in two days can cannibalize distribution. The owner explicitly
  chose speed; releases are spaced and notifications remain off.
- Public view counters can be cached and differ from Studio. Public snapshots
  are directional; Studio/Analytics is the source for retention and subscriber
  attribution.
- The source thumbnails are warm and somewhat dark, but their content won.
  New art retains the relatable social situations while following the new
  bright anime and originality gates.
- Each iteration changes one primary content-form variable; time slot is
  recorded as a nuisance variable, not ignored.

## Archive Criteria

- All nine items have passing packages, real video IDs, and verified public or
  scheduled states no later than 2026-08-31.
- Baseline and follow-up automation are installed.
- The branch is committed, pushed, and merged after required checks pass.

## Execution Result

- Published immediately after elapsed slots: `elr-s-026` (`uEW7EO1pM08`) and
  `elr-s-030` (`w1gPKHGzO0o`).
- Scheduled for 2026-08-31: `elr-s-034` at 00:00, `elr-s-029` at 07:00,
  `elr-s-033` at 09:30, `elr-s-028` at 11:00, `elr-s-032` at 14:30,
  `elr-s-027` at 16:00, and `elr-s-031` at 21:30, all Asia/Shanghai.
- YouTube rejected the requested same-day 23:45 entry for `elr-s-034` as not
  being a future time, so the closest accepted slot, 00:00, was used.
- All items use dedicated generated thumbnails, AI-use disclosure, English
  language, Education category, made-for-kids false, notifications off, and a
  related long video.
- Validation passed: `npm run lint`, `npm test` (165 Python tests plus all
  JavaScript workspace tests), package gates for all nine items, and platform
  copyright/community checks.
- Automation `3-3-shorts` runs every six hours and records only due 6-hour,
  24-hour, 72-hour, 7-day, and 14-day experiment windows.
