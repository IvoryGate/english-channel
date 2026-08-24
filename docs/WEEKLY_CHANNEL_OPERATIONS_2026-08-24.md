# Weekly Channel Operations — 2026-08-24

## Outcome

The channel now runs one fixed portfolio instead of independent publication
pipelines. The next four weeks use a stable Asia/Shanghai schedule:

| Slot | Program | Role |
| --- | --- | --- |
| Monday 08:00 | Classic Listening | long-session depth; voice-gated |
| Tuesday 20:00 | First Steps | acquisition |
| Wednesday 12:30 | Short | discovery and long-form routing |
| Thursday 20:00 | Daily Talk | satisfaction and habit |
| Friday 12:30 | Short | discovery and creative testing |
| Saturday 20:00 | Polished English | authority and conversion |
| Sunday 12:30 | Short | discovery and next-week preview |

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
| Tue 25 Aug, 20:00 | First Steps 020 | verified package |
| Wed 26 Aug, 12:30 | Short 005 | package passes; related video pending |
| Thu 27 Aug, 20:00 | Daily Talk 020 | verified package |
| Fri 28 Aug, 12:30 | Short 006 | package passes; related video pending |
| Sat 29 Aug, 20:00 | Polished English 020 | verified package |

The three 021 packages remain the following week's buffer at the same weekday
and time. Local reservations do not schedule YouTube and grant no remote write
authority.

## Production Queue

1. The tracked Nora/Riley/Mia blind narrator pack has been rendered across all
   six audio acceptance cases. Review `voice-a.wav`, `voice-b.wav`, and
   `voice-c.wav` under the ignored audition `review/` directory; Classic
   Listening remains blocked until one candidate is explicitly accepted.
2. Restore a three-Short ready buffer by producing 007-009 after the narrator
   GPU job releases the shared heavy-resource lease.
3. The first 25-35 minute First Steps Deep Practice pilot now has a production
   brief in `configs/channel/deep-practice-pilot-series-b-2026-09.json`; script
   production is queued for the 2026-09-08 slot. Standard 10-15 minute episodes
   remain in the weekly mix; the pilot adds scenarios, breakdown, guided
   repetition, and a natural-speed replay rather than padding.
4. At T+24h, record delivery anomalies only. At T+7d, review packaging and the
   opening. At T+28d, decide the next portfolio allocation.

## Description Contract

Every regenerated Dialogue description includes the fixed programming footer.
The video body still leads with the episode promise, chapter timestamps,
learning highlights, and one engagement question. The fixed schedule appears
before hashtags so a new viewer can understand when and why to return.

Classic Listening and Shorts must adopt the same schedule disclosure in their
next package revision. Every Short must name or attach its related long-form
video before remote scheduling.

## Stop Conditions

- Do not release Classic Listening before narrator acceptance.
- Do not remotely schedule Short 005/006 before their related-video fields are
  verified.
- Do not create a public duplicate when a local or remote identity already
  exists.
- Do not change title, thumbnail, opening, and cadence in one experiment.
- Missing Studio analytics remain missing; they are never converted to zero.
