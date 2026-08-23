from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

from worker.classics.brand_voice import render_brand_voice
from worker.classics.config import parse_book_config
from worker.classics.io import sha256_file


class _FakeModel:
    class _TtsModel:
        sample_rate = 24_000

    tts_model = _TtsModel()

    calls: list[dict[str, object]] = []

    def generate(self, *, text: str, **settings: object) -> np.ndarray:
        self.calls.append(settings)
        duration = 0.45 if text.startswith("Welcome") else 0.55
        time = np.arange(round(duration * self.tts_model.sample_rate)) / self.tts_model.sample_rate
        return (0.2 * np.sin(2 * np.pi * 220 * time)).astype(np.float32)


def test_brand_voice_uses_configured_riley_profile_and_writes_trace(tmp_path: Path) -> None:
    reference = tmp_path / "assets" / "voices" / "series_b" / "riley_reference_clean.wav"
    reference.parent.mkdir(parents=True)
    sf.write(reference, np.zeros(2_400, dtype=np.float32), 24_000)
    (tmp_path / "pretrained_models" / "VoxCPM2").mkdir(parents=True)
    payload = {
        "schema": "classic-listening-book-v1",
        "book": {"slug": "fixture", "title": "Fixture", "author": "Author", "language": "en", "chapterCount": 1},
        "source": {
            "path": "fixture.epub",
            "sha256": "0" * 64,
            "chapterHeadingPattern": r"^CHAPTER\\s+([IVXLCDM]+)$",
            "boilerplateStopMarkers": ["END"],
        },
        "voice": {
            "mode": "single",
            "profileId": "classic-listening-riley-narrator",
            "referencePath": "assets/voices/series_b/riley_reference_clean.wav",
            "referenceSha256": sha256_file(reference),
            "globalControl": "same Riley narrator",
            "cfgValue": 2.35,
            "inferenceTimesteps": 10,
            "normalize": False,
            "denoise": False,
        },
        "render": {"modelId": "pretrained_models/VoxCPM2", "device": "cpu", "sampleRate": 48_000},
        "mastering": {},
        "branding": {
            "introVoicePath": "public/classics/fixture/intro.wav",
            "outroVoicePath": "public/classics/fixture/outro.wav",
            "introSpokenText": "Welcome to Classic Listening.",
            "outroSpokenText": "Thank you for listening.",
            "voiceCfgValue": 2.15,
            "voiceInferenceTimesteps": 12,
            "outroVoiceCfgValue": 2.0,
            "outroVoiceInferenceTimesteps": 14,
        },
        "visual": {},
        "export": {},
    }
    config = parse_book_config(payload, tmp_path / "fixture.json")

    model = _FakeModel()
    trace = render_brand_voice(tmp_path, config, model_factory=lambda *_: model)

    assert [clip["kind"] for clip in trace["clips"]] == ["intro", "outro"]
    assert all(clip["reused"] is False for clip in trace["clips"])
    assert all(clip["durationSec"] > 0.9 for clip in trace["clips"])
    persisted = json.loads((tmp_path / trace["tracePath"]).read_text(encoding="utf-8"))
    assert persisted["voiceProfile"]["id"] == "classic-listening-riley-narrator"
    assert persisted["referenceSha256"] == sha256_file(reference)
    assert persisted["generationSettings"] == {
        "cfgValue": 2.15,
        "inferenceTimesteps": 12,
        "normalize": False,
        "denoise": False,
    }
    assert [call["cfg_value"] for call in model.calls] == [2.15, 2.0]
    assert [call["inference_timesteps"] for call in model.calls] == [12, 14]
    assert persisted["clips"][0]["generationSettings"] == {
        "cfgValue": 2.15,
        "inferenceTimesteps": 12,
    }
    assert persisted["clips"][1]["generationSettings"] == {
        "cfgValue": 2.0,
        "inferenceTimesteps": 14,
    }
