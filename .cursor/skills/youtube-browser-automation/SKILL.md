---
name: youtube-browser-automation
description: Read-only Playwright search and screenshot collection for YouTube market research. Use when browser search evidence is explicitly requested and API or archived corpus evidence is insufficient.
---

# YouTube Browser Research

## Scope

This skill owns a narrow read-only browser boundary:

- YouTube search result discovery;
- metadata extraction into the ignored research workspace;
- optional screenshots for selector/debug evidence.

It does not sign in, persist account credentials, upload media, edit channel
branding, change metadata, create playlists, schedule, publish, or delete.
Account mutations belong behind the shared channel authority/provider boundary.

## Invocation Policy

Use only when the user requests browser research or when the tracked research
workflow explicitly calls for a browser-search refresh. Prefer APIs and archived
corpora when they provide the required evidence.

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py --smoke
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py --query "english conversation podcast two hosts" --screenshot
```

Output is written under
`workspace/dialogue_podcast_research/youtube_corpus/discovery/` and remains
runtime evidence rather than tracked strategy truth.

Read `WORKFLOW.md` for setup, commands, and boundaries.
