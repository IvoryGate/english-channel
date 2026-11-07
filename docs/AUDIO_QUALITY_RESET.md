# Audio Quality Reset

As of 2026-11-07 this is an implemented experiment with a failed live trial,
not an accepted voice upgrade.
Listening approval remains pending. The reusable original corpus
and settings are in [audio-audition-v1.json](../configs/quality/audio-audition-v1.json).
That file is consumed by `scripts/audio_audition.py`. Production defaults do
not change automatically when an audition succeeds.

## Executable controls and trial

Episode turns may supply `providerSettings` overrides: Chatterbox's six
numerical generation controls, Kokoro speed, or VoxCPM CFG/step controls.
Unsupported controls, non-finite numbers and invalid sampling ranges fail
before generation. Effective settings enter the request, trace and reuse
identity. Free-text `deliveryCue` remains explicitly `editorial_only`: no
keyword-to-emotion mapping or instruction text is appended to speech.

```powershell
.\.conda-env\python.exe scripts/audio_audition.py --run-id expression-v1-20261106
.\.conda-env\python.exe scripts/audio_audition.py --run-id expression-v1-20261106 --render
```

Preparation verifies the local pinned model against recorded upstream file
hashes, freezes host/reference hashes, the voice-acceptance evidence document,
the plan and source-code hashes. It creates only an ignored run manifest;
no model is loaded or downloaded. The render action uses the existing GPU
lease, offline provider environments, serial two-turn batches and a process
watchdog. Attempts are persisted before each batch; a failed run retains its
partial artifacts and does not silently retry. The implemented first round
has no automatic repair or conditional third arm.

The first actual trial (`expression-v2-20261106`) stopped on CUDA out-of-memory
before producing a WAV: two charged attempts, 105.406 seconds. The audition now
explicitly uses `runtimeMode: staged_cpu_offload` for both Chatterbox arms.
Unchanged FP32 components move through CPU between reference encoding, text
token sampling and waveform decoding; the text model and waveform decoder do
not occupy CUDA together. Full-call inference mode also excludes reference
feature extraction from autograd. This is a memory remedy, not a quality claim.
Its nondefault mode is included in cache identity; ordinary existing provider
identities remain unchanged.

One explicit repair may pass `--previous-run-id expression-v2-20261106` with
a new run ID. It freezes the failed-run hash/reason, carries its elapsed time
inside the same 30-minute generation budget, and charges both failed attempts
against the two-retry allowance (28 attempts including the 26 original takes).
The repaired first pair receives the same recorded +10000 seed offset in both
arms. Another failed repair cannot qualify for this recovery path. No GPU
retry occurs automatically.

That repair (`expression-v3-20261107`) also stopped: a SciPy import raised
MemoryError before model loading. Total recorded cost across both runs is
four attempts and 115.687 seconds, with zero completed audio takes. A later
import-only diagnostic succeeded in 22.54 seconds with CUDA hidden; it did not
reproduce the error or establish a cause. This is not a successful staged
inference test. The repeated-failure stop rule applies; no further candidates
were started and no blind listening files exist for these runs.

The normal-host system query reports approximately 32 GB physical RAM, rather
than the historical 16 GB assumption. The v3 observation recorded at most
1763 MiB of whole-device GPU usage before model loading; that includes other
applications and is neither model peak memory nor evidence of savings.
Evidence stays in ignored `workspace/runtime/audio-quality-reset/` and
`workspace/rebuild/chatterbox-import-diagnostic.json`. A future trial must name
its runtime hypothesis, preserve these failed attempts and set a new explicit
scope; successful imports alone do not justify retrying synthesis.

On successful future runs, raw takes remain under `raw/`; `listen/` contains six shuffled A/B pairs with
gain-only, true-peak-safe loudness matching. `review.json` has blank scores;
keep `private-code-map.json` closed until scoring. Resuming a completed trial
reuses its exact traces and keeps blind assignments unchanged. Peak memory
remains null when unmeasured. A completed render means awaiting blind review,
never an accepted new production voice. Record actual run results separately
from this stable specification.

