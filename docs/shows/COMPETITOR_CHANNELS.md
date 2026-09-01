# Competitor channels — topic research reference set

These YouTube channels feed the **real-investigation topic pipeline** for ELR Series A/B/C scripts. They are demand signals only — never copy titles, hooks, anecdotes, or transcript wording.

Canonical machine list: `apps/worker-py/worker/youtube_podcast_research/workspace.py` → `DEFAULT_CHANNELS`.

CEFR routing for backlog candidates: `workspace/shows/tools/refresh_topic_backlog.py` → `CHANNEL_LEVEL_HINT`.

## How to investigate topics for a show (full flow)

Documented in [`EPISODE_PIPELINE.md`](EPISODE_PIPELINE.md) § **Topic selection**. Summary:

```text
[scrape, anti-ban]  scripts/run_research_refresh.py --channel <slug>
                    → workspace/dialogue_podcast_research/youtube_corpus/…

[offline]           workspace/shows/tools/refresh_topic_backlog.py --all
                    → merges hot titles + briefs into topic_backlog.json

[offline]           workspace/shows/tools/select_next_topic.py --show series_X --apply
                    → topic_selection_<date>.json (differentiationAngle for scriptwriter)

[scriptwriting]     series skill + validate_podcast_script.py

[offline]           workspace/shows/tools/mark_topic_done.py --show series_X --episode episode_YYY --auto
```

**Anti-ban:** one channel per refresh run; smoke canary first; 60-min cooldown on rate-limit; never parallel scrape. See EPISODE_PIPELINE.md.

**Anti-homogeneity:** each backlog candidate carries `sourceCompetitor`, `sourceTitle`, `differentiationAngle`; max 3 candidates per (channel, series) per refresh.

## Active reference channels

| Slug | Channel | URL | ELR series hint |
| --- | --- | --- | --- |
| `englishwithhopeee` | English With HOPE | https://www.youtube.com/@englishwithHOPEEE | B · A2-B1 |
| `jandmaypodcast` | J and May Podcast | https://www.youtube.com/@JandMayPodcast | A · B1-B2 |
| `speakenglishwithclass` | Speak English With Class | https://www.youtube.com/@SpeakEnglishWithClass | B · A2-B1 |
| `maxandmiapodcast` | Max & Mia Podcast | https://www.youtube.com/@MaxandMiaPodcast | A · B1-B2 |
| `davidandaliceenglish` | Speak English with David & Alice | https://www.youtube.com/@English.Academy.plus-o | B · A2-B1 |
| `goenglishpodcast` | Go English - The Podcast | https://www.youtube.com/@Goenglishpodcast | B · A2-B1 |
| `englishpodcastunleashed` | English Unleashed: The Podcast | https://www.youtube.com/@EnglishPodcastUnleashed | C · B2-C1 |
| `englishconversationpod` | English Conversation Podcast | https://www.youtube.com/@EnglishConversationPod | A · B1-B2 |
| `englishgoalpodcast` | **English Goal Podcast** | https://www.youtube.com/@EnglishGoalPodcast | A · B1-B2 |
| `highlevellistening` | High Level Listening | https://www.youtube.com/@highlevellistening | C · B2-C1 |
| `bbclearningenglish` | BBC Learning English | https://www.youtube.com/@bbclearningenglish | A · trend reference |

Series key: **A** = Daily Talk (B1-B2), **B** = First Steps (A2-B1), **C** = Polished English (B2-C1).

## English Goal Podcast

- **Hosts:** Kevin + Rachel (dual-host, easy everyday conversation).
- **Why included:** B1-B2 daily-life dialogue packaging; complements Max & Mia / English Conversation Pod without duplicating Class/J&May angles.
- **First collect (when refreshing corpus):**

```powershell
.\.conda-env\python.exe scripts/run_research_refresh.py --channel englishgoalpodcast
.\.conda-env\python.exe workspace/shows/tools/refresh_topic_backlog.py --all
```

## Adding a new channel

1. Add entry to `DEFAULT_CHANNELS` in `workspace.py` (slug, name, url).
2. Add name + slug to `CHANNEL_LEVEL_HINT` in `refresh_topic_backlog.py`.
3. Add a row to the table above in this file.
4. Collect **one channel at a time** via `run_research_refresh.py --channel <slug>`.
5. Run `refresh_topic_backlog.py --all` offline to merge new hot titles into backlogs.

## Analysis outputs (local, no scrape)

```text
workspace/dialogue_podcast_research/youtube_corpus/analysis/corpus_analysis.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/episode_brief_suggestions.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/trending_videos.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/youtube_research_report.md
```

Scriptwriters read aggregate patterns via [`.cursor/skills/dialogue-podcast-scriptwriting/RESEARCH.md`](../../.cursor/skills/dialogue-podcast-scriptwriting/RESEARCH.md); selection records expose per-topic `differentiationAngle`.

## Adjacent long-form reference cohort

The canonical scraper list above remains focused on comparable English
learning channels. Weekly long-form investigation must also inspect a small
manual adjacent cohort so the channel learns topic and retention mechanics
without pretending that all competitors have the same audience:

| Cohort | Examples | Study | Do not import |
| --- | --- | --- | --- |
| Slow-English life ideas | Slow English Podcast, Speak English With Class | Simple-language pacing, chapter movement, life-topic packaging | Celebrity imitation, invented quotes, repetitive padding |
| Evidence-led psychology | Therapy in a Nutshell | Clear distinctions, demonstrations, responsible scope | Clinical advice without primary-source review |
| Accessible philosophy | Daily Stoic, TED-Ed, current Stoicism channels | One idea, historical context, modern application | Sensational fear, quote laundering, authority theater |
| Mainstream women-focused self-development | Mel Robbins, A Better You, The Balance Theory | Emotional specificity, lived experience, community questions | Personality copying or abrupt channel rebranding |

Record manual evidence in the dated market report or weekly plan. Require
publication date, views, runtime, opening promise, structural device, risk, and
a differentiation angle. The current baseline is
[`LONG_FORM_MARKET_RESEARCH_2026-09-01.md`](LONG_FORM_MARKET_RESEARCH_2026-09-01.md).
