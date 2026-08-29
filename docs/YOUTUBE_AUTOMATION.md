# API-First YouTube Release Automation

Routine uploads and scheduling use `scripts/youtube.py`. The controller validates
local QC, media identity, channel identity, metadata, artifacts, and future
schedule before any remote write. It uploads privately, records the returned
video ID immediately, adds the thumbnail, English captions and playlist, waits
for YouTube processing, then applies and verifies `status.publishAt`.

The ignored crash-recovery journal is
`workspace/channel/youtube/release-journal.json`. Once a video ID is recorded,
a retry reuses it and will not upload the same content again. If a process dies
after starting an upload but before recording the returned ID, the next write
is blocked as uncertain; inspect recent private uploads and use `adopt` instead
of risking a duplicate. A changed media fingerprint or reused YouTube ID is a
blocking collision.

## One-time OAuth setup

Create a Google OAuth desktop client for a project with YouTube Data API v3 and
YouTube Analytics API enabled. Keep the downloaded JSON outside Git.

```powershell
$py = ".\.conda-env\python.exe"
$env:YOUTUBE_CLIENT_SECRETS = "D:\secure\youtube-client.json"
& $py scripts/youtube.py auth
```

The refresh token defaults to the ignored
`workspace/channel/youtube/youtube_token.json`. Set `YOUTUBE_TOKEN_PATH` only
when an explicit external secret location is required. Later runs refresh the
token without interactive sign-in.

The OAuth identity must resolve to exactly channel
`UC9QpAkVpv8l1ZQ3X4UtU37A`. Any mismatch stops before mutation. Google may keep
uploads from an unverified API project private until the project passes its
required audit; the controller does not bypass that restriction.

## Weekly release workflow

The release manifest is the desired-state input. Its `weeklyPlan` link is
validated before any remote operation, so a missing content ID or changed time
cannot silently drift from the owner-approved calendar. It may reuse each production
pipeline's `youtube.json` through `metadataFile`, or use explicit `titleFile`
and `descriptionFile`. An already-created Studio upload can be declared with
`youtubeVideoId`; `assetsAlreadySet` is allowed only after the thumbnail and
captions were actually verified.

```powershell
$manifest = "configs\channel\youtube-release-2026-08-31.json"

# Read-only: validate every file, schedule, QC state, and media fingerprint.
& $py scripts/youtube.py --manifest $manifest preflight

# Read-only by default: report what is ready without remote writes.
& $py scripts/youtube.py --manifest $manifest sync

# Upload missing items privately and apply upload assets.
& $py scripts/youtube.py --manifest $manifest sync --apply-upload

# After processing succeeds, apply and verify all approved publication times.
& $py scripts/youtube.py --manifest $manifest sync --apply-upload --apply-schedule

# Inspect resumable state or one item.
& $py scripts/youtube.py status
& $py scripts/youtube.py status --content-id content:series_a:episode_022
```

Use `--content-id` on `sync` for an isolated retry. The controller leaves an
item in `awaiting_processing` when YouTube has not finished ingesting it; rerun
the same command later. It never schedules a failed/rejected upload or a local
package whose `qcStatus` is not `pass`.

## Browser fallback boundary

Routine title, description, private upload, thumbnail, captions, playlist and
publication time are API operations. Use Studio only when:

- OAuth or a documented API operation fails after a safe retry;
- YouTube changes an API contract or requires account verification;
- copyright or Community Guidelines checks need human-visible inspection;
- a native thumbnail experiment is required; or
- a Short needs Studio's Related Video field, which the public Data API does
  not expose.

Any Studio fallback must preserve the manifest content ID and record the real
video ID back into the manifest/journal before another automated retry.
