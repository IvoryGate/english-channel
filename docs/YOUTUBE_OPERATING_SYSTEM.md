# English Channel YouTube Operating System

## Mission

Build an AI-operated YouTube channel that compounds audience knowledge and
creative quality through a scientific loop:

```text
observe market and audience
  -> choose portfolio opportunity
  -> register hypothesis and success criteria
  -> reserve release and production capacity
  -> design and produce
  -> verify and publish within authority
  -> collect immutable evidence
  -> decide and retrospect
  -> update priors, templates, backlog, and allocation
  -> repeat
```

The strategic horizon is one million subscribers. Subscriber count is a lagging
outcome, not a sufficient objective function. The operating system optimizes
durable audience value, learning velocity, and production efficiency under
quality, rights, safety, and trust constraints.

## One Channel, Multiple Product Lines

The channel is a portfolio. Each product line has a distinct audience job and
discovery surface, but all product lines compete for the same viewer attention,
release calendar, brand trust, hardware, API quota, and operating capacity.

| Product line | Portfolio job | Specialized behavior retained |
| --- | --- | --- |
| Dialogue long form | Reach, learner satisfaction, authority, and repeat listening across CEFR bands | topic selection, dialogue script contracts, multi-voice audio, 16:9 packaging, chapters |
| Shorts | Fast discovery and low-cost creative testing that can lead viewers into long form | mobile hooks, sub-minute pacing, 9:16 rendering, engaged-view metrics, related-video routing |
| Classic Listening | Library value, long sessions, playlist continuation, and evergreen audience depth | public-domain rights, source fidelity, single-narrator long-form audio, chapter/season lifecycle |

No product line owns channel policy. A product adapter proposes work and
executes media-specific steps; the channel control plane owns identity,
priority, resources, publication, evidence, experiments, and authority.

## Operating Principles

1. **Evidence before volume.** Existing inventory is an experiment bank. New
   production must answer a registered question or fill an approved portfolio
   need.
2. **One source of channel truth.** A remote video, local content item,
   experiment, and decision have one canonical identity across all pipelines.
3. **Specialize production, unify control.** Do not force a Short and an
   audiobook chapter through the same renderer. Do require both to use the same
   release, authority, resource, observation, and audit contracts.
4. **One causal variable.** Packaging, topic, intro, format, cadence, and
   audience targeting are not changed simultaneously in a causal test.
5. **Missing is not zero.** Delayed, unavailable, privacy-suppressed, and
   genuinely zero analytics are different states.
6. **Credentials are not authority.** The system may possess a token and still
   be forbidden to publish, schedule, delete, spend, or change channel policy.
7. **Files are artifacts, not state.** Lifecycle completion requires a durable
   event, fingerprint, and gate result; file existence alone proves nothing.
8. **Fail closed on identity, rights, provenance, quality, and policy.** Cadence
   never justifies bypassing a release gate.
9. **Prefer repair and reuse.** Repackage or learn from produced inventory
   before generating more content without evidence.
10. **Every decision is replayable.** Store observations and rule versions so a
    future agent can reproduce why an action was selected.

## Target Architecture

```text
Channel control plane
  Portfolio planner
  Canonical identity and lifecycle
  Experiment registry
  Release calendar and authority policy
  Resource scheduler
  Publication coordinator
  Analytics and evidence store
  Decision and retrospective engine
  Exception and notification service
        |
        +-- Dialogue adapter
        +-- Shorts adapter
        +-- Classic Listening adapter
        |
Providers
  YouTube Data / Analytics / Reporting
  audited Studio-only operations
  TTS / ASR / image / render engines
  local hardware / filesystem / secrets / clock
```

The Python control-plane domain follows the repository layering invariant:

```text
types -> schema -> repo -> service -> transport
                                  -> providers
```

Adapters depend on shared channel types and services. Shared channel code does
not import a concrete renderer, TTS engine, browser session, or product-specific
workspace.

