# VoxCPM2 Notes

## Voice Cloning And Style Control

VoxCPM2 uses `reference_wav_path` for reference-only voice cloning. Style and emotion control are text instructions in parentheses before the target text.

Use:

```text
(same cloned narrator, slightly slower, quiet deadpan amusement) "You want to tell me..."
```

Avoid adding a long global instruction before short target text. It can cause extra generated speech after the intended sentence.

## Default Generation Settings

- `model_id`: `pretrained_models/VoxCPM2`
- `device`: `cuda`
- `optimize`: `False`
- `load_denoiser`: `False`
- `cfg_value`: `2.25`
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

1. Regenerate the affected segment only.
2. Use compact control for short or medium-short text.
3. Apply `max_len` for 12 words or fewer.
4. Recompose the full chapter from existing segment WAVs.
