---
name: youtube-browser-automation
description: Playwright browser automation for YouTube search, session persistence, and future AI-driven channel operations. Use when the user asks to automate YouTube in a browser, save login state, search YouTube with Playwright, scrape search results, or build account-operation tooling.
---

# YouTube Browser Automation

## Scope

This skill owns **browser infrastructure only**:

- Playwright Chromium sessions
- Persistent storage state for future account login
- YouTube search and result extraction
- Screenshots for debugging

It does **not** collect full corpora, analyze transcripts, or write podcast scripts. Those live in sibling skills.

## Agent Invocation Policy

Run only when the user explicitly asks for browser automation, Playwright setup, YouTube search scraping, or account-session persistence.

| User intent | Action |
| --- | --- |
| Search YouTube in browser | `youtube_search.py` |
| Save login/session for later reuse | `save_browser_session.py --headful` |
| Debug selectors / page state | `youtube_search.py --screenshot` |

## Shared Library

Implementation lives in:

```text
apps/worker-py/worker/youtube_podcast_research/browser.py
```

Skill scripts are thin CLI wrappers around that library.

## Session Profile

Default persistent profile directory:

```text
workspace/dialogue_podcast_research/youtube_corpus/browser_profile/
```

Use `--headful` once to sign in manually, then rerun headless jobs to reuse saved cookies/storage.

## Downstream Skills

- **youtube-podcast-research** — uses browser discovery output and yt-dlp collection
- **youtube-corpus-analysis** — reads archived corpus artifacts
- **dialogue-podcast-scriptwriting** — drafts original scripts from analysis briefs

Read `WORKFLOW.md` for setup and commands.
