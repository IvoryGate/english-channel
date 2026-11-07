# Instruction-Controlled Voice Feasibility

## Goal And Scope

Determine whether a zero-new-spend instruction-conditioned voice can run on
this Windows 32 GB RAM / RTX 4060 Laptop 8 GB host and produce a useful first
listening comparison. The owner heard some improvement in the completed
Chatterbox comparison but rejected formal use. This is a new hypothesis,
not another scalar-exaggeration retry or a production voice switch.

Branch `codex/instruction-voice-feasibility` starts from main `fd7113b`, after
production handoff/final-media gates merged through PR #25. The parent
[production plan](2026-11-07-production-readiness-reset.md) remains active.

## System Boundaries

Use an isolated local audition environment and ignored runtime evidence, not
a new production provider or scheduler. Preserve existing environments and
model assets. No paid API, public upload, external messages, new voice clone,
default change or reboot. A successful probe does not grant voice acceptance.

## Plan And Budget

1. Freeze official Qwen3-TTS 1.7B CustomVoice model revision
   `0c0e3051f131929182e2c023b9537f8b1c68adfe` and the complete included
   speech-tokenizer snapshot. Expected weights total 4,515,695,644 bytes;
   model download cap 4.6 GB, dependency downloads at most 1 GiB, incremental
   disk at most 12 GiB. Keep caches/temp/output on H. Stop if resolution
   requires replacing inherited Torch or exceeds the cap.
2. Create a Python 3.12 dependency-overlay venv under
   `workspace/runtime/tts-audition/qwen3-customvoice-env`, inheriting project
   Torch/torchaudio 2.7.1+cu118 read-only. Install local Qwen 0.1.1,
   Transformers 4.57.3, Accelerate 1.12.0 and HF Hub 0.36.0 overlays.
   Freeze all effective package paths/versions and verify base files did not
   change. This is not a self-contained environment: base changes invalidate
   the probe identity. Setup/download gets a 20-minute ceiling; retain any
   failure and partial downloads without an unbounded retry loop.
   Pin the wheel hash too. Match its inference/model/tokenizer source against
   reviewed commit `022e286b98fbec7e1e916cb940cdf532cd9f488e`, or independently
   review and fingerprint the actual installed implementation before running.
   Package version 0.1.1 alone is not proof of that source commit.
3. Verify the installed implementation supports SDPA and separate unspoken
   instructions. Load the complete pinned local path with global offline
   mode, CUDA BF16 and SDPA; do not build FlashAttention. Record live resource
   preflight and shared GPU ownership before inference. Pending pagefile
   configuration is not active capacity. Require at least 12 GiB free host
   commit and 6 GiB free VRAM for this first unmeasured load; if unmet, hold.
4. One process, two takes, external five-minute wall limit, no retry. Same
   Ryan preset, English text and reset seed; change only neutral versus
   specific warm/firm delivery instruction. Text: "I can help for ten minutes,
   but I need to leave at six." Limit max_new_tokens to 256. Preserve raw
   WAVs, exact request/runtime/model hashes, elapsed/resource evidence and
   failures. No post-generation time stretching.
5. If both takes finish, match loudness for a blinded short comparison and
   review completeness, unintended speech and audible defects. Larger tests
   require a named next hypothesis after this result; success cannot silently
   expand the two-take budget. Document the decision and independent review.

## Validation And Status

2026-11-07: environment installed; pinned model download is in progress and
local quality/memory feasibility remains unknown. The first resolver attempt
stopped after 64.469 seconds at a proxy TLS handshake timeout, before Qwen
installation or model download. Failure evidence is preserved. One diagnosed
repair uses a process-only direct route with normal certificate verification,
within the original 20-minute setup deadline; system network settings did not
change. Ten official wheels total 20,246,153 bytes.

Independent review passed for actual installed source, effective package
locations and the selected base metadata/source fingerprints. Qwen/Transformers/
Accelerate/Hub resolve from the new overlay; Torch/audio resolve from the base.
A CUDA-hidden import succeeded without initializing CUDA. The overlay has an
unrelated Streamlit/rich constraint conflict, alongside pre-existing base
Playwright/UMAP conflicts; no Qwen dependency conflict was found. This is an
audition environment, not a general application environment or deployment.

The installed wheel is identified by its PyPI hash and actual reviewed source
hashes, not assumed to equal the GitHub commit by version number. Actual audio
tokenizer attention backend must be recorded at load; the top-level backend
argument is not fully forwarded to that auxiliary loader.

Do not rerun unrelated whole-repository tests for ignored runtime artifacts;
validate environment isolation, model hashes and actual outputs directly.
Tracked changes still use PR, required CI and independent review.

## Risks And Decisions

The official table and inference code disable instruction control for the
0.6B variant, so it is not an emotion-control substitute. A 1.7B parameter
count alone does not prove an 8 GB GPU fit. SDPA avoids the unverified Windows
FlashAttention build but may change performance. Ryan is an experiment
preset, not an accepted cast identity for B052.

Sources: [model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice),
[pinned inference code](https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/qwen_tts/inference/qwen3_tts_model.py),
[pinned dependency specification](https://github.com/QwenLM/Qwen3-TTS/blob/022e286b98fbec7e1e916cb940cdf532cd9f488e/pyproject.toml).

## Archive Criteria

Record an exact, reproducible two-take result or an evidenced setup/runtime
failure and the resulting next decision. Do not call an unsuccessful runtime
a quality rejection, or completed setup a voice-quality success. Archive this
bounded feasibility scope when assessed; the parent production/voice gates
remain open until actual acceptance and a verified episode package exist.
