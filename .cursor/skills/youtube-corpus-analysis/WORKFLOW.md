# YouTube Corpus Analysis Workflow

## Prerequisites

Build or refresh the corpus first with **youtube-podcast-research**:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/collect_youtube_corpus.py --smoke
.\.conda-env\python.exe .cursor/skills/youtube-podcast-research/scripts/score_trending_videos.py --dual-host-only
```

## Analyze Corpus Patterns

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-corpus-analysis/scripts/analyze_youtube_corpus.py
```

## Analyze Transcript Structure And Briefs

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-corpus-analysis/scripts/analyze_transcript_structure.py
```

Outputs episode brief suggestions for `polished_english` and general dialogue podcasts.

## Generate Markdown Report

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-corpus-analysis/scripts/generate_research_report.py
```

## Hand Off To Scriptwriting

1. Read `analysis/episode_brief_suggestions.json` for topic clusters and learner problems.
2. Read `analysis/youtube_research_report.md` for durable title/CTA patterns.
3. Draft with **dialogue-podcast-scriptwriting** or **polished-english-episode-script**.
4. Never paste competitor transcript text into scripts.

## Full Loop (cross-skill)

```text
youtube-browser-automation  →  optional low-level search
youtube-podcast-research    →  discover / collect / score trending
youtube-corpus-analysis     →  patterns / beats / briefs / report
dialogue-podcast-scriptwriting (+ polished-english-episode-script) →  original scripts
```
