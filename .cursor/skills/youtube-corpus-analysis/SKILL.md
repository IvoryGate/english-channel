---
name: youtube-corpus-analysis
description: Analyze archived YouTube English podcast corpora — title/CTA patterns, trending signals, transcript structure beats, topic clusters, and polished_english episode briefs. Use when the user asks to analyze competitor podcasts, generate research reports, extract topic/script patterns, or produce episode brief suggestions from the local corpus.
---

# YouTube Corpus Analysis

## Scope

This skill owns **offline analysis** of the local YouTube corpus:

- Title, description, and CTA pattern analysis
- Transcript structure beats (hook, practice, recap, dialogue)
- Topic cluster distribution
- Episode brief suggestions for scriptwriters
- Markdown research reports

It does **not** fetch YouTube data or write finished podcast scripts.

## Agent Invocation Policy

| User intent | Action |
| --- | --- |
| Analyze archived corpus patterns | `analyze_youtube_corpus.py` |
| Analyze transcript beats + topics | `analyze_transcript_structure.py` |
| Render Markdown research report | `generate_research_report.py` |

Requires a corpus built by **youtube-podcast-research**. Read inputs from `CORPUS.md` in that skill.

## Outputs

```text
workspace/dialogue_podcast_research/youtube_corpus/analysis/corpus_analysis.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/transcript_structure.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/episode_brief_suggestions.json
workspace/dialogue_podcast_research/youtube_corpus/analysis/youtube_research_report.md
```

## Downstream Skills

- **dialogue-podcast-scriptwriting** — general two-host scripts from briefs/patterns
- **polished-english-episode-script** — Leo/Mia show-shaped episodes from briefs

Use aggregate patterns only. Do not copy transcript passages into scripts.

Read `WORKFLOW.md` for commands.
