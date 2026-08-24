from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from worker.classics.audio_metrics import audio_texture_metrics


def test_high_band_ratio_distinguishes_high_frequency_energy(tmp_path: Path) -> None:
    sample_rate = 48000
    time = np.arange(sample_rate, dtype=np.float32) / sample_rate
    low_path = tmp_path / "low.wav"
    high_path = tmp_path / "high.wav"
    sf.write(low_path, 0.2 * np.sin(2 * np.pi * 400 * time), sample_rate)
    sf.write(high_path, 0.2 * np.sin(2 * np.pi * 10000 * time), sample_rate)

    low = audio_texture_metrics(low_path)
    high = audio_texture_metrics(high_path)

    assert low["highBandRatio8k"] < 0.01
    assert high["highBandRatio8k"] > 0.9