## Canonical Domain Model

Minimum stable entities:

| Entity | Purpose |
| --- | --- |
| `product_line` | Dialogue, Shorts, or Classic Listening policy boundary |
| `series` | Audience promise, format, playlist, and cadence role |
| `content_item` | Stable episode, Short, chapter, or compilation identity |
| `topic` | Market opportunity, audience job, novelty, and source evidence |
| `creative_version` | Script, title, thumbnail, intro, structure, and prompt version |
| `artifact` | Fingerprinted audio, video, subtitle, image, metadata, and provenance |
| `production_run` | Inputs, engine versions, resource use, retries, gates, and outputs |
| `publication` | Remote video ID, playlist, visibility, schedule, processing, and mutation log |
| `observation` | Immutable raw or normalized metric at a declared window and source |
| `experiment` | Hypothesis, one primary variable, variants, assignment, rules, and outcome |
| `decision` | Evidence-linked action, confidence, limits, rule version, and rollback |
| `resource_lease` | Exclusive or capacity-based claim with heartbeat and recovery policy |
| `authority_policy` | Allowed action, scope, time window, limits, and escalation condition |

IDs must not be inferred from mutable titles or folder names. A content item can
have many creative versions and production runs but at most one active remote
publication for the same canonical media fingerprint unless a reviewed policy
explicitly permits another edition.

## Lifecycle

All product adapters map their internal states onto this channel lifecycle:

```text
discovered -> evaluated -> approved -> reserved -> producing -> qc_failed
  -> publish_ready -> uploaded_private -> platform_checked -> scheduled
  -> published -> observing -> reviewed -> keep | repackage | follow_up | retire
```

`qc_failed -> producing` is a repair loop. Any transition records actor,
timestamp, reason, policy version, idempotency key, input fingerprint, output
identity, and evidence references. Product-specific states may refine a shared
state but may not bypass it.

## Data And Evidence

Tracked files contain schemas, migrations, policies, metric definitions, and
test fixtures. Private runtime state lives under `workspace/channel/`:

```text
workspace/channel/
  channel.sqlite
  raw/                 immutable API, export, and Studio observations
  reports/             generated scorecards and retrospectives
  operations/          journals, checkpoints, and incident records
  leases/              recoverable local resource leases
  credentials/         ignored references only; secrets may live elsewhere
```

SQLite becomes the local transactional source of truth. Raw observations are
append-only. Derived tables and reports are rebuildable. Every import retains
source, collection time, metric window, timezone, dimensions, units, and
availability state.

Legacy Dialogue, Shorts, and Classics JSON ledgers remain readable during
migration. Import creates a collision report; it never silently selects one
ledger as correct.

## Channel-Level Metric System

### Outcome hierarchy

| Layer | Metrics | Decision |
| --- | --- | --- |
| Strategic outcome | subscribers, monthly/returning viewers, watch hours, revenue when applicable | Is the channel compounding toward the long-term goal? |
| Reach | registered impressions, Shorts starts, unique viewers, traffic-source mix | Is YouTube finding an audience for the promise? |
| Selection | CTR by surface, viewed-versus-swiped, engaged-view rate | Does packaging earn qualified attention? |
| Satisfaction | watch time, average duration/percentage, retention curve, negative feedback | Does the content fulfill the promise? |
| Loyalty | returning/regular viewers, playlist continuation, related-video flow | Does one view become a habit or session? |
| Conversion | subscribers per 1,000 qualified or engaged views, end-screen actions | Does attention become a durable relationship? |
| Efficiency | lead time, GPU minutes, intervention count, failure rate, cost per watch hour | Can the system scale sustainably? |
| Safety | rights/provenance gaps, claims, policy incidents, identity mismatches | Must autonomy stop or regress? |

