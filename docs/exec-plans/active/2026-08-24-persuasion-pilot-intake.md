# Persuasion Pilot Protected Intake

## Goal

Preserve the uncommitted Persuasion production implementation, then port its
reusable ingestion, audio, subtitle, visual, packaging, and recovery behavior
onto the accepted Classic Listening foundation without losing local assets or
weakening channel-level policy.

## Scope

Included:

- Create a code-only checkpoint on `codex/classics-persuasion-pilot` for the
  modified and untracked source, tests, configs, scripts, and plans.
- Leave generated PNG/WAV review assets in the protected source worktree until
  their provenance, role, hash, and repository suitability are recorded.
- Port production behavior semantically into
  `codex/persuasion-pilot-intake`; do not replace the foundation's
  `types -> schema -> repo -> service -> transport` lifecycle domain.
- Reconcile the book production config with the rights catalog, shared release
  policy, authority level 0, and the unresolved audio-acceptance block.
- Reconcile package/lock manifests, Remotion compositions, runtime paths,
  provider boundaries, tests, docs, and operator commands.

Not included:

- Deleting, moving, regenerating, or overwriting any source-worktree media.
- Promoting the existing Riley/VoxCPM2 narration for publication.
- Uploading, scheduling, or publishing a video.
- Selecting a replacement TTS provider or raising authority above level 0.

## Status

- Owner: Codex primary agent.
- Branch: `codex/persuasion-pilot-intake` from `13fbf48`.
- Source branch: `codex/classics-persuasion-pilot` at `0c245ec` plus 76 dirty
  status entries before protection.
- Last updated: 2026-08-24.
- State: source code protected at `8d548d0`; media manifest recorded; semantic
  port pending.
- Source media: 33 untracked PNG/WAV/JSON files, 55,819,675 bytes (53.23 MiB), retained
  in place and excluded from the initial code checkpoint.
- Publication hold: shared public scheduling is disabled, Classic Listening
  authority remains level 0, and audio acceptance remains blocked.

## Plan

1. Checkpoint modified and untracked code separately from generated media.
2. Record a media manifest with paths, sizes, hashes, roles, and provenance
   status without copying the binaries.
3. Compare the source production tree to the accepted foundation by behavior
   and port one strict-layer vertical slice at a time.
4. Reconcile manifests and dependencies, run focused and full gates, and
   verify no source asset or runtime artifact changed.
5. Update the branch ledger and source plans; archive this plan only when the
   production adapter is accepted locally.

The source-only `continue_persuasion_1_3.ps1` polling helper is preserved in
the checkpoint but intentionally excluded from the unified adapter: it embeds
an absolute repository path, can wait indefinitely, and represents an obsolete
attempt to continue generation with the now-blocked voice provider.

## Validation

- The source branch has a code-only checkpoint whose diff excludes `public/`
  media and runtime workspaces.
- Every pre-existing source-worktree path and hash remains recoverable.
- Exact EPUB/source coverage, resume, aligned subtitles, QC, V2 proof, and
  packaging tests pass after the semantic port.
- `npm run lint` and `npm test` pass.
- Package manifest and lockfile agree.
- Authority level 0 rejects upload/schedule/public transitions.
- No credential, EPUB, model weight, generated chapter audio, exported video,
  or unreviewed binary enters the integration commit.

## Known Risks

1. The source and accepted foundation contain competing `worker/classics`
   designs. A wholesale copy would destroy authority and event-ledger rules.
2. The source pilot plan begins with three accidentally captured tool-output
   lines; preserve the checkpoint, but remove those lines in the reviewed port.
3. The production config references local voice and visual assets that are not
   all tracked. Missing assets must fail preflight rather than be inferred.
4. Existing chapter packages are review artifacts. The speech-coupled
   electronic texture remains a product blocker regardless of structural QC.

## Archive Criteria

Archive only when the source is durably protected, selected production code is
integrated with strict layering, dependencies and docs agree, full gates pass,
the media inventory remains intact, and the next audio-provider action is
explicitly recorded.
