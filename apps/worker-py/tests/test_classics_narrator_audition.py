from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from worker.classics.narrator_audition import (
    NarratorAuditionError,
    load_audition_config,
    run_narrator_audition,
)


class FakeModel:
    class TtsModel:
        sample_rate = 16000

    tts_model = TtsModel()

    def generate(self, **kwargs):
        seconds = max(0.2, len(str(kwargs["text"])) / 200.0)
        frames = round(self.tts_model.sample_rate * seconds)
        time = np.arange(frames, dtype=np.float32) / self.tts_model.sample_rate
        return (0.05 * np.sin(2 * np.pi * 220 * time)).astype(np.float32)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture(root: Path) -> Path:
    references = []
    for index in range(3):
        path = root / "voices" / f"voice-{index}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, np.zeros(1600, dtype=np.float32), 16000)
        references.append(path)
    cases = {
        "schema": "classic-listening-audio-acceptance-v1",
        "thresholds": {
            "minimumAsrSimilarity": 0.98,
            "maximumTruePeakDbtp": -1.5,
            "maximumClippedSamples": 0,
            "requiredBlindReviewers": 1,
        },
        "cases": [
            {"id": "n", "dimension": "narration", "text": "Morning light filled the room."},
            {"id": "d", "dimension": "dialogue", "text": "I remember it clearly, she said."},
            {"id": "s", "dimension": "fragile_short_line", "text": "Yes, certainly."},
            {"id": "l", "dimension": "long_sentence", "text": "Although the letter arrived early, she waited until the visitors departed before opening it."},
            {"id": "nd", "dimension": "names_and_dates", "text": "Eleanor wrote on the twenty-third of September."},
            {"id": "si", "dimension": "sibilants", "text": "Soft sea winds crossed the terrace."},
        ],
    }
    cases_path = root / "configs" / "cases.json"
    cases_path.parent.mkdir(parents=True, exist_ok=True)
    cases_path.write_text(json.dumps(cases), encoding="utf-8")
    config = {
        "schema": "classic-listening-narrator-audition-v1",
        "auditionId": "fixture",
        "bookSlug": "persuasion",
        "casesRef": "configs/cases.json",
        "outputRoot": "workspace/audition",
        "modelId": "models/voxcpm",
        "device": "cuda",
        "sampleRate": 48000,
        "silenceBetweenCasesSec": 0.1,
        "candidates": [
            {
                "id": f"candidate-{index}",
                "blindCode": f"voice-{chr(97 + index)}",
                "sourceProfileId": f"profile-{index}",
                "referencePath": path.relative_to(root).as_posix(),
                "referenceSha256": _sha256(path),
                "promptText": "A clean reference sentence.",
                "cfgValue": 2.0,
                "inferenceTimesteps": 10,
                "normalize": False,
                "denoise": False,
                "provenanceStatus": "fixture",
            }
            for index, path in enumerate(references)
        ],
    }
    config_path = root / "configs" / "audition.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def test_narrator_audition_builds_three_blind_review_files(tmp_path: Path) -> None:
    config_path = _write_fixture(tmp_path)

    report = run_narrator_audition(
        tmp_path,
        config_path,
        model_factory=lambda *_: FakeModel(),
    )

    assert report["status"] == "awaiting_blind_review"
    assert len(report["candidates"]) == 3
    for code in ("voice-a", "voice-b", "voice-c"):
        assert (tmp_path / "workspace" / "audition" / "review" / f"{code}.wav").is_file()
    mapping = json.loads((tmp_path / "workspace" / "audition" / "private-mapping.json").read_text())
    assert mapping["mapping"]["voice-a"] == "candidate-0"


def test_narrator_audition_dry_run_does_not_load_model(tmp_path: Path) -> None:
    config_path = _write_fixture(tmp_path)

    report = run_narrator_audition(
        tmp_path,
        config_path,
        dry_run=True,
        model_factory=lambda *_: pytest.fail("model must not load"),
    )

    assert report["candidateCount"] == 3
    assert report["caseCount"] == 6
    assert not (tmp_path / "workspace").exists()


def test_narrator_audition_rejects_reference_hash_drift(tmp_path: Path) -> None:
    config_path = _write_fixture(tmp_path)
    payload = load_audition_config(config_path)
    payload["candidates"][0]["referenceSha256"] = "0" * 64
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(NarratorAuditionError, match="hash mismatch"):
        run_narrator_audition(tmp_path, config_path, dry_run=True)