The channel north-star diagnostic is **qualified watch hours per week**, split
by new and returning audience and constrained by subscriber conversion,
negative feedback, policy, and cost. For impression-based long form, retain
qualified watch minutes per 1,000 registered impressions. For Shorts, use
engaged views and average percentage viewed rather than treating every start as
equivalent. Product-specific metrics may not be combined without their surface
and denominator.

### Standard evidence windows

- `T+0`: platform, metadata, captions, playlist, thumbnail, visibility, and
  identity verification.
- `T+24h`: delivery and anomaly triage; never a final winner by default.
- `T+7d`: packaging, hook, intro, and early continuation review.
- `T+28d`: content, loyalty, conversion, and portfolio decision.
- Weekly: inventory, incidents, experiment health, and resource allocation.
- Monthly: product-line allocation and backlog priors.
- Quarterly: channel promise, audience segmentation, autonomy, and major format
  review.

Additional Classic Listening windows such as 6, 72, and 336 hours are supported
as diagnostics but do not replace the common comparison windows.

## Market Research And Topic Selection

Research produces evidence records, not free-form inspiration alone. Each topic
candidate includes:

- audience job or tension;
- demand evidence and collection time;
- competitor saturation and differentiation;
- product-line and series fit;
- novelty against the local and remote catalog;
- teachability or narrative value;
- packaging and visual potential;
- continuation and follow-up potential;
- rights, policy, and factual risk;
- estimated production resources and lead time;
- confidence and evidence expiry.

The portfolio planner selects a mix of proven, adjacent, and exploratory work
within a versioned policy. A candidate cannot enter production until it has a
canonical ID, intended audience outcome, experiment/control designation,
resource estimate, and release-slot eligibility.

## Experiment Contract

Every experiment is registered before the relevant artifact is produced or
published and contains:

- falsifiable hypothesis and decision owner;
- eligible audience, product line, surface, and observation window;
- control and variants with immutable fingerprints;
- exactly one primary changed variable;
- primary metric, guardrails, minimum evidence, maximum duration, and stop
  conditions;
- contamination and invalidation rules;
- outcome of `scale`, `hold`, `repair`, `follow_up`, `retire`, or
  `inconclusive`;
- confirmation requirement before a winning template becomes a default.

Native concurrent YouTube thumbnail experiments are preferred where supported.
Sequential title and format comparisons are matched-cohort evidence and must
not be presented as laboratory causality. Cadence changes are channel-level
experiments because they affect every product line.

## Resource Scheduling

The current 8 GB GPU constraint starts with one exclusive heavy-GPU lease. The
shared scheduler later models:

| Resource | Initial policy |
| --- | --- |
| CUDA/VRAM | one VoxCPM, Whisper, or NVENC-heavy lease at a time |
| CPU/RAM | bounded slots with per-job estimates and minimum free-memory gate |
| Disk | reserve expected output plus safety margin before rendering |
| Network upload | one resumable upload mutation at a time |
| YouTube/API quota | provider-reported budget and retry-after enforcement |
| Studio browser | one audited signed-in mutation session at a time |
| Human review | explicit review task with deadline; never simulated approval |
| Release calendar | channel-wide slot reservation before adapter production |

Every job declares priority, deadline, estimated duration, required resources,
retry budget, checkpoint strategy, preemptibility, and artifact root. Initial
priority order is safety/identity repair, release-critical work, scheduled
measurement, ready-buffer production, then exploration. Aging prevents a
healthy lower-priority pipeline from starving indefinitely.

Leases include owner, process identity, heartbeat, expiry, intent hash, and
recovery action. A stale process may release a lease only after liveness and
checkpoint verification. Deleting a lock file is not a scheduler API.

## Publication And Authority

The channel applies one authority ladder to every product adapter:

| Level | Allowed behavior | Promotion evidence |
| --- | --- | --- |
| 0 · Reconcile | read local/remote state and build the ledger; no writes | complete identity mapping and baseline |
| 1 · Recommend | propose portfolio, experiments, and schedule | four reviewed cycles without material correction |
| 2 · Prepare | research, produce, package, and upload private | consecutive QC/platform passes and idempotent recovery |
| 3 · Schedule | schedule within approved windows and limits | stable scheduled runs with no policy breach |
| 4 · Closed loop | choose routine next actions and bounded allocation | two complete 28-day auditable cycles |

