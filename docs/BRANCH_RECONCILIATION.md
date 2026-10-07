# Branch And Pipeline Reconciliation

## Purpose

This is the intake ledger for the 2026-08-17 YouTube operating-system
unification. It records what exists before any branch cleanup so committed and
uncommitted work can be preserved deliberately.

Disposition terms:

- `absorb`: merge or port the maintained implementation into trunk.
- `supersede`: a later implementation covers the capability; verify parity and
  retain history, but do not merge the stale branch wholesale.
- `preserve`: protect unique or uncommitted work until it has its own reviewed
  intake change.
- `retire`: delete only after merge/parity evidence and explicit cleanup
  authorization.

This document does not authorize branch deletion, worktree removal, remote
YouTube writes, or discarding generated assets.

## Repository Snapshot

- Current root worktree: `main` at `0cfd244`, equal to `origin/main` and
  clean. Refreshed 2026-10-07; the previous values (`main` at `2a22230`
  seven commits behind, `origin/main` at `0c245ec`) are superseded.
- Trunk now contains the intake chain (`92bbc57`, `8e39d68`, `9f4a7a3`,
  `dd9cdce`, `298cfa4`), the TTS provider migration (PR #11), the
  shared-types build-order fix (PR #12), and the worktree intake
  convergence (PR #13), which ended the `deploy-staging` failure streak
  that began on 2026-08-30.
- Eleven worktrees exist: the root, six under `.worktrees/`, two under
  `~/.codex/visualizations`, one detached sandbox on `D:`, and the
  Persuasion pilot worktree. Nine are clean; `.worktrees/douyin-migration`
  and `.worktrees/weekly-analytics` hold uncommitted doc and script edits;
  the Persuasion worktree holds only its inventoried untracked `public/`
  media.
- No git stashes were present (re-verified 2026-10-07).

Branch divergence counts below are relative to `origin/main` and have the form
`trunk-only / branch-only`.

## Intake Matrix

| Source | State | Valuable capability | Disposition | Intake requirement |
| --- | --- | --- | --- | --- |
| `main` (`2a22230`) | root worktree; `7 / 0`; local untracked runtime files | bootstrap platform and local models | preserve, then fast-forward | first classify root untracked files; do not use this stale tree as an integration base |
| `origin/main` (`0c245ec`) | latest known trunk | reviewed trunk and branch point for current work | canonical base | fetch/reconfirm before every intake PR |
| `feat/elr-series-scriptwriting-pipeline` (`d965773`) | source branch preserved; absorbed locally by `codex/elr-dialogue-intake` at `92bbc57` | dialogue research, topics, scripts, production, QC, packaging, publication preflight, channel baseline, autonomous-growth design | absorbed locally; PR pending | intake retains source history, removes the accidental gitlink, reconciles plans, isolates API tests from Redis/port side effects, and passes lint plus full Node/Python tests |
| `codex/shorts-pipeline-pilot` (`fb25a62`) | source branch/worktree preserved; absorbed locally by `codex/shorts-adapter-intake` at `8e39d68` | complete Shorts adapter, vertical render, QC, ledger, private upload, analytics, experiments, accelerated-pilot evidence | absorbed locally; PR pending | intake preserves newer ELR code, centralizes channel release capacity, requires external-state reconciliation, and passes focused plus full gates |
| `codex/classics-autonomous-foundation` (`741b999`) | source branch/worktree preserved; absorbed locally by `codex/classics-foundation-intake` at `9f4a7a3` | rights and policy schemas, append-only lifecycle, authority gates, audio-provider boundary | absorbed locally; PR pending | intake binds cadence to shared channel policy, retains authority level 0 and the audio blocker, and passes focused plus full gates |
| `codex/classics-persuasion-pilot` (`8d548d0`) | source code checkpointed; worktree retains only 33 untracked media files | EPUB ingestion, segmentation, audio/QC, aligned subtitles, packaging, Remotion visuals, tests, plans, generated pilot assets | production adapter absorbed locally at `dd9cdce`; media preserved | semantic intake retains foundation lifecycle/authority, binds release and audio status to shared policy, uses the shared GPU lock, fingerprints all 33 media files, and passes focused plus full gates |
| `feat/youtube-research-topic-selection` (`379ac46`) | clean source; all 43 paths classified in `LEGACY_PIPELINE_PARITY.md` | corpus collection, trend scoring, read-only browser research, competitor analysis | superseded locally at `298cfa4` | 19 identical, 2 evolved, 8 ported/recreated, 13 unsafe account scripts and 1 historical plan intentionally not ported |
| `feat/episode-audio-mastering` (`7615554`) | clean source; all 3 paths classified | mastering acceptance documentation and a focused test | superseded locally at `298cfa4` | test and durable contract ported; completed historical active plan omitted |
| `feat/audiobook-skill-opt-in-srt` (`9dce05c`) | clean source; all 41 paths classified | audiobook segmentation, subtitles, media, packaging, and operator guidance | superseded locally at `298cfa4` | 16 identical, 16 evolved, 7 ported, obsolete unlocked monitor and historical plan omitted |
| `agent/bootstrap-voxcpm-workflow` (`2a22230`) | `7 / 0`; same commit as stale local main | original monorepo/runtime bootstrap | retire candidate | retain through history; delete branch only after local main is current and cleanup is authorized |

## Capability Matrix

Legend: `implemented`, `partial`, `planned`, or `blocked` describes the source
branch/worktree, not current trunk.

| Capability | Dialogue / ELR | Shorts | Classics foundation | Persuasion worktree | Shared today |
| --- | --- | --- | --- | --- | --- |
| market/corpus research | implemented | briefs inherit local strategy | planned for book scoring | source/rights research implemented | no |
| topic/content selection | implemented backlog and scoring | controlled 12-item portfolio | rights/catalog policy | fixed book/chapter scope | no |
| script/source contract | implemented | implemented | source contract only | implemented EPUB/source fidelity | no |
| production orchestration | implemented, resumable | implemented | lifecycle foundation | implemented but uncommitted | no |
| GPU coordination | global PID lock | reuses global lock | policy only | reuses lock | partial lock, no scheduler |
| artifact provenance/QC | implemented | implemented | fail-closed gates | implemented, audio blocker open | no canonical identity |
| publication ledger | JSON preflight prototype | separate JSON ledger | event foundation | exported/local records | no, split brain |
| private upload | planned/prototype boundary | implemented, OAuth/Studio dependent | authority gate only | not authorized | no |
| analytics ingestion | baseline/manual plus planned store | CSV/API snapshot implementation | planned | planned | no |
| experiments | strong methodology, registry planned | implemented local review | policy contract | planned | no shared registry |
| retrospective/feedback | planned decision memos | weekly review implementation | planned | planned | no shared decision store |
| channel-wide cadence | dialogue policy only | conflicting Shorts policy values | product cadence only | chapter cadence only | no |
| autonomy levels | defined 0-4 | graduation gate | defined 0-3 | planned 0-3 | inconsistent |

## Confirmed Conflicts And Duplication

1. **Split publication truth.** Dialogue `channel_ops`, Shorts, and Classics
   each define a ledger or event model with incompatible identities and states.
2. **Conflicting cadence.** The Shorts config currently permits 14 Shorts and
   18 total channel uploads per week, while its README still contains an older
   three-Short/five-total cadence section. Dialogue has a separate spacing
   policy. A product adapter cannot decide total channel capacity.
3. **Competing Classics trees, resolved locally.** The clean foundation and
   Persuasion worktree both added `apps/worker-py/worker/classics/` from the same
   trunk base with different designs. Intake `dd9cdce` retained lifecycle and
   authority layers and ported production behavior rather than overwriting the
   tree.
4. **Shorts would regress ELR if merged as a replacement.** Compared with the
   newer ELR head, the Shorts tree lacks the newer `channel_ops` package,
   publication configs, autonomous-growth docs, and related tests.
5. **Legacy branches are partially copied forward.** Research and audiobook
   paths all exist in the newer ELR branch but many blobs differ. Commit
   ancestry alone cannot prove parity.
6. **Hardware coordination is a mutex, not scheduling.** The global PID lock
   protects the 8 GB GPU from overlap but has no queue, priority, fairness,
   reservation, capacity, or cross-worktree status model.
7. **Plans disagree with tree state.** Some completed work remains in active
   plans on older branches, while the ELR branch contains later plan moves not
   present on current trunk.
8. **Local worktree administration leaked into a branch.** The ELR branch
   tracks `.worktrees/shorts-pipeline-pilot` as a gitlink. `.worktrees/` must be
   ignored and the gitlink removed in the ELR intake change.

## Required Intake Order

1. Protect and classify all dirty/untracked roots; take no cleanup action.
   Completed locally in the foundation inventory; protections remain active.
2. Land the ELR dialogue branch as the maintained production baseline.
   Completed locally at `92bbc57`; it is not trunk until reviewed and merged.
3. Port the Shorts adapter onto that baseline and centralize channel cadence.
   Completed locally at `8e39d68`; it is not trunk until reviewed and merged.
4. Land the clean Classics autonomous foundation. Completed locally at
   `9f4a7a3`; it is not trunk until reviewed and merged.
5. Create a salvage commit for the initially dirty Persuasion worktree, then port it onto
   the foundation through reviewed domain-level conflict resolution. Completed
   locally with source checkpoint `8d548d0` and adapter intake `dd9cdce`; media
   remains protected by its SHA-256 inventory.
6. Audit research, mastering, and audiobook legacy branches against the
   resulting trunk; port only unique behavior/tests. Completed locally at
   `298cfa4`; all 87 paths have recorded dispositions and full gates pass.
7. Introduce the shared channel identity/data contracts and migrate ledgers.
8. Introduce shared resource, publication, analytics, experiment, and decision
   services one vertical slice at a time.
9. Retire branches and remove worktrees only after their disposition checks
   pass and cleanup is explicitly authorized.

## Per-Branch Acceptance Checklist

Before marking any source absorbed or superseded:

- record merge base, head SHA, clean/dirty status, and untracked files;
- compare trees and behavior, not only commit ancestry;
- preserve active plan state and archive only completed scope;
- ensure code, tests, configs, docs, and migrations move together;
- run encoding, docs, architecture, lint, unit, and focused domain checks;
- verify no credentials, private analytics, model weights, or generated media
  entered the commit accidentally;
- verify canonical IDs and runtime paths do not collide;
- confirm remote publishing authority did not change;
- write the final commit/PR reference into this ledger before cleanup.

## Protected Worktree Note

The Persuasion worktree no longer contains uncommitted product code. Commit
`8d548d0` protects its 43 code/test/config/doc paths; the unified adapter was
ported at `dd9cdce`, and the existing package lock already satisfies the exact
Remotion dependency set. The remaining 33 untracked files are 55,819,675 bytes
of PNG/WAV/JSON review media. Every path, size, and SHA-256 is recorded in
`docs/classics/PERSUASION_MEDIA_INVENTORY.md` and reverified after intake.

Those assets remain protected in place. Audio is still blocked by the
speech-coupled electronic texture, and visual/prompt provenance is not yet
complete. Their presence does not authorize deletion, bulk commit, upload, or
publication.

## Remote Branch Archive — 2026-08-24

Repository ownership and write access were confirmed for
`https://github.com/IvoryGate/english-channel.git`. A dry-run push succeeded and
left no test ref. All local code branches were then published without force,
deletion, or history rewriting, in dependency order:

1. Foundation and source records:
   `agent/bootstrap-voxcpm-workflow`,
   `feat/audiobook-skill-opt-in-srt`,
   `feat/episode-audio-mastering`,
   `feat/youtube-research-topic-selection`,
   `feat/elr-series-scriptwriting-pipeline`,
   `codex/youtube-operating-system-foundation`,
   `codex/shorts-pipeline-pilot`,
   `codex/classics-autonomous-foundation`, and
   `codex/classics-persuasion-pilot`.
2. Product intake records:
   `codex/elr-dialogue-intake`, `codex/shorts-adapter-intake`,
   `codex/classics-foundation-intake`, and
   `codex/persuasion-pilot-intake`.
3. Unified audit and control-plane chain:
   `codex/legacy-pipeline-parity`,
   `codex/channel-control-plane-foundation`,
   `codex/channel-resource-leases`, `codex/channel-reconciliation`, and
   `codex/channel-release-reservations`.

Every listed local branch now tracks its same-name `origin/*` ref with no
ahead/behind delta. Local `main` was not rewritten or pushed: it contains no
unique commit and remains behind the newer `origin/main`. Generated media,
logs, temporary prompt files, nested worktrees, and the protected Persuasion
review assets remain untracked and preserved in place under the documented
artifact rules. No pull request, merge, cleanup, or remote publication action
was performed by this archive operation.

## Reconciliation Pass — 2026-10-07

Trunk reference for this pass: `0cfd244`, after PR #11, PR #12, and PR #13.
Evidence per branch: ahead/behind against `main`, `git cherry` patch parity,
intake-chain ancestry, and worktree cleanliness. Plan of record:
`docs/exec-plans/active/2026-10-07-worktree-branch-reconciliation.md`.

| Source | Unique vs `main` | Evidence | Disposition | Action |
| --- | --- | --- | --- | --- |
| `codex/long-form-expansion` | +3 / -33 | all three patches already in `main` by patch id | retire candidate | delete only after authorization |
| `codex/shorts-rapid-3x3-2026-08-30` | +1 / -35 | its patch is already in `main` (merged through PR #9) | retire candidate | delete only after authorization |
| `codex/shorts-pipeline-pilot` | +4 / -90 | absorbed at `8e39d68`, which is in `main`; four pilot-week operational records superseded by trunk's weekly configs | retire candidate | delete only after authorization |
| `feat/audiobook-skill-opt-in-srt` | +5 / -118 | superseded at `298cfa4`; 41 paths classified in `LEGACY_PIPELINE_PARITY.md` | retire candidate | delete only after authorization |
| `feat/episode-audio-mastering` | +1 / -118 | superseded at `298cfa4`; 3 paths classified | retire candidate | delete only after authorization |
| `feat/youtube-research-topic-selection` | +4 / -118 | superseded at `298cfa4`; 43 paths classified | retire candidate | delete only after authorization |
| `intake-backup-20261006` | +3 / -15 | step-1 rollback point; equivalent content landed through PR #13 | retire candidate | delete only after authorization |
| `codex/channel-wide-youtube-ab` | +1 / -34 | experiments-tracking commit unique by patch parity; no earlier disposition in this ledger | preserve, absorb later | no action; intake when the experiments slice is ready |
| 18 zero-commit branches (including the three merged by PR #11-#13 and this PR's branch) | 0 | contained in `main` | retire candidate | delete after authorization; this PR's branch after its merge |
| `codex/classics-persuasion-pilot` | +1 / -111 | checkpoint `8d548d0` is not in `main`; adapter absorbed at `dd9cdce`; media SHA-256 inventoried | preserve, supersede | keep branch and worktree; close PR #5 |
| `codex/douyin-migration` | +1 / -19 | active plan `2026-09-12-douyin-migration` with two uncommitted doc edits | preserve | no action |
| `feat/weekly-analytics-loop` | +2 / -19 | unfinished analytics loop with one uncommitted script change | preserve, absorb later | no action; intake when the work is finished |

Worktree dispositions: keep the root, `.worktrees/douyin-migration`,
`.worktrees/weekly-analytics`, and the Persuasion worktree. Retire
`.worktrees/shorts-pipeline-pilot`, `.worktrees/shorts-rapid-3x3`,
`.worktrees/long-form-expansion`,
`.worktrees/youtube-operating-system-foundation`,
`classics-autonomous-worktree`, and the detached
`D:/CodexData/.codex/worktrees/b8b4/english-channel` at `27b17a7` — all six
verified clean — only after authorization.

Cleanup executed 2026-10-07 with the owner's explicit authorization
("delete local branches, keep remote"):

- Branches: 24 local branches deleted — the 7 retire candidates with
  unique commits and 17 zero-commit branches. No remote branch was
  deleted; `origin` retains every branch as the archive of the
  2026-08-24 publication. Remaining local branches: `main`, this
  reconciliation PR's branch, and the four preserve branches
  (`codex/classics-persuasion-pilot`, `codex/douyin-migration`,
  `feat/weekly-analytics-loop`, `codex/channel-wide-youtube-ab`).
- Worktrees: removed after inventory `classics-autonomous-worktree`
  (1.1 MB, no generated media) and the detached
  `D:/CodexData/.codex/worktrees/b8b4/english-channel` (139 MB, all 71
  `public/` files tracked). The four `.worktrees/` removals were
  interrupted by Windows filesystem errors after git had already
  unregistered them; per the owner's decision only their dependency
  directories were removed (573 MB reclaimed) and their generated
  content is preserved in place under the ignored `.worktrees/` as
  artifact archives. The registered worktree list went from 11 to 4:
  the root plus the three preserve worktrees.
- Incident: the interrupted removal deleted the never-committed
  `exports/youtube/persuasion/chapter-02-recovered/` media (62 MB).
  No copies exist on `H:`, `C:/.codex`, or `D:`; the content was never
  committed and is unrecoverable. The removal check relied on
  `git status` cleanliness, which does not cover ignored files, while
  the artifact rules protect exactly those files. Future worktree
  removals must inventory ignored artifacts first.
- Incident 2: the follow-up removal of the two orphaned `node_modules`
  directories followed Windows junctions into the root checkout,
  emptying the root `node_modules` and deleting tracked files under
  `apps/` and `packages/`. Every tracked file was restored byte-exact
  from the index with `git restore`, `npm install` rebuilt
  `node_modules`, and all untracked assets were verified intact
  (`workspace` 127 GB, `public/shorts`, `exports`, `artifacts`, `logs`,
  `videos`, `.venv` 4.4 GB, `.env.example`). Rule recorded: inventory
  junctions before any Windows `rm -rf` under a `node_modules` tree.
- PR #5 was closed 2026-10-07 with the supersede rationale in its
  comments; its head `8d548d0` remains preserved as a branch.
