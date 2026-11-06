# Production Recovery And Honest Monitoring

## Goal

Repair monitoring and resumability without changing approved visuals, weakening
permissions or repeating completed speech generation.

## Scope And Boundaries

Process provider and ELR status, radial overlay checkpoints/progress, focused
tests and docs. Preserve unrelated dirty files on codex/brand-motion-sound-v4;
do not merge until required CI/review pass. No global permission changes.

## Status

Evening B045 stopped at28 completed Kokoro turns with stateFAILED errno13,
not an indefinitely active batch. Exact failing I/O boundary is unproven from
the old error-only state. Console output preceded durable logging and could
abort production on a broken redirected sink; now persist log first and ignore
only console BrokenPipeError/PermissionError. Actual durable-log errors still
propagate. Resume via the public detached controller rather than a console
redirection chain. Use explicit batch20 only for this confirmed CPU Kokoro run
(Monday23-turn batch succeeded); retain global Chatterbox-safe default2.

2026-10-19 owner requests all automations paused and measured rendering cost
reduction. All three local automations verified PAUSED, including automation-3
through the app tool. Keep current live legacy render untouched. This slice
changes future long-form output to30fps, reuses immutable artwork/geometry,
and processes dynamic light masks in one channel rather than supersampled
RGBA. Preserve audio-driven motion, appearance, captions and2K resolution.
Measure baseline/candidate on identical frames and inspect a short preview
before allowing a new full render. No new scheduler or model generation.

Implemented30fps dialogue, Classic multi-scene composition and chapter concat;
cached static core/band geometry/prepared avatar and supersampled alpha-only
lights. Identical12-frame800px fixture with avatar and particle: baseline
1.7213105s versus0.6285173s,2.74x faster; RGBA pixel max/mean difference0.
Halved delivery frame count is additional, not an end-to-end speed claim.
Real-audio4-second2K preview rendered at30fps,119 output frames/3.966667s;
actual2s frame inspected for geometry, lights and readable captions.35 focused
tests passed; encoding, architecture and docs checks passed. Evidence under
workspace/branding/render-cost. Current legacy full render remains untouched;
full-length optimized timing and CI/PR remain pending. No auto-resume monitor.

15:21 Asia/Shanghai: host CIM inspection confirmed oldB044 process tree and
known old IDs absent, and no other heavy production process. Overlay unchanged
at3,820,224,548 bytes and ffprobe rejects missing moov. Owner authorizes switching
to optimized render if old run remains lengthy. Public controller resume started
15:22:21, PID46524, episode_044_20261019_152221.log, skip-export/no-force.
Keep existing57 turn WAVs; no automations resumed. Actual interruption cause
is still unknown. Never describe the abandoned overlay as a usable final.

2026-10-19 owner requested mechanism repair. Sandbox project commands work;
reviewer capacity blocks elevation. B044 has no final MP4; its monolithic overlay
stopped updating03:53 UTC. Denied process access is not proof of termination.

Correction after shared-handle inspection:03:53 was cached directory metadata,
NOT confirmed termination. Actual overlay grew from1,834,745,892 to1,939,603,492
bytes during this repair. Retain current owner and never start a duplicate.

Implemented tri-state process visibility and fail-closed lease behavior; silent
child15-second heartbeat;30-second FFV1 chunks with exact motion state/precision,
checksum/input identity/frame checks and final-cache reuse; immutable palette
and prepared avatar reuse.43 focused tests passed, including real FFmpeg
interruption/resume and exact RGBA frame continuity. Encoding, architecture and
docs checks passed. Existing live legacy renderer is intentionally not restarted;
the chunk engine applies to subsequent/resumed invocations after it completes.
CI/PR and full-size production proof on the new engine remain uncompleted.

## Plan

