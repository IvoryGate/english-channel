# ELR Episode Audio Mastering

Durable audio quality contract for Series A / B / C after VoxCPM render and before video compose.

Companion publish flow: [`ELR_YOUTUBE_PUBLISH.md`](ELR_YOUTUBE_PUBLISH.md).
The legacy `audiobook-chapter-tts` workflow stays on peak-only quiet boost
(`CONTROLS.md`) unless a human asks for a separate master. The unified Classic
Listening adapter has its own tracked mastering contract and audio-acceptance
gate; a failed narrator cannot be repaired into approval by this chain.

## Goals

1. Reduce metallic / robotic “电音” from clone TTS where post-processing can help.
2. Unify loudness across hosts and turns for YouTube dialogue listening.
3. Keep speech clear: no crushed dynamics, no underwater denoise, no false stereo wideners.
4. Produce a measurable report (LUFS / true peak) before video packaging.

## Where Problems Come From

| Symptom | Primary stage | Secondary |
| --- | --- | --- |
| Harsh metallic / robotic timbre | **VoxCPM `generate`** (`render_episode.py`) | Mild post denoise can soften, not replace a bad clone |
| One host much louder | Per-turn peak variance + dual references | Episode loudnorm after concat |
| Clicks / DC / rumble | Raw wav / room in reference | High-pass + DC remove |
| Over-bright sibilance | Clone + reference | Soft de-ess / mild FFT denoise |

**Do not expect** karaoke, waveform overlay, or AAC mux to fix 电音.

## Pipeline (ordered)

```text
A. Reference hygiene (once per host)
   clean_reference_audio / short clean clips
        ↓
B. Render (per turn)
   run_episode_render.py → turn_NNN.wav
   peak boost only if peak < 0.45 → 0.88
        ↓
C. QC gate (human)
   check_episode.py → trim / rerender / accept
        ↓
D. Master (this doc)  ← required for formal YouTube packs
   per-turn cleanup → concat → program loudnorm
   → 000_episode_XXX.master.wav (+ report)
        ↓
E. Subtitles + compose + export
   use master.wav as compose audio input
```

### A — Reference hygiene

- Prefer cleaned mono references (already in `assets/voices/...`).
- Keep clips short (~8–15s), one speaker, no music beds.
- Re-extract if the clone sounds like the wrong person or has room reverb.

### B — Render settings (anti-电音 defaults for dialogue)

| Knob | Formal default | Notes |
| --- | --- | --- |
| `cfgValue` | **2.15** (podcast) | Higher (2.35+) often sharper / more metallic |
| `inferenceTimesteps` | **10** | Keep unless quality experiments say otherwise |
| `normalize` (VoxCPM) | `False` | Avoid model-side surprise gain |
| `denoise` (VoxCPM) | **try `True` when ZipEnhancer available** | Else leave False and rely on stage D |
| control text | short `characterProfiles` | Long cues worsen instability |

Full episode renders: load the model **once** (`run_episode_render.py`), audiobook-style.

### C — QC gate

Unchanged: trailing silence, CHECK_LONG, ASR vs script.
Human accepts turns before mastering.

### D — Master chain (implemented by `master_episode_audio.py`)

**Per turn** (preserve gaps later):

1. Mono mixdown if needed
2. DC remove
3. High-pass **80 Hz** (speech)
4. Mild FFT denoise (`afftdn`, conservative) — softens clone grit / 电音 edges
5. Soft compressor (gentle ratio) for host-to-host evenness inside a turn
6. True-peak ceiling via `alimiter` (~−1.0 dBTP local)

**Episode:**

7. Concatenate turns with manifest `interTurnSilenceSec`
8. **EBU R128** two-pass `loudnorm`:
   - Integrated target **−16 LUFS** (dialogue / YouTube-friendly)
   - True peak **≤ −1.5 dBTP**
   - LRA target **~11 LU**
9. Write `000_episode_XXX.master.wav` (48 kHz PCM)
10. Write `000_episode_XXX.master_report.json` (measured I/TP/LRA before & after)

**Non-goals of stage D:**

- Pitch correction, Autotune, stereo widening
- Aggressive noise gates that chop consonants
- Replacing a failed clone — that requires **rerender**

### E — Video packaging

`compose_episode_video.py` and export must use **`master.wav`** when present; fall back to `raw.wav` only for pilots.

## Commands

```powershell
$py = ".\.conda-env\python.exe"
$ws = "workspace/shows/series_b/episode_001"
$man = "$ws/000_episode_001.episode_manifest.json"

# After human audio QC approval:
& $py workspace/shows/tools/master_episode_audio.py --manifest $man

# Optional stronger denoise (listen first):
& $py workspace/shows/tools/master_episode_audio.py --manifest $man --denoise-strength 12

# Then subtitles/compose against master:
& $py workspace/shows/tools/compose_episode_video.py `
  --show series_b --episode episode_001 --workspace $ws `
  --audio "$ws/000_episode_001.master.wav"
```

## Acceptance checklist

- [ ] `master_report.json` shows integrated loudness within **±1 LU** of −16 LUFS
- [ ] True peak ≤ **−1.5 dBTP**
- [ ] No obvious pumping / underwater denoise
- [ ] Riley vs Sam perceived loudness even on phone speaker
- [ ] If 电音 still severe: flag turns, **rerender** with cfg 2.15 + cleaner ref, then remaster

## Relation to audiobook

| | Audiobook | ELR dialogue |
| --- | --- | --- |
| Default post | Peak boost quiet segments only | Full master chain before YouTube |
| Loudness | No chapter LUFS by default | −16 LUFS program target |
| Why | Literary narration already even | Dual hosts + clone variance |

## Revision history

- 2026-07-17: Initial formal dialogue mastering contract + tool.
