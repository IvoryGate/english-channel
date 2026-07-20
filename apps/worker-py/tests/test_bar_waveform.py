from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.bar_waveform import _frame_bar_peaks  # noqa: E402


def test_mixed_speech_like_signal_spreads_across_bands() -> None:
    sample_rate = 44100
    seconds = np.linspace(0, 0.12, int(0.12 * sample_rate), endpoint=False)
    mixed = (
        np.sin(2 * np.pi * 180 * seconds)
        + np.sin(2 * np.pi * 520 * seconds)
        + np.sin(2 * np.pi * 1200 * seconds)
        + np.sin(2 * np.pi * 2600 * seconds)
    ).astype(np.float32)

    peaks = _frame_bar_peaks(mixed, 24, sample_rate)
    active = int(np.sum(peaks > 0.28))

    assert peaks.shape == (24,)
    assert active >= 8