1. Distinguish alive/dead/unknown probes; unknown retains resource safety.
2. Checkpoint short overlay chunks with motion state and verified input identity.
3. Emit bounded progress; cache immutable palette work without changing pixels.
4. Run recovery/visual tests, then continue canonical production within existing
   project permissions. Escalate only a genuine boundary.

## Validation

2026-10-20: bounded Chatterbox loader and canonical-only Classic video package
tests13/13 pass. Real Persuasion12 run passed model loading and wrote40 segment
WAVs by03:26, unlike previous1455 failure before first output. Full chapter/QC
and peak-memory measurement remain pending. Chapter12 reviewed YouTube copy
added to match generated AFTER THE FALL cover. Metadata exports no longer copy
the finished MP4; existing files are not deleted.

2026-10-19 evening: Persuasion12 failed before first output with Windows1455
inside safetensors whole-file loading, while system commit was44.6/50.4GB.
Add a provider-local Chatterbox checkpoint reader: ordinary constructors and
nonpersistent buffers retained, components moved to the approved device, then
one tensor copied at a time with key/shape/offset checks. No meta initialization,
quantization, voice/model change, package mutation or system pagefile changes.
Tiny-fixture correctness tests precede a serialized real-model trial; production
memory improvement remains unverified until that trial succeeds.

Denied/nonexistent PID tests; completed overlay reuse; interrupted chunk resume;
input invalidation; existing media tests; encoding and architecture checks.

## Risks And Decisions

2026-10-21: C035 completed125 audio turns and37m58s master, but frame encoder
exited while writing chunk7/76. Six verified lossless chunks remain reusable.
The Windows pipe error obscured encoder stderr. Bound FFV1 encoding to one
thread and retain stderr plus chunk/exit status on pipe failures; suppress
secondary close-pipe errors without masking the original failure. This is
bounded resource use and diagnostic repair, not a proven original root cause.
Resume packaging with existing master/QC/thumbnail and cached frames.
Focused resumable-frame tests4/4 pass, including pixel-exact resumed motion,
cache reuse and encoder-error propagation. Ordinary pytest startup hit unrelated
global plugin/typeguard incompatibility; isolated plugin autoload test run
passed without changing installed packages. Host inspection found no production
process before one finite recovery4336 started10:39 local with skip-master,
skip-qc and skip-thumbnail; full final verification/duration gates remain active.
Actual recovery observation: changing the checkpoint engine source invalidates
its identity fingerprint. The old six chunks are retained, but the new render
starts at frame0; do not claim those frames were reused. Audio/master/QC are
reused. Do not change the running renderer again without a real new failure.

2026-10-21 16:23: B046 final encoding was interrupted without a logged exception.
Host CIM confirmed controller4336 absent and no Python/ffmpeg processes; cause
unknown, not attributed to memory. Reconciled stale RUNNING to FAILED and
resumed finite controller41388. Existing48turn QC0flags/master/complete19257frame
overlay are reused by packaging-only recovery; no TTS or frame redraw intended.

16:52 disk recovery: ThursdayShorts220-223 all packagedPASS. C036 preflight
stopped with H free7.1GiB (10GiBminimum). Verified C035 canonical final SHA
matches its scheduled remote checkpoint, then removed only regenerable9.52GB
000_episode_035.barwave.mov; final MP4/audio/checkpoint retained. H free17.2GB
confirmed. No production processes active before finite queue41972 resumed;
C03646pending turns now rendering. Overlay can be regenerated, not undeleted.

Never start a second heavy task on unknown process visibility. No force TTS.
Do not alter approvals to work around capacity. Cache files are intermediates
inside the canonical workspace, never H:\Youtube exports.

