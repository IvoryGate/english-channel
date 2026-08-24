from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from worker.classics.v2_proof import scene_timeline


def test_scene_timeline_places_boundaries_in_inter_segment_silence(tmp_path: Path) -> None:
    sample_rate = 1000
    manifest = {
        "segments": [
            {"id": "001", "filename": "001.wav"},
            {"id": "002", "filename": "002.wav"},
            {"id": "003", "filename": "003.wav"},
        ]
    }
    for filename, seconds in (("001.wav", 2), ("002.wav", 3), ("003.wav", 4)):
        sf.write(tmp_path / filename, np.zeros(sample_rate * seconds, dtype=np.float32), sample_rate)
    duration, boundaries = scene_timeline(
        manifest, tmp_path, ["001", "002", "003"], ["001", "002", "003"], 0.4
    )
    assert duration == pytest.approx(9.8)
    assert boundaries == pytest.approx([2.2, 5.6])
