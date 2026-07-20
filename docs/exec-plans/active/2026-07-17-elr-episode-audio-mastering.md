# ELR Episode Audio Mastering

## Goal

Define and ship a formal high-quality audio path for Series A/B/C: reduce clone metallic artifacts where possible, unify loudness, and gate video compose on a measured master WAV.

## Scope

Included:

- Durable spec `docs/shows/AUDIO_MASTERING.md`
- Tool `workspace/shows/tools/master_episode_audio.py`
- Wire publish docs + compose/export to prefer `master.wav`
- Smoke on Series B episode_001 existing turns (no full VoxCPM re-render in this slice unless master still fails QC listen)

Non-goals:

- Changing Pride & Prejudice audiobook default peak-only policy
- Full Series B VoxCPM re-render of all 134 turns (optional follow-up if human rejects mastered timbre)
- Neural voice conversion / third-party paid mastering SaaS

## System Boundaries

- `docs/shows/AUDIO_MASTERING.md`
- `docs/shows/ELR_YOUTUBE_PUBLISH.md`
- `docs/shows/VIDEO_PIPELINE.md`
- `workspace/shows/tools/master_episode_audio.py`
- `workspace/shows/tools/compose_episode_video.py` / `episode_artifacts.py` (prefer master audio)
- Tests under `apps/worker-py/tests/` for report schema / dry helpers if practical

## Status

- **State:** active / implementing
- **Owner:** agent
- **Last update:** 2026-07-17

## Plan

1. Document stage map (reference → render → QC → master → video).
2. Implement ffmpeg-based per-turn cleanup + concat + two-pass loudnorm (−16 LUFS / −1.5 dBTP).
3. Emit `000_episode_XXX.master.wav` + `master_report.json`.
4. Update publish/video docs; compose prefers master when present.
5. Run master on Series B episode_001; report LUFS numbers; wait for human listen before optional re-render.

## Validation

- ffmpeg filters present: `loudnorm`, `afftdn`, `highpass`, `alimiter`
- Master report JSON includes input/output integrated loudness and true peak
- Master duration ≈ raw duration (±0.5s)
- Human listen: 电音 / loudness evenness

## Risks And Decisions

- Decision: dialogue uses **−16 LUFS** (not Spotify −14) for clearer headroom on clone peaks.
- Decision: mild denoise is post-render; severe 电音 still requires VoxCPM rerender (cfg ~2.15, better refs).
- Risk: over-denoise dulls consonants — default strength conservative; `--denoise-strength` opt-in higher.
- Risk: loudnorm two-pass adds runtime — acceptable once per episode after QC.

## Archive Criteria

- Spec merged and linked from publish workflow
- Tool runnable end-to-end on one formal episode
- Compose path documented to use `master.wav`
- Series B either accepted with master or explicitly queued for VoxCPM re-render with notes in plan
