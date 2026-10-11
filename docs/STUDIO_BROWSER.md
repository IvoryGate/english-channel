# Browser Studio Uploads

## Purpose and Boundary

Publishing is **browser-only YouTube Studio automation** over a persistent,
human-visible Chromium session (same proven pattern as
`docs/IMAGEGEN_BROWSER.md`). There is no YouTube API OAuth and no API
token. The browser performs the exact manual flow a human operator used
since day one: open the upload dialog, feed local files, fill metadata
from durable package artifacts, store as **private**, wait for platform
checks, verify, then flip to **public**.

Hard rules that never change:

- Upload first as **private**; publish only after the platform checks
  pass and the agent has verified the details page.
- Never re-upload blindly: check the Studio content list (and the
  `workspace/runtime/studio-browser/uploads/*.json` sidecars) for an
  existing copy before any retry.
- Login is a one-time human step per profile; everything after it is
  scripted. Credentials never enter the repository.

## Session Workflow

```powershell
# Start (persistent Chromium + CDP on port 9335; opens a blank tab)
python apps/worker-py/scripts/studio_session.py

# ...log into YouTube Studio once in that window (first day / expired
# session). Login persists in the profile. ...

# List specs that would be uploaded (pure offline dry run)
python apps/worker-py/scripts/studio_upload.py list `
    --manifest configs/channel/youtube-release-2026-10-05.json

# Upload (attaches over CDP; stores each video as private; writes a
# sidecar with the video id per content id)
python apps/worker-py/scripts/studio_upload.py upload `
    --manifest configs/channel/youtube-release-2026-10-05.json `
    --only content:shorts_main:elr-s-161

# After checks pass and verification: publish
python apps/worker-py/scripts/studio_upload.py publish `
    --manifest configs/channel/youtube-release-2026-10-05.json `
    --only content:shorts_main:elr-s-161

# End of day: Ctrl+C in the session terminal (login persists)
```

Key facts:

- CDP port defaults to **9335** (`ELR_STUDIO_CDP_PORT` overrides), chosen
  so it cannot collide with vibecut (9333) or imagegen (9334).
- Profile (and login) persist in
  `workspace/runtime/studio-browser/chromium-profile/` inside the ignored
  `workspace/` tree.
- Upload results (content id → video id, title, visibility, checks) are
  written to `workspace/runtime/studio-browser/uploads/<contentId>.json`
  for traceability and for the `publish` command.
- The session starts on a blank page by design (a startup navigation with
  no CDP client wedges DevTools on this machine); the upload client
  navigates after attaching.

## Metadata Contract

`load_manifest_specs()` builds every upload from the release manifest and
the durable package artifacts — never from ad-hoc strings:

- long-form shows (`series_a/b/c`): `titleFile` / `descriptionFile`
  (`reports/*.youtube_title.txt`, `*.youtube_description.txt`),
  `thumbnail`, `captions` (`.srt`), `playlistId`, `categoryId`.
- classic chapters: `metadataFile` (`reports/*.youtube.json` with
  top-level `title` / `description` / `tags`) plus `captions` and
  `playlistId`.
- shorts: `package/upload.json` (`upload` block) with `titleFile` /
  `descriptionFile` overrides and a custom `thumbnail`.

## Selector Notes (zh-CN Studio UI, learned the hard way)

- The main video file is set through **CDP `DOM.setFileInputFiles`**
  with a local path. Playwright's normal `set_input_files` refuses files
  larger than 50MB over a CDP connection ("browser not co-located"), and
  the channel's long-form videos are 90–700MB. Thumbnails and captions
  are small and still use the file-chooser path.
- Title/description are `#title-textarea` / `#description-textarea`
  custom components — fill the inner `[contenteditable=true]` node, not
  the host element.
- Custom thumbnails live behind `ytcp-thumbnail-uploader button`
  (labelled "上传文件"); Shorts support custom thumbnails too.
- The wizard's step button is "继续" on details and "下一步" elsewhere;
  the final visibility page's save button is "保存" (not "存为私享").
- The visibility radio must be clicked as `role=radio` named "私享";
  clicking the label text does nothing.
- After saving, Studio pops a "正在处理视频" completion dialog a few
  seconds later whose backdrop blocks everything; dismiss every enabled
  "关闭" button (the wizard's hidden close is disabled — take the last
  enabled one) and press Escape until no
  `tp-yt-iron-overlay-backdrop.opened` remains.
- The live upload dialog element `ytcp-uploads-dialog` exposes the new
  `video-id` as an attribute — the most reliable id source; the content
  list search is only the fallback.
- The `/videos/upload` deep link does **not** reliably open the dialog;
  the Create menu (创建 → 上传视频) does.

## Weekly Loop Position

Uploads happen in the daily production loop after QC passes (see
`docs/YOUTUBE_OPERATING_SYSTEM.md`): render → QC → imagegen cover →
**Studio upload (private) → checks → publish** → write the video id back
into the weekly plan manifest.