## Initial audit findings before these patches

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Written performance directions do not reach current synthesis | `prepare_episode_manifest.py` saves `deliveryCue`; `render_episode.py` requests omit it, but reports record it | A recorded cue is not an executed control |
| All turns inherit episode-level settings | `worker/tts/dialogue.py` builds identity from provider settings; the renderer does not pass turn overrides | A changed delivery note alone cannot change or invalidate generated speech |
| Pause contracts disagree | Manifest parsing saves `pauseAfterSec`; raw/master concatenation uses the global gap, while `prepare_episode_youtube_packaging.py` uses each turn's pause | Timing variation is absent from the sound and chapter times can drift |
| Technical checks do not establish expression | ASR, peak and loudness checks exist; Classic acceptance has no explicit emotional-performance scale | A technically clean episode can still be dull |
| Provider guidance is stale | `TTS_PIPELINE.md` and parts of `AUDIO_MASTERING.md` centre VoxCPM; `show_config.json` selects Chatterbox for A/C and Kokoro for B | Resolve actual configuration before following historical tuning advice |

These describe the pre-patch code and contract. The controls and timing repairs
above address their mechanical causes. They do not prove how much each issue
contributes to the user's listening dissatisfaction. The current mastering
chain also applies denoise and compression across providers. Whether that
helps each voice requires a matched-volume comparison, not a blanket removal.

Several current episode directories are junctions into
`E:\EnglishChannelArchive\workspace\shows\...`. They were initially unreadable;
the owner connected E: during this audit on November 6. Read-only access to
A045, B047 and C036 was then confirmed, and their manifests, all 205 turn
traces, QC/master/video/chapter reports and selected WAVs were inspected.
Preserve the links and assets. This bounded inspection does not establish
archive-wide integrity or subjective listening quality.

## October production evidence after archive reconnection

Evidence lives under `workspace/shows/series_{a,b,c}/episode_{045,047,036}/`:
the root episode manifest, `audio/turns/*.trace.json`,
`reports/000_episode_NNN.{qc,master_report,video_report,youtube_packaging}.json`
and `audio/_master_turns/`. Records date the sampled generation to October 21.

| Episode | Provider / effective settings | Traces | Raw speech seconds | Recorded generation seconds | Generation/speech ratio | Master duration seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A045 | Chatterbox 500M, exaggeration 0.5 / CFG 0.5 | 112 | 1984.04 | 1912.58 | 0.96 | 2278.946 |
| B047 | Kokoro, speed 0.95, Heart/Fenrir | 47 | 638.73 | 157.86 | 0.25 | 652.525 |
| C036 | Chatterbox 500M, exaggeration 0.5 / CFG 0.5 | 46 | 672.20 | 681.18 | 1.01 | 684.800 |

Each episode has exactly one effective-settings variant across its traces,
despite varied written delivery cues. A045 trace references now map Ethan to
`ethan_reference_clean.wav` and Nora to `nora_reference_clean.wav`, matching
its manifest; the reversed September audition filenames are not present.
The first raw WAV of each episode was byte-hashed and matches its trace.
This is a three-WAV integrity sample, not a full-media checksum audit.

All three stored QC reports have zero review flags and zero raw compose drift.
Their master reports nevertheless record B047 at -1.33 dBTP and C036 at
-1.41 dBTP against a -1.5 dBTP target; A045 records -1.50 dBTP. Integrated
loudness is -16.21, -16.72 and -16.01 LUFS respectively. These are persisted
measurements, not new measurements of final encoded videos. Add a final-master
acceptance check and remeasure before claiming release compliance; zero raw
QC flags do not certify the processed audio.

The timing defect is observable in these artifacts, not only inferred from
code. A045's master report applies tempo 0.882219, but its chapter package
still totals 2014.66 seconds from raw turns versus 2278.946 seconds for the
master. Summing the actual mastered WAV headers plus the recorded master gaps
puts chapter marker `p101` at audio time 2026.359 seconds; packaging records
1790.800 seconds, a 235.559-second difference. Both use the same intro offset,
so that offset cannot explain the discrepancy. B047's final marker differs
by 1.840 seconds and C036's last marker by 0.240 seconds because the stored
per-turn pauses differ from the global master gap. Public descriptions were
not inspected or changed; these findings establish local packaging defects.

