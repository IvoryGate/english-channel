# Legacy Pipeline Parity Audit

## Goal

Prove whether the legacy research/topic-selection, episode-mastering, and
audiobook branches contain behavior or tests not already present in the unified
ELR, Shorts, and Classics code line, then port only verified gaps.

## Scope

Included:

- Audit `feat/youtube-research-topic-selection` at `379ac46`.
- Audit `feat/episode-audio-mastering` at `7615554`.
- Audit `feat/audiobook-skill-opt-in-srt` at `9dce05c`.
- Compare each source commit against both its merge base and the current tree.
- Classify every source path as identical, evolved, missing, obsolete, or
  uniquely valuable.
- Port only missing behavior/tests/docs in focused commits and rerun full gates.

Not included:

- Merging any stale branch wholesale.
- Deleting branches or worktrees.
- Reverting newer ELR, Shorts, or Classics behavior.
- Running production media, changing accounts, or publishing content.

## Status

- Owner: Codex primary agent.
- Branch: `codex/legacy-pipeline-parity` from `64415a6`.
- Last updated: 2026-08-24.
- State: completed locally at `298cfa4`; all 87 source paths classified and
  full gates pass.
- Publication hold: no remote YouTube mutation is authorized.

## Plan

1. Record commit/path/blob parity for all three branches.
2. Review every differing test, contract, and implementation hunk.
3. Port only current gaps, preserving newer contracts and strict layering.
4. Run focused checks, `npm run lint`, and `npm test`.
5. Update the branch ledger with evidence and archive this plan.

## Validation

- Every source path has a recorded disposition.
- Superseded branches have parity evidence, not only ancestry evidence.
- Any port includes code, tests, and docs together.
- No runtime artifact, credential, media, or source-branch mutation occurs.
- Full repository gates pass.

Completed on 2026-08-24:

- Source classification: 43 research, 3 mastering, and 41 audiobook paths.
- Focused restored regression suite: 24 passed.
- Full Python suite: 112 passed; all Node workspace suites passed.
- Encoding, TypeScript workspace and root Remotion checks, architecture, docs,
  and Python compile gates passed.
- Read-only browser CLI help passed without opening a browser.
- The tracked host registry is byte-identical to the protected root-workspace
  source (`SHA-256 60cee8e05c2ef6a7952d32414ef1baa8dcc16d307e7ef998906f90fe6560404c`).
- No legacy branch, root-workspace source, account session, remote channel,
  runtime media, or credential was modified.

## Archive Criteria

Archive when every changed path on all three branches is accounted for,
verified gaps are ported or explicitly rejected with reason, full gates pass,
and the reconciliation ledger identifies the final disposition of each branch.
