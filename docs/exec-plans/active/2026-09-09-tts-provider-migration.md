# TTS Provider Migration And Week-One Preview Gate

## Goal

Move Dialogue and Classic Listening production behind a manifest-selected TTS
provider so the 2026-09-14 week can use Kokoro Heart/Fenrir and Chatterbox
original 500M without weakening resumability, provenance, GPU safety, ASR/QC,
mastering, subtitles, or packaging.

## Scope

- Add a provider contract and isolated-process adapters for Kokoro,
  Chatterbox original 500M, and VoxCPM compatibility fallback.
- Validate provider-specific manifest settings, pinned model revisions, host
  voice mappings, and unsupported Turbo-only settings.
- Make `--skip-existing` reuse depend on a complete trace identity rather than
  WAV existence.
- Preserve one model load per episode batch, selective turn rendering,
  sequential generation, GPU lease behavior, raw concatenation, and the
  existing post-render checks.
- Document H-drive-only interpreters, models, caches, and temporary paths.
- Produce three local 3–5 minute review previews: Kokoro dialogue,
  Chatterbox 500M dialogue, and Chatterbox 500M Classic narration.

Explicit non-goals:

- Do not create or execute the 2026-09-14 weekly plan until the owner accepts
  all three previews.
- Do not publish, upload, or schedule preview media.
- Do not commit environments, caches, model weights, generated audio, or
  preview artifacts.
- Do not use Chatterbox Turbo in a public episode during week one or mix TTS
  engines within one public program.

## System Boundaries

- Dialogue renderer and manifests: `workspace/shows/tools/`.
- Shared TTS provider contracts and isolated workers: `apps/worker-py/worker/tts/`.
- Classic production integration: `apps/worker-py/worker/classics/`.
- Focused validation: `apps/worker-py/tests/`.
- Runtime and operating documentation: `docs/LOCAL_RUNTIME.md` and show/classic
  production documentation.
- Ignored runtime outputs: `workspace/runtime/tts-audition/`.

## Status

- Branch: `feat/tts-provider-migration`.
- Owner: primary Codex agent.
- Last updated: 2026-09-09.
- State: provider integration implemented and focused validation passing.
  Three owner-gated previews are rendered with ASR/QC and mastering evidence;
  owner listening acceptance is pending before weekly-plan creation.

## Plan

1. Inventory current Dialogue and Classic render entry points, manifests,
   voice registries, GPU lease integration, and local audition assets.
2. Implement provider-neutral schemas, trace identity, isolated worker
   protocol, and Kokoro/Chatterbox/VoxCPM adapters.
3. Adapt Dialogue and Classic renderers while preserving their downstream
   artifact and quality contracts.
4. Add focused tests for configuration, host mapping, identity reuse,
   stale-artifact invalidation, unsupported settings, and cleanup on failure.
5. Document reproducible H-drive runtime selection and pinned asset policy.
6. Run focused and repository-proportional validation.
7. Generate and validate the three 3–5 minute previews, then present them for
   owner listening approval.
8. After explicit owner approval, create the 2026-09-14 weekly plan and begin
   full production as a later plan phase.

## Validation

- `npm run lint` passes, including encoding, TypeScript, architecture, docs,
  Remotion, and Python compilation checks.
- `npm test` passes: API/shared/tooling/web checks and all 188 Python tests.
- Focused migration suite passes 25 tests for provider configuration, trace
  identity, branding, Classic, episode workspace, and float-WAV concat.
- Failure paths release isolated workers and the shared GPU lease.
- Every preview has complete per-turn trace, deterministic identity, ASR/QC
  evidence, a composed review WAV, and no mixed-engine turns.
- `npm run check:encoding`, relevant Python tests, and `git diff --check` pass.
- Git status confirms no runtime environments, model files, caches, or audio
  entered the change.

## Risks And Decisions

- Chatterbox 500M long-form stability is unproven; episode-level Kokoro and
  emergency VoxCPM rollback remain available.
- Provider subprocesses use separate H-drive interpreters because their Python
  dependency sets are intentionally isolated.
- Chatterbox PerTh watermark stays enabled and is recorded in trace output.
- Existing WAVs are reusable only when provider, revision, voice/reference
  identity, seed, normalized text, and effective settings match their trace.
- A public episode uses exactly one provider. Turbo remains an internal tag
  experiment only during week one.
- Provider-native WAVs use float32. Delivery mastering owns final resampling,
  loudness, and quantization so generation is not quantized twice.
- Preview QC treats number-word/digit ASR forms as equivalent. One-word Classic
  interjections are excluded from the model-quality audition only; full chapter
  production continues to block and repair those fragile source segments.

## Preview Evidence

- Kokoro Heart/Fenrir dialogue: 216.10 seconds; 33 turns; ASR content gate
  passed; mastered to -16.21 LUFS and -1.49 dBTP.
- Chatterbox original 500M dialogue: 236.74 seconds; 26 turns; one bounded seed
  retry removed an actual leading hallucination; numeric ASR equivalence passed;
  mastered to -15.98 LUFS and -1.50 dBTP.
- Chatterbox original 500M Classic: 195.04 seconds; three-zone chapter sample;
  ASR review set empty after excluding a one-word audition fragment; mastered
  to -16.87 LUFS and -1.41 dBTP.
- Review manifest: `workspace/runtime/tts-audition/previews/review.json`.

## Archive Criteria

Move this plan to `completed/` only after provider integration, tests,
documentation, all three previews, owner listening acceptance, and the
subsequent weekly-plan handoff are complete. Keep it active while preview
approval or full-week rollout remains pending.