Use the first raw A045 and B047 turns as existing short comparison references
only: `audio/turns/turn_001.wav` is 13.300 and 14.775 seconds respectively.
Their scripts and voices differ, so preference between them cannot isolate
a provider effect. No subjective listening verdict has been made.

## Measured historical evidence, not current capacity

The accessible September audition traces under
`workspace/runtime/tts-audition/previews/` give these totals:

| Provider | Turns | Speech seconds | Generation seconds | Generation/speech ratio | Median recorded model-load seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chatterbox original 500M | 26 | 229.74 | 232.77 | 1.01 | 24.909 |
| Kokoro | 33 | 206.50 | 50.43 | 0.24 | 13.763 |

Both sets use one settings variant. These figures exclude process startup,
retries, mastering and video; repeated model-load fields are not independent
load events and must not be summed. The host reports an RTX 4060 Laptop with
8188 MiB VRAM; a 2026-11-07 host query measured approximately 32 GB RAM,
superseding the historical 16 GB operating assumption. Retain bounded
batches and measure total wall time and peak memory before increasing capacity.

The completed migration plan records owner acceptance on September 9, while
the runtime preview `review.json` still says `awaiting_owner_listening`.
The old dialogue audition also maps Ethan to a Nora-named reference and Nora
to an Ethan-named reference; the current registry has the opposite mapping.
This is an approval/provenance discrepancy, not evidence that current public
episodes have the wrong voices. Freeze and verify the actual reference hashes
for this experiment instead of inheriting the old preview's approval.

## First experiment: expression under fixed conditions

The six snippets cover embarrassment, quiet support, disagreement, dry humour,
conversational repair and literary narration with names. They contain 13
utterances and 188 words, estimating 89 seconds at 130 words per minute with
the specified turn gaps.
Duration is an estimate, not a quota: never pad or stretch the audition.
The narrative and dialogue are original test copy, not competitor excerpts.

1. Resolve the existing voice registry and approval evidence. Freeze paths,
   reference hashes, verified local model files and package versions. Fail if
   unavailable; this zero-new-spend trial authorizes no downloads or purchases.
2. Render the same words, speakers and seeds with `cb-baseline` and
   `cb-expression`. Only `exaggeration` changes, from 0.5 to 0.7. The written
   `performanceIntent` is a listening rubric, not text to prepend to synthesis.
3. Make six separate A/B review pairs with the same 0.28-second turn gaps and
   peak-safe, matched loudness. No music, video, denoise, stretching or sound
   effects. Preserve untouched raw takes.
4. Randomise pair order and save scores before revealing provider/settings.
   Owner triage takes at most 12 minutes of the available 30-60 weekly review
   minutes. A tie or insufficient evidence is a valid result.
5. If expression improves but delivery becomes too fast, a later round changes
   only `cfgWeight` from 0.5 to 0.3 against `cb-expression`. Do not run this arm
   automatically or treat two changed controls as a one-variable result.

