# Weekly Channel Operations — 2026-08-24

## Outcome

The channel now runs one fixed portfolio instead of independent publication
pipelines. The next four weeks use a stable Asia/Shanghai schedule:

| Slot | Program | Role |
| --- | --- | --- |
| Every day 12:30 | Short | discovery, testing, and long-form routing |
| Monday 08:00 | Classic Listening | long-session depth; voice-gated |
| Tuesday 20:00 | First Steps | acquisition |
| Thursday 20:00 | Daily Talk | satisfaction and habit |
| Saturday 20:00 | Polished English | authority and conversion |

Community rituals run alongside this grid: Monday Choice, Wednesday Reply
Challenge, Friday Phrase Clinic, and Sunday Reading Club. Each post asks one
answerable question and receives a reply pass within 24 hours.

The fixed grid and public description footer are versioned in
`configs/channel/programming.json`. Do not move slots before the first review
on 2026-09-20 unless identity, platform, quality, or production evidence forces
a stop.

## Current Evidence

The public channel page was read on 2026-08-24 and displayed 92 subscribers,
121 videos, and 5,331 lifetime views. The 78-subscriber value remains valid
only as the signed-in Studio snapshot from 2026-08-17; it is not the current
subscriber count.

The refreshed public RSS feed still ends with Shorts 004 on 2026-08-19 and
Dialogue 019 on 2026-08-17. It contains no Dialogue 020/021 release. The feed
does not cover private or unlisted inventory.

## This Week

| Local slot | Content | Readiness |
| --- | --- | --- |
| Mon 24 Aug, 17:00 | Short 005 | package passes; related video pending |
| Mon 24 Aug, 20:00 | First Steps 020 | verified catch-up package |
| Tue 25 Aug, 12:30 | Short 006 | package passes; related video pending |
| Wed 26 Aug, 12:30 | Short 007 | package passes; related video pending |
| Thu 27 Aug, 12:30 | Short 008 | package passes; related video pending |
| Thu 27 Aug, 20:00 | Daily Talk 020 | verified package |
| Fri 28 Aug, 12:30 | Short 009 | package passes; related video pending |
| Sat 29 Aug, 12:30 | Short 010 | package passes; related video pending |
| Sat 29 Aug, 20:00 | Polished English 020 | verified package |
| Sun 30 Aug, 12:30 | Short 011 | package passes; related video pending |

The three 021 packages remain the following week's buffer at the same weekday
and time. Local reservations do not schedule YouTube and grant no remote write
authority.

## Production Queue

1. Recover the Classic narrator first. The blind pack was rejected: candidate
   A drifted to a male voice despite having little electronic texture, while B
   and C remained female but had obvious electronic artifacts. Run a new female
   synthesis pass from `configs/classics/narrator-audition-recovery.json` with
   higher inference steps and lower guidance; Classic Listening remains blocked
   until one candidate is explicitly accepted. The D/E/F recovery pack is now
   rendered. E has the lowest mean 8 kHz high-band ratio (`0.033050`), followed
   by D (`0.036172`) and F (`0.067554`); use that only to prioritize listening,
   not as automatic voice approval.
2. Shorts 007-011 are complete and pass their package gates for the daily 12:30
   cadence. Scale to a second 18:00 Short only after seven ready items are
   present in the scheduled buffer, rolling QC is at least 95%, and the
   identity store has no unresolved collision.
3. Historical outcome: the first intended 25-35 minute First Steps Deep
   Practice pilot rendered at 14:46 and is therefore classified as a standard
   episode, not a valid duration treatment. The current recovery contract is
   one 35-45 minute Flagship 40, two 18-25 minute Extended episodes, and three
   10-15 minute Standard episodes per week. See
   `configs/channel/weekly-plan-2026-09-07.json`; measured media duration, not
   the planned label, controls classification.
4. At T+24h, record delivery anomalies only. At T+7d, review packaging and the
   opening. At T+28d, decide the next portfolio allocation.

## Description Contract

Every regenerated Dialogue description includes the fixed programming footer.
The video body still leads with the episode promise, chapter timestamps,
learning highlights, and one engagement question. The fixed schedule appears
before hashtags so a new viewer can understand when and why to return.

Classic Listening and Shorts must adopt the same schedule disclosure in their
next package revision. The public footer now says Shorts run every day at
12:30. Every Short must name or attach its related long-form video before
remote scheduling.

## Stop Conditions

- Do not release Classic Listening before narrator acceptance.
- Do not remotely schedule Short 005/006 before their related-video fields are
  verified.
- Do not create a public duplicate when a local or remote identity already
  exists.
- Do not change title, thumbnail, opening, and cadence in one experiment.
- Missing Studio analytics remain missing; they are never converted to zero.
