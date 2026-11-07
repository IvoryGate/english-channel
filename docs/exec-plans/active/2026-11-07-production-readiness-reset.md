# Production Readiness Reset And First Local Pilot

## Goal

Finish the usable research -> brief -> script -> voice/visual -> measured
master -> captions/video -> community draft -> measurement-plan workflow,
then begin the first local production as requested on 2026-11-07. Do not
confuse completion of future 28-day observations with readiness to produce.

## Scope And Boundaries

Branch `codex/production-readiness-reset` starts from main `e872b3b`.
Reuse the ELR controller, provider interface and existing workspaces; no new
parallel database or scheduler. Complete final-master and encoded-audio gates,
add a small executable production handoff contract, retain private evidence
locally and produce a real pilot only after the relevant preparation gates.
Zero new paid spend; no public release, messages or paused-automation restart.
The user's instruction already authorizes local production after workflow
acceptance. Do not ask again whether to start that production.

## Execution

1. Final audio acceptance: fresh measured loudness/true peak after mastering
   and final encoding, fingerprinted evidence, meaningful regression tests.
2. Runtime feasibility: preserve failed expression-v2/v3. Investigate one
   staged-mode two-turn probe only after an import/resource preflight passes;
   named hypothesis is that staged weights fit the measured 32 GB/8 GB host.
   Fresh scope allows 5 minutes, two turns, no automatic retry. On success,
   allow one separately recorded bounded six-snippet run (26 turns/30 minutes)
   for listening; on failure, diagnose once and evaluate installed Kokoro CPU
   as a separate cost/reference path, never an expression-test winner.
3. Production handoff: machine-check brief, voice identity/evidence, image
   provenance and canvas, script-review evidence, community exercise drafts
   and T+24h/7d/28d measurement plan. Separate local preparation, production
   validation and public release; unknown public metrics cannot grant release.
4. Freeze one original pilot from the existing H1 brief; prepare its complete
   script and draft community follow-up while independent runtime work runs.
5. Full validation, independent review, scoped PR/CI/merge. Begin local pilot
   production once workflow gates pass; preserve remaining listening or public
   gates truthfully if the owner must assess actual output.

## Validation And Status

2026-11-07: active. Tests must distinguish raw QC from final-media acceptance,
reject stale/edited artifacts and unknown evidence, and allow valid local work
without pretending that publication or listening approval exists. All E-drive
archives remain read-only; new media uses H-drive ignored workspaces.

### Production Handoff Slice

2026-11-07, metrics_integrity: implemented the read-only layered handoff
validator and ELR CLI, with original brief/script evidence, manifest-bound
human voice acceptance, source/final image provenance, community drafts and
future measurement plans. The production hook binds the actual consumed
workspace/script/manifest/images. Local pilots preserve frozen manifests;
legacy CFG rewriting is disabled only for that format. Local package evidence
requires artifact-bound review and the final-audio acceptance adapter; it never
grants public release.

Validation: 26 handoff and 17 orchestrator tests passed (43 combined), including
pending voice, stale artifacts, substituted production context, human-only voice
acceptance and both controller freeze paths. Encoding, docs, architecture and
diff checks passed. Actual episode B052 reports ready_to_prepare=true and
local_production/package_verified/public_release=false. Voice listening and
final visual/package evidence remain open, so the overall plan stays active.

### Final Audio And Pilot Preparation

2026-11-07: final master and decoded final video now require measured -16 LUFS
+/- 1 LU and true peak <= -1.5 dBTP, fingerprinted to their actual inputs.
Packing/export cannot bypass this with skip flags. The focused 26-test suite
includes real WAV/AAC measurements and stale-artifact/source rejection. An
independent review passed. Handoff/controller/source-pause integration passed
53 combined tests and independent review. Full repository lint and tests pass:
372 Python tests plus Node/API/web checks. CI remains due before merge.

The original B052 pilot has 961 spoken words across 44 turns and three explicit
six-second practice gaps. Its source pause directive survives manifest
preparation, is not spoken or counted, and applies only to its next turn.
Script review and preparation evidence pass. The complete thumbnail and body
art have independently reviewed 1920x1080 PNG outputs, source/prompt/reference
hashes and explicit resize/conversion history; visual evidence now passes.
Voice acceptance is the only remaining local-production handoff gate. The
finished package must still earn its separate acceptance.

Staged FP32 completed the bounded two-take feasibility probe: 47.11 seconds
generation wall time for 8.64 seconds of raw speech. The owner's preliminary
listening feedback was "similar, still needs improvement"; it grants no voice
acceptance or default change. The separately scoped 26-take context comparison
completed all takes with no retries in 525.922 seconds runner wall time,
producing 124.24 seconds of raw speech. Matched pair loudness differed by at
most 0.02 LU. Sampled device VRAM reached 3203 MiB, while free host commit fell
to 239 MiB; this is not comfortable production headroom. These are sampled
whole-device/host observations, not process memory peaks.

After hearing two complete contexts, the owner reported some improvement but
not ready for formal use. No arm preference, numerical score or production
voice acceptance was inferred. Stop scalar-exaggeration reruns; investigate a
separately bounded instruction-conditioned model trial before another audition.

The owner approved D-drive pagefile configuration of 8192 MB initial and
16384 MB maximum, without reboot. Configuration was verified; the live usage
query still showed only the C-drive pagefile. Do not count the pending D-drive
capacity as active memory. Before/after evidence remains in ignored
`workspace/rebuild/pagefile-*-20261107.json`.

## Completion Criteria

The actual pipeline can produce and verify a local pilot package through the
shared contracts. Record artifact paths, measured checks and open human gates.
If runtime prevents that result, retain this plan active with exact evidence;
do not archive the whole workflow as complete merely because code merges.
