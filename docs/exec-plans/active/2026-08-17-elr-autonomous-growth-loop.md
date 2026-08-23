# ELR Autonomous Growth Loop

## Goal

Turn the existing A/B/C production pipeline into an auditable product-growth
system that can plan, produce, publish, measure, experiment, review, and select
the next action with progressively greater autonomy.

The first outcome is a reliable baseline and one complete measured release
cycle. Full automatic public publishing is not the first milestone.

## Scope

Included:

- Reconcile the 63 completed local dialogue episodes with actual YouTube videos.
- Add a publication ledger and versioned schemas for metrics, experiments,
  decisions, and channel policy.
- Integrate YouTube Data and Analytics/Reporting APIs where supported.
- Define a Studio ingestion path for impressions, CTR, and native thumbnail
  experiments that are not covered by the public APIs.
- Add a canonical `channel_ops.py` controller and observable run state.
- Build scorecards, experiment assignment, decision memos, and rollback rules.
- Upload private, validate on platform, and later schedule only within an
  explicitly approved policy.
- Pilot the system on the dialogue portfolio before extending it to Classic
  Listening.

Non-goals for the first implementation slice:

- Deleting or bulk-editing existing YouTube videos.
- Automatically resolving copyright or policy disputes.
- Monetization changes or paid promotion.
- Rebranding the channel or permanently cancelling a series.
- Producing episode 022+ before the baseline decision.

## System Boundaries

Expected tracked code and documentation:

- `scripts/channel_ops.py`: public controller.
- `apps/worker-py/worker/channel_ops/`: schemas, repositories, services,
  providers, analytics normalization, experiments, decisions, and policy.
- `apps/worker-py/tests/test_channel_ops_*.py`: focused tests.
- `configs/channel_ops/`: non-secret channel policy, series roles, metric and
  decision rule versions.
- `docs/shows/AUTONOMOUS_GROWTH_SYSTEM.md`: product and operating contract.
- `docs/shows/strategy.md`, `ELR_YOUTUBE_PUBLISH.md`, and production Skills:
  operator guidance aligned with the new controller.

Private runtime state:

- `workspace/channel_ops/channel_ops.sqlite`.
- `workspace/channel_ops/raw/` immutable API and Studio snapshots.
- `workspace/channel_ops/reports/` scorecards and decision memos.
- OAuth client secrets and refresh tokens outside the repository.

## Status

- Owner: Codex primary agent.
- Last updated: 2026-08-23.
- State: signed-in Studio baseline complete; the first publication identity
  gate, JSON ledger, and six-slot release-plan validator are implemented.
- Current blocker: browser file-upload security prevents automated thumbnail,
  video, and subtitle selection in Studio. Polished English 019 title and
  description were corrected in place; its thumbnail still needs a permitted
  upload path or one manual file selection before verification can close.
- Baseline evidence:
  [`YOUTUBE_BASELINE_2026-08-17.md`](../../shows/YOUTUBE_BASELINE_2026-08-17.md).
- Intake note: the maintained ELR implementation is preserved at source head
  `d965773` and is being absorbed by `codex/elr-dialogue-intake`. Its
  `channel_ops` JSON ledger remains a Dialogue-era migration input; the shared
  channel control plane defined by `docs/YOUTUBE_OPERATING_SYSTEM.md` will
  become authoritative in a later slice.

## Plan

### Milestone 0: freeze, inventory, and acceptance criteria

- Pause new episode production beyond the existing bank.
- Define canonical episode identity independent of local folder naming.
- Inventory the 63 episode workspaces and reconcile backlog discrepancies.
- Channel ID and three podcast playlists are confirmed from Studio. Record them
  in the publication ledger and retain Asia/Shanghai as the operator timezone
  until audience-online data is sufficient.
- Obtain explicit policy approval before any remote correction, upload, or
  scheduling action. Read-only Studio analysis is already authorized.
- Add fixtures and acceptance criteria before live account access.

Observed publication state:

- 57 dialogue videos are published: 19 per podcast playlist.
- Episodes 020 and 021 are produced but unpublished for all three series.
- Daily Talk 019 and First Steps 019 are correct.
- Polished English 019 video `T7HIPOcdQFk` has the correct-duration media but
  originally had First Steps 019 title and description. The title and
  description were corrected on 2026-08-17; thumbnail verification remains
  open because automated local file selection was denied.

Implemented first slice:

- `scripts/channel_ops.py preflight` fingerprints MP4, thumbnail, subtitles,
  title, description, and YouTube metadata; it validates show, CEFR band,
  packaged copy, 2K resolution, duplicate titles/media, and idempotent resumes.
- `scripts/channel_ops.py validate-plan` validates both channel and same-series
  spacing, then preflights every release candidate.
- `workspace/channel_ops/publications.json` records the confirmed 019 video IDs
  and canonical MP4 fingerprints for Series A/B/C.
- All six 020/021 candidates pass the release plan dated 2026-08-18. Leaked
  Chinese chapter markers in First Steps 019/020/021 were fixed at the source;
  the published 019 description was corrected in Studio, and a CJK public-copy
  blocker now prevents recurrence.

