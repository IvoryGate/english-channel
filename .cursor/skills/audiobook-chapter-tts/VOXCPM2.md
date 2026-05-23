# VoxCPM2 Notes

## Voice Cloning And Style Control

VoxCPM2 uses `reference_wav_path` for reference-only voice cloning. Style and emotion control are text instructions in parentheses before the target text.

Use:

```text
(same cloned narrator, slightly slower, quiet deadpan amusement) "You want to tell me..."
```

Avoid adding a long global instruction before short target text. It can cause extra generated speech after the intended sentence.

`globalControl` in the manifest is documentation and consistency for humans/agents. `compose_control` does **not** repeat it in every `ttsText`. Per segment, only a short `deliveryCue` (and `same cloned narrator` for narration) is sent to the model. Voice identity comes from `reference_wav_path`.

## Pacing (generation-time, opt-in)

VoxCPM2 has no `speed` parameter. Optional knobs:

1. **`paceCue`** in the manifest — only applied when the key is present; omitted by default.
2. **`referenceTempoRatio`** when cleaning reference audio (`0.88`–`0.94` slows cloned prosody before render).

## Dialogue consistency

Use **`characterProfiles`** in the manifest: one short stable cue per speaker. Dialogue segments combine profile + short `deliveryCue`; very long dialogue uses the profile only unless `renderPolicy: include_delivery_cue`. See `SEGMENTATION.md` and `CONTROLS.md`.

## Post-render peak boost

After each segment is generated, `normalize_segment_peak` boosts only very quiet WAVs (peak < 0.45 → 0.88). Do not enable chapter-wide RMS normalization in scripts unless the user explicitly asks.

## Default Generation Settings

- `model_id`: `pretrained_models/VoxCPM2`
- `device`: `cuda`
- `optimize`: `False`
- `load_denoiser`: `False`
- `cfg_value`: `2.25` (override per chapter with manifest `cfgValue`, e.g. `2.35`)
- `inference_timesteps`: `10`
- `normalize`: `False`
- `denoise`: `False`

## Reference Audio

Clean reference audio by default before cloning:

- mono mixdown
- DC removal
- 80Hz high-pass
- conservative spectral subtraction
- head/tail trim
- peak normalize

If cleaned reference changes the timbre too much, rerun with the original reference.

## Bad Case Handling

Suspicious signs:

- segment duration much longer than neighboring segments
- high seconds-per-word ratio
- speech continues after the provided text
- unintelligible words not present in source

First response:

1. Regenerate the affected segment only (`render_chapter.py --segments <id>`).
2. Use compact control for short or medium-short text.
3. Rely on automatic `max_len` (128 for ≤12 words, 56 for ≤4 words) or set per-segment `maxLen`.
4. For flat long dialogue, try `renderPolicy: include_delivery_cue`.
5. Recompose the full chapter from existing segment WAVs when the user asked for rerender.

Troubleshooting table: `CONTROLS.md`.
