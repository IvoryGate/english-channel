# Measured Episode Audio Timeline

The shared `workspace/shows/tools/episode_timeline.py` contract resolves actual
turn durations and inter-turn gaps for mastering, subtitles and YouTube chapters.
It fixes the former raw/master split: slowing speech during mastering changes
chapter times as well as captions. Original turn WAVs remain unchanged.

## New Production

- `pauseAfterSec` overrides `renderSettings.interTurnSilenceSec` between turns.
  Gaps must be finite and nonnegative. There is no extra gap after the last turn.
- Raw composition, QC duration expectation and mastered concatenation consume
  the same gap vector. One silence clip is reused per distinct gap length.
- Flagship pacing calculates the speech target after subtracting the actual
  gap total. Timing is measured again from the processed turn WAVs; multiplying
  raw times by an intended tempo is not accurate enough.
- Master reports include a versioned timeline, manifest timing/text identity,
  processed-turn hashes, final master hash and actual program duration. The
  sum of processed durations plus gaps must match the master within 0.05 seconds.
- Chapters and per-clip subtitles resolve that same clock. They reject changed
  manifest text/pauses, modified processed media, missing reports or duration
  mismatch instead of silently using original speech durations.
- Existing `--gap-sec` subtitle overrides are compatibility assertions: a value
  that disagrees with the resolved audio is rejected. Normal pack/preview calls
  no longer force a global gap over the actual recording.

The timeline contains unrounded seconds internally; display timestamps round
only at export. Intro offsets remain a separate measured video boundary.
Script-derived word placement remains labelled scripted rather than ASR-verified.

The historical `render_episode_edge_tts.py` prototype is outside this canonical
pipeline: it retains flat paths and compressed turn audio. It is not covered by
the shared PCM timeline acceptance and must not be substituted for the formal
renderer without a separate migration.

## Existing Recordings

Old master reports do not contain hashes or a gap vector. For those files the
resolver reads the actual processed turn WAVs, uses the report's recorded
uniform `gapSec`, and checks the total against both the actual master WAV and
reported duration. It reports `legacy-mastered-turns-duration-validated`.
This repairs timing without generating speech or rewriting archived audio, but
does not claim complete historical provenance. Newly changing a manifest pause
cannot retroactively change a legacy recorded gap.

If a master exists, missing or inconsistent master evidence is an error; raw
turns cannot substitute for it. Raw-only previews may use measured raw turns
and manifest pauses, labelled `raw-turns-manifest-gaps`. When a concatenated raw
file exists its duration must agree too.

Existing uploaded descriptions, captions and videos are not automatically
changed. Review a local repair report first and handle any remote corrections
through the publication boundary. Do not overwrite a saved legacy report to
make an invalid recording pass.

## Verification

`test_episode_timeline.py` covers variable and zero gaps, no trailing silence,
tempo budgets, legacy master reconstruction, shared chapter/subtitle offsets,
stale text/pauses and same-duration audio replacements, missing master evidence,
duration drift and real FFmpeg concat behavior. The same contract permits a
read-only A045 audit; write comparison results outside the E: archive.

The 2026-11-06 read-only A045 check resolved 112 mastered turns plus recorded
0.28-second gaps to 2278.945729 seconds, matching the actual master WAV.
Marker p101 resolves to 2026.359 seconds rather than the historical package's
1790.800 seconds, a 235.559-second correction before the unchanged intro offset.
Comparison evidence is `workspace/rebuild/audio-timeline-audit.json`; the
archive and remote metadata were not modified.

This is timing integrity, not subjective voice acceptance or a final loudness
gate. Those remain separately evaluated in `docs/AUDIO_QUALITY_RESET.md`.
