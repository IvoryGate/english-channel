# YouTube Browser Automation Workflow

## Setup

```powershell
.\.conda-env\python.exe -m pip install -r apps/worker-py/requirements.txt
.\.conda-env\python.exe -m playwright install chromium
```

## Search YouTube

Smoke (one default query, no scroll):

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py --smoke
```

Custom query with screenshot:

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/youtube_search.py --query "english conversation podcast two hosts" --screenshot
```

Output:

```text
workspace/dialogue_podcast_research/youtube_corpus/discovery/browser_search_latest.json
```

## Connect YouTube Account

Google often blocks Playwright's bundled Chromium with **"This browser or app may not be secure"**.  
Use **installed Google Chrome** with a persistent profile instead.

**Important:** Close stale Chrome windows before Playwright scripts, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .cursor/skills/youtube-browser-automation/scripts/close_browser_profile.ps1
```

Playwright sessions now close extra tabs on start/end so the profile does not accumulate tabs.

### Recommended: open real Chrome (no automation)

```powershell
powershell -ExecutionPolicy Bypass -File .cursor/skills/youtube-browser-automation/scripts/open_youtube_login.ps1
```

1. Chrome opens YouTube Studio with the project profile folder.
2. Sign in normally with your Google account.
3. Close Chrome when done — cookies stay in `chrome_user_data/`.

### Alternative: Playwright + installed Chrome

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/save_browser_session.py --headful
```

Uses `channel=chrome` and the same `chrome_user_data/` profile. Press **Enter** in the terminal when login is done.

### Verify

```powershell
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/verify_youtube_session.py --headful
```

Profile directory (local only):

```text
workspace/dialogue_podcast_research/youtube_corpus/browser_profile/chrome_user_data/
```

**Security:** Do not paste passwords into chat. Login happens only in the browser.

## Upload Channel Avatar (Playwright)

```powershell
powershell -ExecutionPolicy Bypass -File .cursor/skills/youtube-browser-automation/scripts/close_browser_profile.ps1
.\.conda-env\python.exe .cursor/skills/youtube-browser-automation/scripts/update_channel_avatar.py
```

Default image: `workspace/dialogue_podcast_research/youtube_corpus/branding/channel_avatar_elr_800.jpg`

Studio may show an unsupported-browser warning; the script clicks **Skip to YouTube Studio** automatically.

## Extension Points

Future AI account operations should extend `worker/youtube_podcast_research/browser.py`:

- upload packaging review
- comment moderation drafts
- studio analytics page scraping
- scheduled publish checks

Keep account actions in this skill or a future `youtube-account-operations` skill — not in scriptwriting or analysis skills.
