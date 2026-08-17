# Research Guidance

## Where Research Lives

YouTube acquisition and analysis feed the **topic-selection pipeline** (see [`docs/shows/EPISODE_PIPELINE.md`](../../../docs/shows/EPISODE_PIPELINE.md) § Topic selection and [`docs/shows/COMPETITOR_CHANNELS.md`](../../../docs/shows/COMPETITOR_CHANNELS.md)).

- **Real investigation (scrape, anti-ban)** — `scripts/run_research_refresh.py --channel <slug>` refreshes one competitor channel at a time into the local corpus, then re-runs offline analysis.
- **Offline topic merge** — `workspace/shows/tools/refresh_topic_backlog.py --all` reads analysis JSON and merges candidate topics into each series `topic_backlog.json` (records `sourceCompetitor`, `sourceTitle`, `differentiationAngle`).
- **Offline pick next topic** — `workspace/shows/tools/select_next_topic.py --show series_X --apply`.

Legacy skill names (`youtube-podcast-research`, `youtube-corpus-analysis`) refer to the same corpus under `workspace/dialogue_podcast_research/youtube_corpus/`.

Default analysis outputs:

```text
workspace/dialogue_podcast_research/youtube_corpus/analysis/youtube_research_report.md
workspace/dialogue_podcast_research/youtube_corpus/analysis/episode_brief_suggestions.json
```

## How To Use The Corpus

- Use titles, descriptions, and analysis JSON as aggregate market research.
- Extract patterns: promise shape, learner problem, episode pacing, CTA type, and vocabulary level.
- Do not reuse full transcript passages, distinctive stories, or channel-specific catchphrases.
- Convert monologue lessons into original two-host dialogue: one host asks or makes the learner mistake, the other host coaches and models natural English.

## Durable Patterns To Prefer

High-performing English learning content usually has a narrow, concrete promise:

- Fix one common mistake.
- Practice one real-life situation.
- Learn one phrase family.
- Sound more natural in one specific context.
- Compare awkward learner English with natural spoken English.

Good podcast episode titles should be specific enough to imply the listener outcome:

```text
Stop Saying "I'm Fine": Natural Answers For Everyday English
Ordering Coffee In English Without Freezing
5 Polite Phrases Native Speakers Use At Work
Why Your English Sounds Too Formal In Casual Conversation
```

## Description Pattern

Use 2-4 short paragraphs:

1. State the learner pain point.
2. Promise what the episode practices.
3. List 3-5 phrases or situations covered.
4. End with one action: comment an answer, repeat a prompt, subscribe, or download notes if available.

## Two-Host Conversion Pattern

Map research insights into two stable roles:

- Host A: learner proxy, curious friend, asks direct questions, makes realistic mistakes.
- Host B: coach, concise explainer, models natural phrases and gives corrections.

Every teaching point should appear in dialogue:

1. Host A says the awkward or basic version.
2. Host B gives the natural version.
3. Both hosts act out a short example.
4. Host A tries a variation.
5. Host B recaps the rule in one sentence.

## Episode Rhythm

For a 6-10 minute draft:

- Hook: 30-45 seconds.
- Main lesson: 3-5 teaching beats.
- Practice loop: repeat-after-me or choose-the-better-line.
- Recap: 3 takeaways.
- CTA: one learner action.

Keep each host turn short enough for natural TTS later: usually 1-3 sentences per turn.
