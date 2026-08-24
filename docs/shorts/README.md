# English Listening Room Shorts

## Product

Shorts are the acquisition and experiment layer for the existing English
Listening Room shows. They are not a fourth long-form show.

The product promise is: **one useful English moment in 35 to 55 seconds** for
mobile-first A2-B1 adult learners. YouTube currently classifies eligible square
or vertical uploads up to three minutes as Shorts, but this acquisition pilot
deliberately keeps a 59-second hard ceiling. The first experiment compares
roughly 42-second and 54-second treatments instead of using 20-second clips.

The first controlled cycle contains twelve Shorts:

- four single-narrator micro stories;
- three listen-and-choose exercises;
- three situational dialogues;
- two narrated classic cliffhangers.

The portfolio deliberately keeps dialogue at 25%. Dialogue is used only when a
response, misunderstanding, or polite conversational move is the learning
point. The canonical contracts are:

- `configs/shorts/product.json` — product, quality, publishing, and experiment
  policy;
- `configs/shorts/pilot-2026-08.json` — the first twelve controlled briefs.

## Public controller

Use only `scripts/shorts.py` for routine Shorts work.

```powershell
$py = ".\.conda-env\python.exe"

& $py scripts/shorts.py plan
& $py scripts/shorts.py bootstrap
& $py scripts/shorts.py status
```

Every Short has one canonical ignored runtime directory:

```text
workspace/shorts/elr-s-001/
  manifest.json
  audio_manifest.json
  audio/
  video/
  reports/
  package/
```

Re-running `bootstrap` is idempotent. It will not overwrite an existing Short
with a different content hash. Published identity is never reused for revised
copy; revisions receive a new `shortId`.

## Production

### Visual direction and brand

Every production Short requires a story-specific generated editorial
background. Pure code gradients and generic technology motifs are not accepted
production visuals. Art direction is warm, mature, calm, and especially
welcoming to the channel's core women aged 25-44 without excluding other
learners.

Every upload also requires a dedicated 9:16 discovery cover. It reuses the
approved story illustration but adds a short editorial headline, format label,
CEFR level, and channel identity. The cover is uploaded as Studio metadata and
is never inserted as a static opening card: Shorts Feed performance still
depends on the live first frame and hook. Screenshot thumbnails are not the
production default.

Each manifest stores a visual brief and the approved background path. The
renderer combines that image with a restrained pan/zoom, the existing English
Listening Room avatar, a persistent wordmark, readable editorial caption card,
and one final CTA: `Subscribe for your next listening story.` Internal Short
IDs never appear in the viewer-facing composition. Missing imagery, logo, or
CTA fails preflight rather than falling back to a generic production design.

### 1. Preflight

```powershell
& $py scripts/shorts.py preflight --short elr-s-001
```

The pilot keeps every item private and reports a pending Related Video as a
warning until the channel video ID is assigned.

### 2. Render audio

Short audio reuses the project-local VoxCPM2 runtime and the proven Riley/Sam
references. A narrator maps to Riley; a real dialogue maps Riley and Sam to two
voices. The renderer loads the model once for the small Short batch, masters to
48 kHz mono near -14 LUFS, then replaces planned timings with measured WAV
timings.

```powershell
& $py scripts/shorts.py render-audio --short elr-s-001
```

For an isolated Git worktree, the controller automatically looks for model and
voice assets in the owning repository. Override only when necessary:

```powershell
$env:ELR_SHORTS_RUNTIME_ROOT = "H:\english-channel"
$env:ELR_SHORTS_DEVICE = "cuda"
```

The renderer uses the owning repository's global GPU lock, so a scheduled Short
cannot overlap a long-form VoxCPM or Whisper production job.

Measured delivery is preserved unless it crosses the pre-registered short/long
duration boundary. In that case only, mastering applies a bounded tempo
correction toward the planned duration and scales the caption timeline by the
same factor, so an experiment item cannot silently enter the wrong variant.

### 3. Render 9:16 video

```powershell
& $py scripts/shorts.py render --short elr-s-001
& $py scripts/shorts.py render-thumbnail --short elr-s-001
```

The data-driven Remotion composition is 1080x1920 at 30 fps. It has no long-form
intro or outro. Generated scene, hook, caption pages, question, answer, speaker
chips, brand treatment, CTA, and progress are driven by the manifest. Audio is
muxed after visual rendering so generated audio files never need to enter the
Remotion source tree.

For a silent visual smoke proof only:

```powershell
& $py scripts/shorts.py render --short elr-s-001 --preview
```

### 4. Package and quality gate

```powershell
& $py scripts/shorts.py package --short elr-s-001
```

Packaging fails before upload when duration, privacy, generated background,
dedicated thumbnail, brand, CTA, dimensions, stream presence, render duration
drift, or electrical hum are invalid. The audio gate measures stationary 50 Hz and 60 Hz harmonic
families against their local spectral floor; suspicious material is held for
review and a strong mains signature blocks packaging. A passing package writes
private-upload metadata and records `packaged` in the duplicate-safe
publication ledger.

## YouTube authorization and private upload

Create a Google OAuth desktop client with YouTube Data API v3 and YouTube
Analytics API enabled. Keep the downloaded client JSON outside Git, then run the
one-time interactive grant:

