from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


def audio_texture_metrics(path: Path) -> dict[str, Any]:
    info = sf.info(path)
    sample_rate = int(info.samplerate)
    max_analysis_seconds = 120
    if info.frames <= sample_rate * max_analysis_seconds:
        audio, _ = sf.read(path, dtype="float32", always_2d=True)
    else:
        window_seconds = 20
        window_frames = sample_rate * window_seconds
        starts = np.linspace(0, info.frames - window_frames, 6, dtype=np.int64)
        chunks: list[np.ndarray] = []
        with sf.SoundFile(path) as handle:
            for start in starts:
                handle.seek(int(start))
                chunks.append(handle.read(window_frames, dtype="float32", always_2d=True))
        audio = np.concatenate(chunks, axis=0)
    mono = audio.mean(axis=1)
    if mono.size == 0:
        raise ValueError(f"Audio is empty: {path}")
    mono = mono - float(np.mean(mono))
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(np.square(mono))))
    windowed = mono * np.hanning(mono.size)
    power = np.square(np.abs(np.fft.rfft(windowed)))
    frequencies = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)
    audible = power[(frequencies >= 80.0) & (frequencies <= 20000.0)]
    audible_power = float(np.sum(audible)) or 1.0

    def band_ratio(low_hz: float) -> float:
        band = power[(frequencies >= low_hz) & (frequencies <= 20000.0)]
        return float(np.sum(band) / audible_power)

    weighted_power = power[(frequencies >= 80.0) & (frequencies <= 20000.0)]
    weighted_frequency = frequencies[(frequencies >= 80.0) & (frequencies <= 20000.0)]
    centroid = float(np.sum(weighted_frequency * weighted_power) / audible_power)
    zero_crossings = float(np.mean(np.abs(np.diff(np.signbit(mono)))))
    return {
        "path": str(path),
        "durationSec": round(float(info.frames / sample_rate), 3),
        "analyzedDurationSec": round(float(mono.size / sample_rate), 3),
        "sampleRate": int(sample_rate),
        "peakDbfs": round(20.0 * math.log10(max(peak, 1e-12)), 3),
        "rmsDbfs": round(20.0 * math.log10(max(rms, 1e-12)), 3),
        "highBandRatio8k": round(band_ratio(8000.0), 8),
        "highBandRatio12k": round(band_ratio(12000.0), 8),
        "spectralCentroidHz": round(centroid, 2),
        "zeroCrossingRate": round(zero_crossings, 6),
    }
