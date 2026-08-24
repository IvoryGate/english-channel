# YouTube Browser Research Workflow

## Setup

Install the project runtime, then install the Playwright Chromium binary:

```powershell
.\.conda-env\python.exe -m pip install -r apps/worker-py/requirements.txt
.\.conda-env\python.exe -m playwright install chromium
```

## Search

Smoke test one default query without scrolling:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py --smoke
```

Collect one explicit query and an evidence screenshot:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py `
  --query "english conversation podcast two hosts" --screenshot
```

The JSON result records query, video IDs, URLs, titles, channels, and other
visible search metadata. Downstream corpus collection and analysis remain in
the `youtube-podcast-research` and `youtube-corpus-analysis` skills.

## Safety Boundary

- Use an isolated local browser profile only for public search state.
- Do not enter credentials or reuse a signed-in channel profile.
- Do not add account, Studio, upload, avatar, playlist, or publish actions to
  this skill.
- A future account browser provider must require shared authority checks,
  idempotency, before/after capture, and explicit approval for sensitive
  mutations.