```powershell
$env:YOUTUBE_CLIENT_SECRETS = "C:\secure\youtube-client.json"
& $py scripts/shorts.py youtube-auth
```

The refresh token defaults to the ignored
`workspace/shorts/ops/youtube_token.json`. A scheduled run can refresh it
without opening a browser. Never commit either credential file.

If OAuth has not been provisioned yet, an authenticated Codex in-app browser
may use YouTube Studio as the operational fallback. Before uploading, verify
that Studio is signed in to `English Listening Room`, search the Shorts table
by title, and compare the local content key so an existing draft or scheduled
upload is never duplicated. Upload privately, set audience and metadata, set
and re-open the Related Video field to verify it persisted, wait for both
copyright and community checks, then schedule only within an explicitly
authorized publishing window. Record the returned YouTube ID in the local
publication ledger. A signed-out session, different channel, account check, or
ambiguous duplicate is a blocking condition. This fallback keeps operations
moving, but OAuth remains the preferred unattended path.

Upload is intentionally private and idempotent:

```powershell
& $py scripts/shorts.py upload-private --short elr-s-001
```

If a Short already has a YouTube ID, the command returns the existing ledger
entry instead of uploading a duplicate. Public release is a separate state
transition and stays disabled in `product.json` until the API project audit and
pilot acceptance are complete.

YouTube's documented Data API does not expose the Studio Related Video field.
The ledger therefore retains `relatedVideoId`, and the Studio step must set and
verify the related long-form video before scheduling. A missing value never
silently falls back to a description URL.

## Accelerated pilot cadence

The 2026-08 cold-start validation requested two Shorts per day at 08:00 and
20:30 Asia/Shanghai. It is a bounded learning proposal, not permanent adapter
authority or an assumption that upload volume causes growth. The request now
lives in `configs/channel/release-policy.json`; it must be reconciled against
actual YouTube state and receive channel-level approval before additional
scheduling. Each approved morning/evening pair changes one assigned variable
only, keeps unrelated creative decisions matched, and avoids two near-identical
topics on the same day.

Use the first three hours only for delivery and processing anomalies. At 24
hours, record engaged-view rate, viewed-versus-swiped behavior when available,
average percentage viewed, subscribers per 1,000 engaged views, interactions,
and related long-form uplift. Do not declare a winner until the configured
seven-day age and minimum sample gates are satisfied. If quality, copyright,
channel identity, or upload integrity fails, reduce cadence before relaxing a
quality gate.

## Analytics and experiments

API sync uses aggregate metrics for each ledger YouTube ID:

```powershell
& $py scripts/shorts.py sync-analytics
& $py scripts/shorts.py review
```

`engagedViews`, average percentage viewed, subscribers, and interactions are
preferred over raw Shorts starts/replays. Related-long-video traffic is not a
documented direct metric in this query; add `long_form_views` through a Studio
export when available.

CSV imports use this header:

```text
short_id,date,views,engaged_views,average_percentage_viewed,subscribers_gained,likes,comments,shares,long_form_views
```

```powershell
& $py scripts/shorts.py ingest-analytics --input C:\exports\shorts.csv
& $py scripts/shorts.py review --cutoff 2026-08-31
```

Each experiment requires at least three measured entries per variant and 200
combined engaged views per variant. A variant scales only when its normalized
score leads by at least 10% and neither engaged-view rate nor average percentage
viewed breaks the 10% guardrail. Otherwise the result remains `hold`; the
system never invents significance from one viral upload.

## Publication cadence

Shorts does not own channel cadence. `configs/channel/release-policy.json`
defines total capacity, authority, reservations, and time-bounded product
programs. This adapter may request preferred windows but cannot set a total
channel ceiling or schedule publicly when channel authority is disabled. Older
three-per-week and accelerated twice-daily schedules are historical hypotheses,
not simultaneous active policies.

## Autonomous operating loop

The intended scheduled tasks are:

1. Daily 09:00 — sync analytics, inspect upload/processing failures, and report
   exceptions only.
2. Monday 09:30 — update the backlog and lock the next three briefs according
   to 70% proven, 20% adjacent, and 10% exploratory allocation.
3. Monday/Wednesday/Friday 10:00 — produce the next scheduled private package;
   stop on any failed quality gate.
4. Tuesday/Thursday/Saturday — verify the private upload and Related Video,
   then schedule only after public publishing has been explicitly enabled.
5. Sunday 10:00 — write the weekly review and use its decisions to create the
   next plan.

The computer and desktop application must be running for local scheduled tasks.
Use an isolated worktree for code changes; generated runtime state remains
under ignored `workspace/shorts/`.

## Mandatory escalation

Routine planning, production, private upload, data collection, and review do
not require human approval after the pilot. Stop and notify the channel owner
for copyright or policy claims, account verification, two consecutive upload
failures, an identity/hash collision, missing analytics, new paid services,
brand-policy changes, or any public release while the autonomy gate is closed.

## Autonomy graduation gate

Enable unattended public scheduling only after all of the following are true:

- twelve consecutive Shorts complete without manual media repair;
- zero duplicate uploads;
- at least 95% scheduled-run success;
- every package has manifest, provenance hash, and passing media QC;
- four weekly reviews produce traceable next-cycle decisions;
- OAuth refresh works unattended;
- the API project can publish beyond private mode;
- no copyright or Community Guidelines incident occurs.
