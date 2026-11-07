# Local Production Handoff

The read-only handoff validator distinguishes preparation, production, verified
local packages and publication. It reuses existing episode workspaces, TTS
identity contracts and final-audio acceptance. It creates no database, schedule,
approval, media or remote action.

For a local pilot, prepare the manifest explicitly, record provider/runtime
choices and intentional practice pauses, then review and fingerprint it.
Produce/render-audio retain those exact bytes instead of regenerating it.
The render monitor ignores its legacy series-level `--cfg` rewrite for this
format. Changing the frozen inputs requires preparation and a new review;
missing manifests stop before generation. Other formats retain their existing
prepare/CFG behavior.

The named `local_pilot` format is selected in
`production/production_card.json`. Controller preflight uses **800–1400 spoken
words** for this format while retaining the other series script checks.
Intentional practice gaps belong in the source draft as
[`[Pause After: 6]`](EPISODE_PIPELINE.md#intentional-practice-pauses), so explicit
manifest preparation preserves them before review and freezing.

```powershell
.\.conda-env\python.exe scripts/elr.py handoff --input workspace/shows/series_b/episode_052/production/handoff.json --require ready_to_prepare
```

`--require` accepts `ready_to_prepare`, `local_production`, `package_verified`
or `public_release`. The command prints JSON and exits 0 only when the requested
stage passes; otherwise it exits 2. `public_release` always fails: local evidence
cannot grant channel authority or prove platform acceptance.

| Stage | Evidence required |
| --- | --- |
| `ready_to_prepare` | Original brief and research references, reviewed script, community practice and follow-up drafts, T+24h/7d/28d measurement plan |
| `local_production` | Preparation plus reviewed production manifest, all actual speaker/provider/settings identities accepted by a human on a fingerprinted audio sample, and verified visual provenance and canvas |
| `package_verified` | Production plus fingerprinted master/video/captions/description, an artifact-bound package review and current final-master/encoded-audio acceptance |
| `public_release` | Never granted by this validator; separate authority and remote checks remain necessary |

Missing or pending evidence does not pass. Preparation does not require future
audience observations, finished media, or an accepted voice. It permits planning
and a separately bounded audition; it does not permit whole-episode rendering.
The controller requires `local_production` for both full render-audio and produce
when the production card selects `format: local_pilot`. Existing formats retain
their existing preflight contract.

## Runtime Contract

All evidence references have the shape `{"path": "project/relative/file",
"sha256": "64 lowercase hexadecimal characters"}`. Actual bytes must match.
Paths may reference existing read-only archives through project paths; no file
is rewritten. Large media is hashed in streaming chunks.

The input object uses schema `elr-production-handoff-v1` and contains:

- `contentId`, `episodeId`, and project-relative `workspace`.
- References `brief`, `script`, `scriptReview`, `community`, `measurementPlan`
  and, once prepared, `productionManifest`.
- `voices`: selections described below; an empty list is pending, not accepted.
- `visuals`: one `thumbnail` and one `body` selection described below.
- `package`: null until built, then `{manifest, artifacts, review}`.

Each preparation JSON record includes the same `contentId`:

| Reference/schema | Required fields |
| --- | --- |
| `brief` / `elr-production-brief-v1` | `hypothesisId`, `audienceNeed`, `viewerOutcome`, `originality: original`, `originalityBasis`, nonempty `research` reference list |
| `scriptReview` / `elr-script-review-v1` | Review fields below; exact `scriptSha256`, `briefSha256`; `manifestSha256` required for production; checks `original_work`, `viewer_outcome`, `practice_payoff`, `spoken_text_only` |
| `community` / `elr-community-drafts-v1` | `status: draft_only`, `remoteActionAuthorized: false`, `practicePrompt`, `channelAuthoredExample`, `followUpDraft`, `feedbackRouting` |
| `measurementPlan` / `elr-measurement-plan-v1` | Exactly three `windows`, each with `at` (`T+24h`, `T+7d`, `T+28d`), `source`, nonempty `metrics`; `decisionRule`, `guardrails`, `missingEvidenceAction: hold` |

A review records `status`, `reviewer: {kind, id}`, `reviewedAt`, and `checks`.
Only `status: accepted` with all named checks literally true passes. Record the
actual reviewer and decision; do not fill these fields from file existence or
unit-test success. Agent review is allowed for scripts, visuals and packages.
Voice acceptance requires an actual human listening review. These records are
explicit attestations, not automated proof of subjective quality.

## Voice And Visual Evidence

Each voice selection is `{speakerId, identity, acceptance}`. Derive identities
without loading models using
`worker.production_handoff.providers.manifest_voice_identities(root, manifest)`.
It uses the same provider defaults, effective settings and voice references as
the renderer. Each spoken host must be present. A speaker with different
per-turn settings requires separately accepted variants before extending this
minimal handoff.

`identity` includes `providerId`, `modelId`, `modelRevision`, `localModelPath`,
`runtimeMode`, `providerSettings` and `voice`. Clone voices include the existing
`referencePath`/`referenceSha256`; presets include `voiceId`. Compute its digest
with `worker.production_handoff.schema.identity_sha256`.

The acceptance record uses `elr-voice-acceptance-v1`, `scope: local_production`,
`identitySha256`, audio `sample` and `sampleTrace` references, and review fields.
The trace must be the existing `elr-tts-turn-trace-v1` format and bind the same
provider/settings/voice and sample audio hash. The human review checks are
`identity`, `rights`, `intelligibility`, `stability`, `naturalness` and
`appropriate_emotion`. Unknown rights or listening outcomes block production.
Acceptance for one preset, reference or parameter set cannot approve another.

Each visual is `{role, artifact, provenance}`. The artifact is the accepted
1920x1080 image consumed by the production adapter. Its provenance record uses
`elr-visual-provenance-v1`, the same `contentId` and `role`, `generator`, a `prompt`
reference, explicit `references` list, original `source` reference,
`sourceCanvas: [width,height]`, final `output` reference and descriptive
`transform`. Review checks are `identity_consistency`, `readability` and
`no_unintended_text`. Intended headline lettering is allowed.

Source dimensions are measured independently from the final canvas. For
example, an original 1672x941 source must remain recorded as 1672x941 even if an
explicit later transform produces 1920x1080. Hashes, prompts and original
references remain available; resizing cannot establish identity approval.

## Package And Controller Binding

`package.artifacts` contains exactly `master`, `video`, `captions` and
`description` references. `package.manifest` must equal `productionManifest`.
The `review` reference uses `elr-local-package-review-v1`, the same `contentId`,
`manifestSha256`, and `artifactHashes` for those four artifacts plus `thumbnail`
and `body`. Required review checks are `captions_sync`, `visual_readability`,
`promise_fulfilled` and `no_unintended_speech`.

The CLI supplies the existing `require_episode_audio_acceptance` adapter. It
rechecks current manifest/source/media fingerprints and measured final loudness
and true peak; both master and encoded records must bind the declared package.
A service instantiated without this adapter cannot claim `package_verified`.
This does not claim native YouTube processing, audience validation or permission
to upload.

The local-pilot production card stores `handoff` as a fingerprinted reference
and `publicReleaseAllowed: false`. Controller preflight calls
`evaluate_reference(root, reference, "local_production", expected_context=...)`.
`expected_context` contains `episodeId`, `workspace`, actual `script` and
`productionManifest` paths, and `visuals: {thumbnail: path, body: path}`. These
paths must match the accepted references and their bytes. The formal ELR pack
uses `coverBakedScene` and `videoBgSource16x9` as visual inputs. A valid handoff
for a different episode or a copy of its files cannot approve the current run.

The implementation follows `types -> schema -> repo -> service -> transport`,
with existing TTS identity and final media checks behind provider/adapter
boundaries. The handoff reports evidence; the ELR controller retains execution
ownership, and the shared channel domain retains publication authority.
