# YouTube Operating System Unification

## Goal

Turn the repository's dialogue, Shorts, and Classic Listening pipelines into
one channel operating system that can research the market, choose portfolio
investments, produce content, allocate local hardware, publish safely, measure
results, run controlled experiments, write retrospectives, and feed evidence
back into the next planning cycle.

The long-term product objective is a sustainable path to one million YouTube
subscribers. The engineering objective is not one universal media renderer. It
is one control plane, one evidence model, and one authority policy over
specialized content pipelines.

## Scope

Included:

- Establish the channel-level product, metric, experiment, resource, identity,
  publication, and autonomy contracts.
- Reconcile every live branch and worktree as `absorb`, `supersede`, `preserve`,
  or `retire` before branch cleanup.
- Preserve and later commit the unfinished Persuasion worktree without mixing
  it into an unrelated branch.
- Adopt one canonical channel controller and durable operations store.
- Keep dialogue long form, Shorts, and Classic Listening as product adapters
  behind shared planning, scheduling, resource, publication, analytics, and
  decision services.
- Migrate local JSON ledgers into a versioned shared store while retaining raw,
  immutable source snapshots and artifact provenance.
- Enforce channel-wide upload capacity, experiment isolation, GPU scheduling,
  authority levels, stop rules, and auditability.
- Update code, tests, and documentation together in a sequence of short-lived
  branches and pull requests.

Explicit non-goals for the first slice:

- Deleting branches, worktrees, generated assets, or uncommitted files.
- Publishing, editing, deleting, or scheduling YouTube content.
- Combining specialized renderers into one implementation.
- Changing the channel promise or cancelling a content line before the shared
  analytics model can compare portfolio roles.
- Claiming that the current repository already implements the target control
  plane.

## System Boundaries

Target shared surfaces:

- `docs/YOUTUBE_OPERATING_SYSTEM.md`: channel product and operating contract.
- `docs/BRANCH_RECONCILIATION.md`: source-of-truth inventory and intake order.
- `configs/channel/`: versioned channel policy, authority, resource capacity,
  metric definitions, and release constraints.
- `apps/worker-py/worker/channel/`: strict
  `types -> schema -> repo -> service -> transport` control-plane domain.
- `apps/worker-py/worker/channel/providers/`: YouTube, analytics, Studio,
  scheduler, secrets, notification, and hardware adapters.
- `scripts/channel.py`: the only routine channel-level command surface.
- `workspace/channel/`: ignored database, immutable observations, reports,
  leases, and operation journals.

Product adapters retained behind the control plane:

- Dialogue long form: `scripts/elr.py`, `workspace/shows/`, and related media
  tooling.
- Shorts: `scripts/shorts.py`, `apps/worker-py/worker/shorts/`, and
  `workspace/shorts/` during migration.
- Classic Listening: `scripts/classics.py`,
  `apps/worker-py/worker/classics/`, and `workspace/classics/` during
  migration.

## Status

- Owner: Codex primary agent.
- Branch: `codex/youtube-operating-system-foundation` from `origin/main` at
  `0c245ec`.
- Last updated: 2026-08-23.
- State: Phase 0 inventory and protection rules are complete. The ELR dialogue
  pipeline is absorbed locally at `92bbc57` with full gates passing; it is not
  trunk until reviewed and merged. The next product intake after that merge is
  Shorts, followed by the clean Classics foundation.
- Safety hold: no branch or worktree may be deleted until its disposition is
  recorded and unique commits plus uncommitted files are preserved.
- Publication hold: this plan grants no new YouTube write authority.
- Foundation validation: encoding, documentation-index, and architecture checks
  pass and were reconfirmed on 2026-08-23. No production code or runtime state
  changed in this slice.

## Plan

### Phase 0: inventory and protect

- Record every local and remote branch, divergence point, worktree, active
  plan, unique capability, and uncommitted file set.
- Tag each source as `absorb`, `supersede`, `preserve`, or `retire` with an
  explicit prerequisite and verification command.
- Add `.worktrees/` to the repository ignore policy so local worktree
  administration cannot be committed as a gitlink again.
- Preserve the Persuasion worktree until its code, tests, plans, and selected
  production assets are committed on its own branch.

Exit: the reconciliation document is reviewable and no unique work is
unaccounted for.

### Phase 1: land proven product pipelines

- Rebase and merge the current ELR dialogue branch into latest `main` after
  removing the accidental `.worktrees/shorts-pipeline-pilot` gitlink.
- Merge Shorts as an adapter without removing the newer ELR channel-operations
  files; resolve cadence and package-manifest conflicts against channel policy.
- Merge the clean Classic Listening foundation before porting the unfinished
  Persuasion production implementation.
- Reconcile the older research, mastering, and audiobook branches file by file;
  do not merge whole stale branches when later work already contains their
  behavior.

Exit: current trunk contains all accepted specialized pipelines, their tests,
and accurate active/completed plans.

### Phase 2: shared contracts and source of truth

- Define stable IDs for channel, product line, series, content item, artifact,
  production run, publication, metric observation, experiment assignment,
  decision, and resource lease.
- Introduce versioned SQLite migrations and repositories. Store raw YouTube/API
  captures immutably and make derived views reproducible.
- Import dialogue, Shorts, and Classics ledgers with collision reports and
  source identifiers; never silently overwrite domain state.
