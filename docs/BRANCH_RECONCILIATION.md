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

- Current root worktree: `main` at `2a22230`, seven commits behind
  `origin/main`.
- Latest known trunk: `origin/main` at `0c245ec`.
- Root worktree has 45 file-level untracked entries under `.worktrees/`,
  `logs/`, `videos/`, and two `_tmp_prompts_*.json` files. These appear to be
  local operations/media state but remain protected until separately
  classified.
- No git stashes were present.
- Initial worktrees: root `main`, clean Shorts, clean Classics foundation, and
  dirty Persuasion pilot. The unification worktree was then created separately
  from `origin/main`. Persuasion code is now checkpointed; only its inventoried
  media remains untracked.

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
