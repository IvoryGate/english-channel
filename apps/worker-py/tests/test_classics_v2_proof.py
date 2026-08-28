from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from worker.classics.paths import ClassicPaths
from worker.classics.v2_chapter import _chapter_audio_source, _voice_variant_metadata
from worker.classics.v2_proof import V2ProofError, _loudnorm_second_pass_filter, scene_timeline


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


def test_chapter_audio_source_supports_canonical_production(tmp_path: Path) -> None:
    paths = ClassicPaths(tmp_path, "persuasion")
    segment_dir, raw_audio = _chapter_audio_source(paths, 1, "production")
    assert segment_dir == paths.segment_audio_dir(1)
    assert raw_audio == paths.raw_audio(1)


def test_chapter_audio_source_preserves_isolated_previews(tmp_path: Path) -> None:
    paths = ClassicPaths(tmp_path, "persuasion")
    segment_dir, raw_audio = _chapter_audio_source(paths, 1, "voice-b")
    assert segment_dir == paths.audio_dir(1) / "previews" / "voice-b" / "segments"
    assert raw_audio == paths.audio_dir(1) / "previews" / "voice-b.wav"


def test_production_voice_metadata_uses_current_config() -> None:
    config = type(
        "Config",
        (),
        {
            "voice": {
                "profileId": "classic-listening-mia-narrator",
                "referenceSha256": "a" * 64,
                "cfgValue": 1.65,
                "inferenceTimesteps": 32,
            }
        },
    )()
    assert _voice_variant_metadata(config, "production") == {
        "name": "production",
        "profileId": "classic-listening-mia-narrator",
        "referenceSha256": "a" * 64,
        "cfgValue": 1.65,
        "inferenceTimesteps": 32,
    }
    assert _voice_variant_metadata(config, "voice-b") == {
        "name": "voice-b",
        "parametersSource": "preview-generation-trace",
    }


def test_loudnorm_second_pass_uses_measured_values() -> None:
    value = _loudnorm_second_pass_filter(
        -16.0,
        -1.5,
        11.0,
        {
            "input_i": "-18.20",
            "input_tp": "-0.60",
            "input_lra": "3.10",
            "input_thresh": "-28.40",
            "target_offset": "-0.10",
        },
    )
    assert "I=-16.0:TP=-1.5:LRA=11.0" in value
    assert "measured_I=-18.20" in value
    assert "measured_TP=-0.60" in value
    assert "offset=-0.10:linear=true" in value


def test_loudnorm_second_pass_rejects_incomplete_measurements() -> None:
    with pytest.raises(V2ProofError, match="incomplete"):
        _loudnorm_second_pass_filter(-16.0, -1.5, 11.0, {"input_i": "-18.20"})