- Centralize artifact fingerprints and remote video identity so one media hash
  cannot create duplicate uploads across adapters.

Exit: every local item and remote video resolves to one canonical identity and
one auditable lifecycle.

### Phase 3: channel planner and resource scheduler

- Build a portfolio planner that consumes demand, audience, performance,
  experiment, inventory, cadence, and production-cost evidence.
- Replace the process-local GPU lock with a lease-based resource scheduler for
  GPU/VRAM, CPU, RAM, disk, network, API quota, and human review capacity.
- Preserve one-heavy-GPU-job-at-a-time as the initial 8 GB safety policy while
  allowing CPU research, metadata, and approved visual preparation in
  parallel.
- Reserve release slots and experiment cells at channel level before a product
  adapter starts production.

Exit: competing pipelines cannot oversubscribe hardware, release capacity, or
experiment traffic.

### Phase 4: publication and analytics control plane

- Implement provider-based, idempotent private upload, metadata, captions,
  thumbnail, playlist, processing, and status reconciliation.
- Enforce one authority ladder and one channel-wide policy; credentials never
  imply permission.
- Ingest YouTube Data/Analytics evidence and audited Studio-only observations
  into immutable snapshots with explicit missing/suppressed/delayed states.
- Schedule T+0, T+24h, T+7d, and T+28d reviews, with product-specific windows
  only where justified.

Exit: the same publication and observation rules apply to every content line.

### Phase 5: experiment, retrospective, and optimization loop

- Register hypotheses before production and limit each causal test to one
  primary changed variable.
- Use metric contracts appropriate to surface while retaining a channel-level
  value model: qualified watch time, returning audience, subscriber
  conversion, continuation, and cost.
- Generate evidence-linked weekly and 28-day decisions with `scale`, `hold`,
  `repair`, `follow_up`, or `retire` outcomes and explicit confidence.
- Feed accepted decisions into topic scores, packaging priors, content
  templates, cadence, and resource allocation without rewriting history.

Exit: one complete measured cycle selects the next portfolio actions from
stored evidence and can be replayed.

### Phase 6: progressive autonomy

- Run read-only reconciliation, recommendation, private preparation,
  scheduling, and bounded closed-loop operation as separate authority levels.
- Promote only after published acceptance gates; automatically reduce
  authority on policy, identity, data, provenance, or quality incidents.
- Keep deletion, rights disputes, monetization, paid spend, credentials,
  material rebranding, and new public formats behind explicit user approval.

Exit: routine operations are autonomous within policy and exceptions are
specific, actionable, and auditable.

## Validation

Every slice must run the repository gates appropriate to its changes:

- `npm run check:encoding`
- `npm run check:docs`
- `npm run check:architecture`
- `npm run lint`
- `npm test`
- Focused Python tests for each changed domain.

System acceptance gates:

- No unique committed or uncommitted branch content is lost during intake.
- One canonical ID maps each artifact and remote video to exactly one content
  item.
- Remote mutations and heavy-resource work are idempotent and lease-protected.
- Channel and per-series cadence constraints cannot contradict one another at
  runtime.
- Experiments cannot start without a hypothesis, primary metric, guardrails,
  minimum evidence, stop rule, and assignment fingerprint.
- Missing or privacy-suppressed analytics never become numeric zero.
- Every decision cites immutable observations, rule versions, and artifact
  fingerprints.
- Publication above configured authority fails closed.

## Risks And Decisions

1. The repository currently has multiple valid domain designs but no single
   channel source of truth. Preserve adapter specialization and unify control,
   evidence, and policy.
2. `main` is behind `origin/main`, while several feature branches diverged
   before the merge commit. Intake must use tree/content comparison, not branch
   names or commit counts alone.
3. The Shorts branch lacks newer ELR channel-operations files in its tree;
   merging it as a replacement would regress publication safeguards.
4. The Persuasion worktree contains substantial uncommitted code and media.
   It is a protected intake source until a dedicated salvage commit exists.
5. The clean Classics foundation and unfinished Persuasion implementation both
   add `worker/classics/` with different contracts. Land and adapt them in that
   order; do not overwrite either tree wholesale.
6. Local JSON ledgers are useful prototypes but create split-brain publication
   and analytics state. Migrate with provenance, then make the shared store
   authoritative.
7. The current GPU lock prevents overlap but offers no fairness, priorities,
   reservations, or visibility. The replacement begins conservatively with one
   exclusive heavy-GPU lease.
8. A one-million-subscriber goal is a strategic horizon, not an optimization
   metric. The system must optimize measurable audience value and learning
   velocity without sacrificing policy, rights, quality, or trust.

## Archive Criteria

Move this plan to `completed/` only when:

- accepted dialogue, Shorts, and Classics capabilities are merged into trunk;
- all legacy branches and worktrees have a recorded, verified disposition;
- the shared identity, resource, publication, analytics, experiment, decision,
  and authority services are the source of truth;
- each product adapter completes at least one end-to-end private publication
  rehearsal through the shared control plane;
- one channel-level T+28d retrospective produces the next portfolio plan;
- recovery, escalation, secrets, and data-provenance behavior are documented
  and tested; and
- no routine operation depends on an undocumented branch, manual ledger, or
  untracked source file.