The official Chatterbox model card suggests higher exaggeration and lower CFG
for dramatic speech, and notes that exaggeration can increase speed. Our
staged comparison separates those effects; it does not promise that dramatic
delivery suits every scene. [Official tuning guidance](https://huggingface.co/ResembleAI/chatterbox)

Kokoro remains an optional separate cost reference using its already-installed
Heart/Fenrir presets. Different voices prevent attributing preference solely
to emotion controls. Its official model card describes 82M parameters and
Apache-licensed weights; small size is not a listening-quality guarantee.
[Official model card](https://huggingface.co/hexgrad/Kokoro-82M)

## Budget and decision

Round one permits 26 initial utterance generations and at most two total
defect repairs, each with a named defect and changed, recorded seed. Retain
rejected takes. One GPU job, two Chatterbox turns per process, a five-minute
batch watchdog and a 30-minute total wall-clock limit keep the trial bounded.
Stop on repeated crash or exhausted budget; an incomplete run does not pass.
Use at most 512 MiB of new artifacts and require 2 GiB free disk or the existing
runtime's stricter requirement. Unknown resource ownership stops the trial.

Score naturalness, appropriate emotion, timing, intelligibility, voice
stability and desire to continue from 1 to 5, using the anchors in the JSON.
The provisional selection rule requires preference on at least four of six
snippets, median naturalness/emotion/intelligibility/voice-stability scores of
at least 4, and no clarity or identity regression. Unrequested words, lost
meaning, unresolved name errors, clipping and missing provenance fail the
audition. ASR flags require review; a transcript score is not a listening score.

This small test selects the next experiment, not a statistically established
winner. Before changing a public voice, add two owner-arranged target-listener
reviews and one 8-12 minute fatigue test. Volunteers involve no new paid spend;
this document does not authorize outreach. After synthesis selection, compare
the same raw takes through minimal processing and the current full mastering
chain at matched loudness. Production release gates still apply afterward.

Record wall minutes per accepted audio minute, rejected-take fraction, human
review time, peak RAM/VRAM and listening preference. Unsupported measurements
remain null with a reason. Do not label an unmeasured peak as zero.

## Follow-up patch boundaries

| Separate slice | Change | Required proof |
| --- | --- | --- |
| Audition runner | Consume this spec; freeze references/model hashes; bounded offline generation; blinded review export | Two-arm requests differ only in declared variable; budgets stop; partial evidence survives; no public action |
| Effective performance controls | Provider capability schema, validated supported turn overrides, request and trace wiring in `worker/tts/` and episode renderer | Emitted settings equal recorded settings; a changed effective setting invalidates reuse; unsupported controls cannot appear applied |
| Shared audio timeline | One resolved turn/pause timeline for raw/master audio, subtitles and chapter packaging; include measured tempo when used | Variable-gap fixture and mastered-duration fixture agree across outputs; no existing audio is silently regenerated |
| Final-master acceptance | Evaluate measured loudness and true peak after mastering, retaining the raw QC result separately | Out-of-target processed audio cannot inherit a pass from raw segment QC; remeasure final delivery encoding |
| Voice acceptance records | One identity-bound approval record replacing scattered acceptance assertions | Approval binds provider/revision/reference/settings and review-artifact hash; historic mismatches remain visible |

Keep free-text editorial intent separate from supported controls. Chatterbox
500M has numerical controls; the current Kokoro adapter exposes preset voice
and speed, not arbitrary emotional instructions. Do not place stage directions
in spoken text to simulate missing functionality. Changing cues without a
supported acoustic mapping should report editorial-only status.

No new model belongs in round one. Qwen3-TTS is a later research candidate:
its official table marks instruction control for the 1.7B CustomVoice and
VoiceDesign variants, not the 0.6B variants. Local Windows memory/latency and
English performance remain unverified. [Official model table](https://github.com/QwenLM/Qwen3-TTS)
Chatterbox Turbo/Nano offer different controls, but are not implemented by the
current adapter and require a separate provider review. The current official
repository includes a retirement notice alongside older promotional material;
verify maintenance and exact artifacts before selecting a new dependency.
[Official repository](https://github.com/resemble-ai/chatterbox)

Store generated evidence only under the ignored runtime root in the spec.
No audio files, credentials or private listener details belong in Git. This
slice changes neither formal voice settings nor public schedules and does not
reactivate the paused automations.

## Completed Staged Comparison, 2026-11-07

The explicit staged FP32 runtime completed the two-take feasibility probe and
then the separately budgeted 26-take/six-context comparison with no retry.
The full comparison used 525.922 seconds runner wall time for 124.24 seconds
of raw speech; paired listening loudness differed by no more than 0.02 LU.
It is stored under `workspace/runtime/audio-quality-reset/staged-expression-20261107/`.
The earlier failed budgets remain charged and separate. Sampled free Windows
commit reached 239 MiB, so success alone does not establish safe production
headroom. D-drive pagefile settings have been approved and saved, but their
capacity was not active at the last live query; no reboot was performed.

The owner heard the initial short probe as similar and still needing work.
After two complete contexts, the owner heard some improvement but did not
accept the voices for formal use. No winner or dimension scores were inferred.
The current scalar-exaggeration experiment is therefore not a basis for a
default change. A new instruction-conditioned provider would require a
separate bounded feasibility and listening trial; no repeated Chatterbox run
or whole episode is justified by these results.
