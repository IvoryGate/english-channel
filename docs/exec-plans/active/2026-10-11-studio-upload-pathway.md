# Studio Upload Pathway — 2026-10-11

## Goal

Give the channel a durable, browser-only YouTube Studio upload pathway so
the agent can upload, verify, and publish videos end to end without the
human clicking through the UI, and without any API OAuth. The immediate
driver is the 2026-10-05 week backfill: 13 verified-missing uploads
(4 long-form, 9 Shorts) that must land private, pass platform checks,
and be published by the agent.

## Why Not the Harness Browser

The harness desktop browser's `files.upload` tool copies bytes over RPC
with a hard 5 MiB cap; channel files are 47–700 MB. The Playwright MCP
browser likewise transfers rather than referencing local paths and would
need yet another login. The proven pattern is the one already used for
image generation: a repository-owned persistent Chromium with a CDP port
and Python Playwright attached over CDP.

## Scope

- `apps/worker-py/worker/studio/session.py` — persistent headed
  Chromium, CDP 9335, profile `workspace/runtime/studio-browser/`,
  blank startup, human one-time login.
- `apps/worker-py/worker/studio/upload.py` — manifest-driven specs,
  upload-as-private flow, dialog dismissal, video-id capture
  (`ytcp-uploads-dialog` attribute, content-list fallback), publish
  flip, sidecar trace records.
- `apps/worker-py/scripts/studio_session.py` and
  `apps/worker-py/scripts/studio_upload.py` (list/upload/publish).
- `apps/worker-py/tests/test_studio.py` — pure-logic tests (spec
  building for the three metadata conventions, validation, id parsing).
- `docs/STUDIO_BROWSER.md` — operations doc with the selector notes
  learned during the first live uploads.
- Backfill execution: upload the 13 missing items private, verify checks,
  publish, adopt all remote video IDs (including the 7+2 already on
  platform) into `configs/channel/weekly-plan-2026-10-05.json`, record
  the temporary rolling-7-day-limit exception, archive the 2026-10-03
  week plan.

## Non-Goals

- No YouTube Data API path; no credentials in the repository.
- No Shorts background or large media committed (runtime profile and
  sidecars stay inside the ignored `workspace/` tree).
- No changes to render/QC pipelines; this pathway consumes existing
  QC-passed artifacts only.

## Key Decisions

- Files are fed to Studio through **CDP `DOM.setFileInputFiles`** with
  local paths because Playwright refuses >50 MB transfers over a CDP
  connection; thumbnails/captions (small) use the file-chooser path.
- Uploads are always stored **private** first; publishing is a separate
  command that runs only after platform checks pass and details have
  been verified, per the owner's instruction that the agent completes
  the loop itself.
- Upload results are journaled as per-content JSON sidecars under
  `workspace/runtime/studio-browser/uploads/`, which the `publish`
  command and the weekly-plan ID write-back consume.

## Status

- [x] Session + upload modules, scripts, pure-logic tests, docs.
- [x] Live flow proven on Shorts (title/description/custom thumbnail/
  private/checks/video-id capture), including >50 MB files via CDP.
- [ ] Remaining backfill: 6 Shorts (s-168…s-173) + 4 long-form
  (c:ep029, c:ep030, a:ep034, persuasion ch009) uploaded, verified,
  published.
- [ ] ID adoption + limit-exception record + plan archive in the
  closing PR.

## Archive Criteria

Merged to `main` with the pathway live, the 13-item backfill published
and verified on Studio, `weekly-plan-2026-10-05.json` carrying every
remote video ID, and the 2026-10-03 week plan archived in the same PR.
