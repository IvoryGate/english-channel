# Source Channels

Default channels archived by `collect_youtube_corpus.py` (defined in `apps/worker-py/worker/youtube_podcast_research/workspace.py::DEFAULT_CHANNELS`):

## Original set (user-supplied)

| Slug | Name | URL |
| --- | --- | --- |
| `englishwithhopeee` | English With HOPE | https://www.youtube.com/@englishwithHOPEEE |
| `jandmaypodcast` | J and May Podcast | https://www.youtube.com/@JandMayPodcast |
| `speakenglishwithclass` | Speak English With Class | https://www.youtube.com/@SpeakEnglishWithClass |

## Expanded set (dual-host competitors — surfaced by discovery)

Added to broaden trend signals and reduce homogeneity risk from tracking only the original 3. These are direct competitors (two-host English learning podcasts).

| Slug | Name | URL |
| --- | --- | --- |
| `maxandmiapodcast` | Max & Mia Podcast | https://www.youtube.com/@MaxandMiaPodcast |
| `davidandaliceenglish` | Speak English with David & Alice | https://www.youtube.com/@English.Academy.plus-o |
| `goenglishpodcast` | Go English - The Podcast | https://www.youtube.com/@Goenglishpodcast |
| `englishpodcastunleashed` | English Unleashed: The Podcast | https://www.youtube.com/@EnglishPodcastUnleashed |
| `englishconversationpod` | English Conversation Podcast | https://www.youtube.com/@EnglishConversationPod |
| `highlevellistening` | High Level Listening Advanced English Podcast | https://www.youtube.com/@highlevellistening |

## Trend reference (institutional, not a direct competitor)

| Slug | Name | URL |
| --- | --- | --- |
| `bbclearningenglish` | BBC Learning English | https://www.youtube.com/@bbclearningenglish |

## Collecting (anti-ban)

Add new channels by extending `DEFAULT_CHANNELS`, then collect **one channel at a time** via `scripts/run_research_refresh.py --channel <slug>` (never all at once). Discovery results in `discovery/` may surface more channels to add after manual review.

## Anti-homogeneity policy

Studying competitors is for **demand signals** (what topics learners watch), not for copying their format, titles, or phrasing. The topic-selection flow enforces this:

- `refresh_topic_backlog.py` records each candidate's `sourceCompetitor` + `sourceTitle` + a `differentiationAngle` prompt.
- `select_next_topic.py` exposes those fields in the selection record and applies a **source-diversity bonus** so selection rotates across competitors instead of clustering on one channel's playbook.
- The scriptwriter must read `differentiationAngle` and deliberately diverge in hook, angle, and phrasing — never clone a competitor's title or structure.

See `docs/shows/EPISODE_PIPELINE.md` § Topic selection.
