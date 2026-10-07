# Worktree And Branch Reconciliation

## Goal

Give every legacy branch and worktree a disposition backed by evidence
(ancestry, patch parity, and the intake ledger), execute only the cleanup
that the ledger's rules and an explicit authorization allow, and bring
`docs/BRANCH_RECONCILIATION.md` back to a current snapshot.

## Scope

Included:

- Refresh the stale snapshot in `docs/BRANCH_RECONCILIATION.md` (it still
  records `main` at `2a22230` and `origin/main` at `0c245ec`) with the
  post-PR-11/12/13 state at `0cfd244`.
- Record per-branch evidence: ahead/behind against `main`, `git cherry`
  patch parity, intake-chain ancestry, worktree cleanliness.
- Classify every branch and worktree as absorb, supersede, preserve, or
  retire candidate, with the evidence written into the ledger's intake
  matrix.
- Execute cleanup (local and remote branch deletion, worktree removal,
  closing stale PR #5) only for the retire-candidate list and only after
  explicit authorization, recording each result in the ledger.
- File follow-ups for preserve and absorb-pending items instead of acting
  on them.

Explicit non-goals:

- No deletion or removal of preserve items: the Persuasion checkpoint
  branch, its worktree, and the SHA-256 inventoried media; the douyin
  migration worktree with its uncommitted plan edits; the
  weekly-analytics worktree with its uncommitted script change.
- No wholesale merge of any stale branch; no history rewrite; no force
  push.
- No YouTube, credential, or remote-platform operation.
- No discarding of generated media, logs, or temporary files.

## System Boundaries

- `docs/BRANCH_RECONCILIATION.md` (the ledger) and `docs/exec-plans/*`
- Local refs: 11 branches with unique commits, 18 with none, 11 worktrees
- Remote refs on `origin` and pull request #5

## Status

- Owner: OpenCode agent.
- Started: 2026-10-07.
- State: completed 2026-10-07. Ledger refreshed, dispositions evidenced,
  the authorized cleanup executed and recorded (with both incidents),
  PR #5 closed, and this plan archived in PR #14, the PR that completes
  its scope. Absorb-later items (`feat/weekly-analytics-loop`,
  `codex/douyin-migration`, `codex/channel-wide-youtube-ab`) remain
  preserve dispositions for their own future intake.

## Plan

1. Refresh the ledger snapshot and write the evidence-backed disposition
   matrix (the first commit of this PR).
2. Request explicit cleanup authorization for the retire-candidate list.
3. After authorization: delete the authorized branches locally and on
   `origin`, remove the authorized worktrees, and close stale PR #5 with
   the supersede rationale.
4. Record the final refs in the ledger, run the gates, and archive this
   plan in the PR that completes its scope.

## Disposition Matrix (2026-10-07)

Evidence: ahead/behind against `0cfd244`, `git cherry` patch parity, and
intake-chain ancestry (`92bbc57`, `8e39d68`, `9f4a7a3`, `dd9cdce`,
`298cfa4` are all in `main`; `8d548d0` is not).

Retire candidates (no content beyond what `main` already holds):

- `codex/long-form-expansion` (+3/-33): all three patches already in
  `main` by patch id.
- `codex/shorts-rapid-3x3-2026-08-30` (+1/-35): its patch is already in
  `main` (merged through PR #9).
- `codex/shorts-pipeline-pilot` (+4/-90): capability absorbed at
  `8e39d68`, which is in `main`; the four remaining commits are
  pilot-week operational records superseded by trunk's weekly configs.
- `feat/audiobook-skill-opt-in-srt` (+5/-118),
  `feat/episode-audio-mastering` (+1/-118), and
  `feat/youtube-research-topic-selection` (+4/-118): superseded at
  `298cfa4` with per-path dispositions recorded in
  `LEGACY_PIPELINE_PARITY.md`.
- `intake-backup-20261006` (+3/-15): the step-1 rollback point; its
  content landed through PR #13 as the nine-way split.
- 18 branches with zero unique commits against `main`, including the
  three merged by PR #11, #12, and #13 and this PR's own branch (whose
  deletion waits for this PR's merge).

Preserve (in flight or protected media):

- `codex/channel-wide-youtube-ab` (+1/-34): unique experiments-tracking
  commit with no earlier ledger disposition; found during execution and
  added to this matrix. Absorb later through its own intake.
- `codex/douyin-migration` (+1/-19) with two uncommitted doc files in
  `.worktrees/douyin-migration`.
- `feat/weekly-analytics-loop` (+2/-19) with one uncommitted script in
  `.worktrees/weekly-analytics`.
- `codex/classics-persuasion-pilot` (+1/-111, checkpoint `8d548d0` is not
  in `main`) and its worktree holding the inventoried `public/` media.

Supersede:

- PR #5 (head `8d548d0`, opened 2026-08-24): the production adapter was
  absorbed at `dd9cdce`; closed 2026-10-07 with the rationale in its
  comments, with the checkpoint branch kept as the history record.

Worktree disposition (11 total):

- Keep: the root worktree, `.worktrees/douyin-migration`,
  `.worktrees/weekly-analytics`, and the Persuasion worktree.
- Retire candidates, all verified clean: `.worktrees/shorts-pipeline-pilot`,
  `.worktrees/shorts-rapid-3x3`, `.worktrees/long-form-expansion`,
  `.worktrees/youtube-operating-system-foundation`,
  `classics-autonomous-worktree` under `~/.codex/visualizations`, and the
  detached `D:/CodexData/.codex/worktrees/b8b4/english-channel` at
  `27b17a7`.

## Execution Record — 2026-10-07

- Worktrees: `classics-autonomous-worktree` (1.1 MB, no generated media)
  and the detached `D:` sandbox (139 MB, all 71 `public/` files tracked)
  were inventoried first and then removed cleanly. The four
  `.worktrees/` removals (`shorts-pipeline-pilot`, `shorts-rapid-3x3`,
  `long-form-expansion`, `youtube-operating-system-foundation`) were
  interrupted by Windows filesystem errors after git had already
  unregistered them. Per the owner's decision only their dependency
  directories were removed (573 MB reclaimed) and their generated
  content stays in place under the ignored `.worktrees/` as artifact
  archives. The Persuasion, douyin, and weekly-analytics worktrees were
  never touched; the registered worktree list went from 11 to 4.
- Incident: the interrupted removal deleted the never-committed
  `exports/youtube/persuasion/chapter-02-recovered/` media (62 MB
  recovered chapter MP4, SRT, QC frames and audio, three JSON records
  from the 2026-08-31 recovery). Copies were searched for on `H:`,
  `C:/.codex`, and `D:`, and none exist; the content was never
  committed, so it is unrecoverable. Root cause: the removal check used
  `git status` cleanliness, which does not cover ignored files, while
  the ledger's artifact rules protect exactly those files. Future
  worktree removals must inventory ignored artifacts first.
- Branches: 24 local branches deleted under the explicit authorization
  (7 retire candidates with unique commits, 17 zero-commit). No remote
  branch was deleted; `origin` keeps every branch as the archive. Six
  local branches remain: `main`, this PR's branch, and the four
  preserve branches.
- Incident 2: the background removal of the two orphaned `node_modules`
  directories followed Windows junctions out of their targets. Because
  npm's workspace entries inside them resolved into the root checkout,
  the removal emptied the root `node_modules` and deleted tracked files
  under `apps/` and `packages/` in the root worktree. Recovery: every
  tracked file was restored byte-exact from the index with
  `git restore -- apps packages`, `npm install` rebuilt the root
  `node_modules`, and all untracked assets were verified intact
  afterwards (`workspace` 127 GB, `public/shorts`, `exports`,
  `artifacts`, `logs`, `videos`, `books`, `reference`, `.venv` 4.4 GB,
  `.env.example`). Rule recorded: never `rm -rf` a `node_modules` tree
  on Windows without inspecting its junctions first.
- PR #5 closed with the supersede rationale; `8d548d0` remains
  preserved as a branch.

## Validation

- Every disposition cites ahead/behind counts, a `git cherry` result, or
  intake-chain ancestry verified against `main`.
- Cleanup executes only after explicit authorization and only for the
  retire-candidate list; each deletion and removal is recorded in the
  ledger with its date and result.
- `npm run lint` and `npm run test` stay green on this PR branch.
- Results 2026-10-07: registered worktrees 11 → 4, local branches 30 → 6,
  PR #5 closed, 573 MB of dependency directories reclaimed, and the two
  worktree removals that did complete were pre-inventoried.

## Risks And Decisions

- Decision: this plan deletes nothing without explicit authorization.
  The ledger states it does not authorize deletion or worktree removal,
  so cleanup waits behind a question to the repository owner.
- Risk: `intake-backup-20261006` is the only rollback point for the
  intake split. Mitigation: its content reached `main` through PR #13, so
  deletion is safe once that merge (already done) and the authorization
  are both true.
- Risk: removing a worktree with untracked media would destroy protected
  assets. The `git status`-based "clean" check proved insufficient: it
  does not cover ignored files, and the interrupted removal of
  `youtube-operating-system-foundation` destroyed its never-committed
  `exports/` recovery media (see Execution Record). Mitigation from now
  on: inventory ignored artifacts before any removal, and keep the
  Persuasion, douyin, and weekly-analytics worktrees excluded from every
  removal list.

## Archive Criteria

- Authorized cleanup executed and recorded, preserve and absorb follow-ups
  filed, the ledger current, gates green, and this plan moved to
  `docs/exec-plans/completed/` in the PR that completes its scope.