Authority is scoped by product line, action, time, rate, and destination. It
automatically drops after identity collision, unexplained metric loss, missing
evidence, repeated production failure, provenance uncertainty, account change,
claim, or policy incident.

The following always require explicit user authority: deletion or unlisting,
copyright or policy disputes, credential/security changes, monetization, paid
spend, channel rename, material rebranding, new public format, or operation
outside an approved policy window.

## Operating Cadence

### Daily

- reconcile running jobs, resource leases, uploads, platform processing, and
  due observations;
- act automatically only on safe retries and approved routine steps;
- emit exception reports for blocked gates rather than noisy success updates.

### Weekly

- refresh market and audience evidence whose freshness window expired;
- review inventory and channel release capacity;
- inspect experiment health and contamination;
- lock the next portfolio plan with controls and resource reservations;
- write a decision memo stating what changed, what will be tested, what remains
  fixed, and when the decision will be revisited.

### Monthly and quarterly

- compare product-line contribution to reach, satisfaction, loyalty,
  conversion, and cost;
- reallocate capacity only from sufficient evidence;
- review audience overlap before splitting or combining channel formats;
- revisit the channel promise and autonomy policy without rewriting past
  experiment definitions.

## Canonical Command Surface

The target routine interface is one channel controller; product controllers
remain adapter/debug surfaces. The identity-foundation commands marked below
are implemented; the remaining commands describe later slices:

```powershell
$py = ".\.conda-env\python.exe"

& $py scripts/channel.py inventory
& $py scripts/channel.py init
& $py scripts/channel.py status
& $py scripts/channel.py collisions
& $py scripts/channel.py import-dialogue --source <ledger.json>
& $py scripts/channel.py import-shorts --source <ledger.json>
& $py scripts/channel.py import-classics --source <operations-directory>

# Target commands not implemented by the identity foundation:
& $py scripts/channel.py reconcile
& $py scripts/channel.py plan --horizon 28d
& $py scripts/channel.py resources status
& $py scripts/channel.py run --next
& $py scripts/channel.py publish preflight --item <id>
& $py scripts/channel.py publish upload-private --item <id>
& $py scripts/channel.py publish schedule --approved-policy
& $py scripts/channel.py analytics sync
& $py scripts/channel.py experiments review
& $py scripts/channel.py retrospective weekly
& $py scripts/channel.py retrospective 28d
```

Until real legacy imports and collision review are complete, existing product
commands are not interchangeable and their local ledgers remain migration
inputs rather than channel truth. See
[`CHANNEL_CONTROL_PLANE.md`](CHANNEL_CONTROL_PLANE.md) for the implemented
boundary.

## Million-Subscriber Roadmap

Growth milestones are evidence gates, not promises tied to a calendar date:

1. **Truth:** reconcile all published inventory, analytics, audiences, costs,
   and incidents.
2. **Repeatability:** demonstrate that at least one acquisition path and one
   satisfaction/loyalty path work across multiple controlled releases.
3. **Portfolio fit:** prove how Shorts, dialogue, and evergreen listening do or
   do not move viewers between surfaces.
4. **Operational scale:** maintain quality and experiment integrity while
   increasing throughput through better scheduling, reuse, and provider choice.
5. **Audience compounding:** grow returning and regular viewers, playlist
   continuation, and subscriber conversion rather than relying on isolated
   viral events.
6. **Format expansion:** add or retire public formats only after the control
   plane can measure incremental audience value and cannibalization.

The active implementation sequence and archive gates live in
`docs/exec-plans/active/2026-08-17-youtube-operating-system-unification.md`.
The source-branch intake ledger lives in `docs/BRANCH_RECONCILIATION.md`.