### Milestone 1: data contracts and publication ledger

- Add versioned schemas for episodes, publications, snapshots, retention points,
  experiments, variants, assignments, decisions, production runs, and policy.
- Implement SQLite migrations and strict repository/service layering.
- Add deterministic artifact fingerprints and idempotent reconciliation.
- Import a user-reviewed mapping of existing published videos.
- Test missing IDs, duplicates, conflicting states, and atomic updates.
- Add hard tests for cross-series title/CEFR mismatches, duplicate title with a
  different MP4 fingerprint, metadata/media episode mismatch, and retry after a
  successful remote create.

### Milestone 2: read-only YouTube integration

- Add OAuth provider boundaries with least-privilege read scopes.
- Ingest channel/video metadata and targeted Analytics reports.
- Ingest retention curves per video and traffic-source reports.
- Store raw responses immutably and normalize derived metrics separately.
- Add a Studio-assisted import for impressions, CTR, returning/regular viewers,
  and native Test & Compare results when APIs do not expose the required field.
- Produce baseline scorecards without writing to the channel.

### Milestone 3: product diagnosis and experiment registry

- Classify episodes by series, learner moment, topic spine, packaging family,
  intro architecture, duration, and release context.
- Compute matched 7-day and 28-day baselines and confidence bands.
- Implement experiment eligibility, assignment, guardrails, and invalidation.
- Generate three compliant thumbnail variants and title-cohort candidates from
  one approved hypothesis.
- Write the first evidence-linked 28-day plan.

### Milestone 4: private publication automation

- Add resumable YouTube upload, metadata, caption, thumbnail, playlist, and
  disclosure operations behind a provider.
- Default to private and verify processing, resolution, captions, and metadata.
- Persist video IDs and every remote mutation before proceeding.
- Make retries idempotent and prohibit duplicate uploads by fingerprint.
- Keep public visibility and scheduling disabled until the user approves policy.

### Milestone 5: controlled Studio experiments and scheduling

- Use the signed-in browser only for Studio-only operations after authorization.
- Start and read native thumbnail Test & Compare experiments.
- Add an approved scheduling policy with cadence, windows, playlists, maximum
  concurrent tests, and rollback.
- Schedule from the existing episode bank and collect T+24h/T+7d/T+28d data.
- Stop automatically on authentication, policy, provenance, or data anomalies.

### Milestone 6: recommendation and closed-loop pilot

- Run four weeks in recommendation mode and compare agent decisions with user
  corrections.
- Promote to private preparation after the acceptance threshold is met.
- Pilot scheduling on one acquisition series for eight releases, unless the
  baseline selects a different series.
- Add automatic repackage/follow-up proposals and series allocation within
  approved bounds.
- Promote to closed-loop operation only after two stable 28-day cycles.

## Validation

Repository gates:

- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- `npm test`
- Focused `test_channel_ops_*.py` tests with plugin autoload disabled where
  required by the project-local Python environment.

Functional gates:

- 100% of published dialogue videos map to exactly one canonical episode.
- Every remote mutation is idempotent, logged, and reversible where supported.
- No secret appears in git, logs, reports, or error payloads.
- Raw analytics snapshots are immutable and derived metrics are reproducible.
- Retention and traffic-source queries reconcile with a reviewed Studio sample.
- A private upload passes video, thumbnail, caption, playlist, metadata, and
  processing verification without duplicate upload.
- An experiment cannot start without hypothesis, primary metric, guardrails,
  stop rule, and control/variant fingerprints.
- A decision memo can be regenerated from cited snapshots and rule version.
- Scheduling outside approved policy is rejected before any remote write.

## Risks And Decisions

1. The initial account diagnosis is complete, but a one-time browser read is
   not a reproducible data pipeline. Preserve snapshots and add scheduled
   read-only ingestion before automating decisions.
2. The YouTube APIs do not provide every Studio metric or native experiment
   control. Use API-first integration and a clearly separated Studio provider;
   do not scrape or simulate unsupported data.
3. API projects may be limited to private uploads until audited. Treat private
   upload as a valid first milestone, not a workaround to bypass policy.
4. Low channel volume makes single-video title tests unreliable. Pool matched
   cohorts, allow `inconclusive`, and use native concurrent thumbnail tests.
5. The mixed dialogue/audiobook channel may fragment audiences. Measure viewer
   overlap before recommending a split; do not infer it from intuition alone.
6. Synthetic voice and visual provenance must remain traceable. Uncertain
   disclosure or voice rights stop publication.
7. The system optimizes qualified watch time and loyalty, not CTR or raw output
   alone.
8. Publication identity is now a demonstrated safety risk. Remote writes remain
   disabled until the ledger, fingerprints, and idempotency checks pass.

## Archive Criteria

Move this plan to `completed/` only when:

- the publication ledger and analytics baseline cover all published dialogue
  videos;
- one private upload and one approved scheduled release complete end to end;
- at least one native thumbnail experiment and one cohort decision are recorded;
- the first T+28d decision memo is reproducible from stored evidence;
- autonomy level, policy, rollback, and escalation behavior are documented and
  tested;
- code, tests, docs, and production Skills pass repository gates.
