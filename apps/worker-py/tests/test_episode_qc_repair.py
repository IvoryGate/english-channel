from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "workspace" / "shows" / "tools"))

from check_episode import blocking_segment_ids, has_blocking_qc_issues  # noqa: E402
from prepare_episode_manifest import target_max_len  # noqa: E402
from repair_episode_qc import advance_seed_offsets, trim_trailing_silence, try_quiet_repair  # noqa: E402
from worker.tts.trace import TRACE_SCHEMA, sha256_file, turn_trace_path  # noqa: E402


def test_target_max_len_single_word_tight_cap() -> None:
    assert target_max_len(1) == 28
    assert target_max_len(2) == 48
    assert target_max_len(12) == 128
    assert target_max_len(20) is None


def test_blocking_segment_ids_short_too_long() -> None:
    report = {
        "chapter": {"flags": ["HAS_REVIEW_SEGMENTS"]},
        "segments": [
            {"id": "p001", "flags": [], "status": "ok"},
            {"id": "p089", "flags": ["CHECK_LONG", "SHORT_TOO_LONG"], "status": "review"},
            {"id": "p081", "flags": ["CHECK_LONG"], "status": "review"},
        ],
    }
    assert blocking_segment_ids(report) == ["p089"]
    assert has_blocking_qc_issues(report) is True


def test_check_long_alone_not_blocking() -> None:
    report = {
        "chapter": {"flags": ["HAS_REVIEW_SEGMENTS"]},
        "segments": [{"id": "p081", "flags": ["CHECK_LONG"], "status": "review"}],
    }
    assert blocking_segment_ids(report) == []
    assert has_blocking_qc_issues(report) is False


def test_advance_seed_offsets_changes_only_selected_turns() -> None:
    manifest = {
        "turns": [
            {"id": "p001"},
            {"id": "p002", "ttsSeedOffset": 2000},
            {"id": "p003"},
        ]
    }

    advance_seed_offsets(manifest, ["p001", "p002"])

    assert manifest["turns"][0]["ttsSeedOffset"] == 1000
    assert manifest["turns"][1]["ttsSeedOffset"] == 3000
    assert "ttsSeedOffset" not in manifest["turns"][2]


def test_quiet_repair_updates_wav_trace_and_manifest(tmp_path: Path) -> None:
    workspace = tmp_path / "episode"
    wav = workspace / "audio" / "turns" / "001_riley.wav"
    wav.parent.mkdir(parents=True)
    sf.write(wav, np.asarray([-0.3, 0.15], dtype=np.float32), 24_000, subtype="FLOAT")
    trace_path = turn_trace_path(wav)
    trace_path.write_text(
        json.dumps({"schema": TRACE_SCHEMA, "outputSha256": sha256_file(wav), "peak": 0.3}),
        encoding="utf-8",
    )
    segment = {
        "id": "p001",
        "order": 1,
        "filename": "001_riley.wav",
        "text": "A valid sentence with enough words for ordinary timing checks.",
        "wordCount": 10,
        "flags": ["TOO_QUIET"],
    }
    manifest = {"rendered": [{"id": "p001", "peak": 0.3, "outputSha256": "old"}]}

    assert try_quiet_repair(workspace, segment, manifest) is True

    repaired, _ = sf.read(wav, dtype="float32")
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert float(np.max(np.abs(repaired))) == pytest.approx(0.88, abs=1e-5)
    assert trace["outputSha256"] == sha256_file(wav)
    assert trace["postProcessing"][-1]["kind"] == "quiet-peak-normalization"
    assert manifest["rendered"][0]["outputSha256"] == sha256_file(wav)


def test_trailing_silence_trim_preserves_float_pcm(tmp_path: Path) -> None:
    wav = tmp_path / "turn.wav"
    speech = np.full(24_000, 0.2, dtype=np.float32)
    silence = np.zeros(24_000, dtype=np.float32)
    sf.write(wav, np.concatenate([speech, silence]), 24_000, subtype="FLOAT")

    assert trim_trailing_silence(wav) is True

    assert sf.info(wav).subtype == "FLOAT"