20:47 Classic13 disk recovery: all155 audio turns and33 overlay chunks were
complete; concat failed with explicit No space left on device, H free4.4MB.
Host process inspection confirmed no project Python/ffmpeg before recovery.
Verified canonical final SHA against scheduled publication records for
C034/B046/C036/A043, then removed only their four regenerable barwave MOVs
(11,429,929,118bytes). Final MP4s, audio and checkpoint JSON retained. These
cache files can be regenerated, not undeleted. Free11.43GB confirmed before
finite controller12556 resumed; new logs weekly-classic13-space-recovery-
20261021-2050. All29652 cached frames accepted and radial-complete observed
immediately, without TTS regeneration. Check disk again before A045's larger
overlay/concat peak; do not change the running renderer's cache fingerprint.

21:24 recovery outcome: Classic13 final1001.38sec,30fps, QC/timeline PASS,
155segments100percent source coverage. Uploaded WxExlJmIFiw; correct generated
cover, Persuasion playlist, title/description and English captions+5sec visibly
saved. Both platform checks explicitly no issues before authoritative schedule
successOct24 08:00UTC+08. Durable browser checkpoint saved. Finite queue moved
automatically to B047; overlay11700/19576 observed. Before larger A045 peak,
reclaim only SHA-verified completed regenerable intermediates, not finals/audio.

21:56: B047 uploadedcYOivQxuAH0, bothplatformchecksPASS and authoritative
schedule successOct24 20:00UTC+08; generatedcover/title/description/FirstSteps
playlist andEnglish+5secSRTsaved. Sunday232-235 locallypackagePASS; A045
Chatterbox2turn batches12/112observed. To prevent next disk-full failure,
verified publicA041/A042 andscheduledB047 finalSHAs against their records,
then removed only three regenerable barwaveMOVs (8,085,422,927bytes).
FinalMP4/audio/checkpoints retained. These MOVs can regenerate, not undelete.
H free21.13GiB confirmed for A045 peak; no active job files removed.

23:34: A045 actually failed at15:19UTC with Windows exit3221225478
(0xC0000006), no Python traceback. Cause not proven; do not label memory or
disk-full.112audio/QC0flags/master/thumbnail and53100/68369frames retained.
Host CIM confirmed no project Python/ffmpeg before recovery. Added existing
validated packaging-only recovery branch to finite runtime queue for A045,
preserving final verification and duration gates; PowerShell parser PASS.
Sandbox StartProcess25980 did not survive or write state; host confirmed absent,
then single host controller45968 started23:33 with weekly-a045-recovery-
20261021-2335 logs. RUNNING state and cached chunk acceptance observed. No
renderer code/fingerprint changes, no audio/master/thumbnail regeneration.

2026-10-22 10:44: A045 recovery completed final2291.959sec38m12,112audio
QC0flags, readyupload. A044 failed17:18UTC exit1073807364 at~4500cachedframes;
cause unproven. Hostconfirmed noheavyprocess before packaging-only finite
recovery14728;43audioQC0flags/master/thumbnail retained, parserPASS, cached4500
accepted then5712newprogress. Newlogs weekly-a044-recovery-20261022-1040.
235prior stalled save had not persisted metadata remotely: sameID draft still
filename/emptydescription. Restored title/description/cover on SAMEID, both
checksPASS thenprivateSave; correcttitle/idPRIVATErow verified. No reupload.
C035PUBLICverified;220publishedlate recovery with correctC035association and
bothchecks originalPASS. Requested09:30notbackdated. Durable checkpoints saved.

2026-10-22 release milestone: finite local queue DONE_LOCAL_PUBLICATION_PENDING.
A04524y5uh2fvvc38m12 scheduledOct25 08:00 andA044lGf10l3uOLo10m51scheduled
Oct25 20:00, both authoritative Studio successdialogs, bothplatformchecksPASS,
generatedcovers/DailyTalk/metadata/English+5secSRTverified. All14longs nowremote
PUBLICorSCHEDULEDverified. All28Shorts haveactualIDs, but233/234draftfinalchecks
andremainingrelated/schedule reconciliation stillrequired; weeknotcomplete.

## Archive Criteria

Recovery tests pass, actual resumed production is verified, CI/review passes,
and the completing PR archives this plan.
