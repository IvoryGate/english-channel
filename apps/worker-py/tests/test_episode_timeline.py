from __future__ import annotations

import json
import shutil
import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "workspace/shows/tools"))
sys.path.insert(0, str(ROOT / ".cursor/skills/audiobook-chapter-tts/scripts"))

from episode_artifacts import artifact_paths, master_turn_wav_path, turn_wav_path
from episode_timeline import (
    manifest_gaps, master_timeline_record, resolve_episode_timeline, wav_duration,
)
from master_episode_audio import concat_turns, resolve_playback_tempo
from media.align_media_words import align_turn_clips_scripted
from prepare_episode_youtube_packaging import episode_timeline, resolve_markers


def wav(path: Path, seconds: float, sample: bytes = b"\x01\x00") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        output.writeframes(sample * round(seconds * 48000))
    return path


def fixture(root: Path) -> tuple[dict, list[Path]]:
    manifest = {"episodeId": "episode_001", "renderSettings": {"interTurnSilenceSec": 0.3,
                "outputAudio": "000_episode_001.raw.wav"},
                "turns": [{"id": f"p{i:03d}", "order": i, "filename": f"turn_{i:03d}.wav",
                           "speaker": "Nora", "text": "Hello there.", "pauseAfterSec": gap}
                          for i, gap in enumerate([0.1, 0.7, 99.0], 1)]}
    clips = [wav(turn_wav_path(root, turn["filename"]), 1) for turn in manifest["turns"]]
    return manifest, clips


def legacy_master(root: Path, manifest: dict, *, new_contract: bool = False) -> list[Path]:
    paths = artifact_paths(root, manifest["episodeId"])
    clips = [wav(master_turn_wav_path(root, turn["id"], turn["filename"]), 2)
             for turn in manifest["turns"]]
    duration = 6.8 if new_contract else 6.6
    wav(paths["masterWav"], duration)
    report = {"episodeId": manifest["episodeId"], "sourceTurns": 3,
              "gapSec": 0.3, "durationSec": duration, "playbackTempo": 0.5}
    if new_contract:
        report["timeline"] = master_timeline_record(manifest, clips, paths["masterWav"])
    paths["masterReport"].parent.mkdir(parents=True, exist_ok=True)
    paths["masterReport"].write_text(json.dumps(report), encoding="utf-8")
    return clips


def test_raw_timeline_honors_variable_pauses_and_no_trailing_gap(tmp_path: Path) -> None:
    manifest, _ = fixture(tmp_path)
    rows = episode_timeline(tmp_path, manifest)
    assert manifest_gaps(manifest) == [0.1, 0.7]
    assert [row["startSec"] for row in rows] == pytest.approx([0, 1.1, 2.8])
    assert rows[-1]["endSec"] == pytest.approx(3.8)


def test_legacy_master_clock_shared_by_chapters_and_subtitles(tmp_path: Path) -> None:
    manifest, _ = fixture(tmp_path)
    clips = legacy_master(tmp_path, manifest)
    timeline, resolved_clips = resolve_episode_timeline(tmp_path, manifest)
    alignment = align_turn_clips_scripted(clips, manifest["turns"], gaps_sec=timeline["gapsSec"])
    assert resolved_clips == clips
    assert timeline["source"] == "legacy-mastered-turns-duration-validated"
    assert timeline["gapsSec"] == [0.3, 0.3]  # actual legacy audio, not newly interpreted manifest pauses
    assert timeline["durationSec"] == pytest.approx(6.6)
    rows = episode_timeline(tmp_path, manifest)
    assert rows[-1]["startSec"] == pytest.approx(4.6)  # raw would incorrectly be 2.8
    assert alignment["turns"][-1]["words"][0]["start"] == pytest.approx(4.6)
    markers = resolve_markers(rows, [{"turnId": "p003", "label": "Last"}], intro_offset_sec=5)
    assert markers[-1]["videoTimestampSec"] == pytest.approx(9.6)


def test_new_master_contract_uses_measured_audio_and_variable_gaps(tmp_path: Path) -> None:
    manifest, _ = fixture(tmp_path)
    legacy_master(tmp_path, manifest, new_contract=True)
    timeline, _ = resolve_episode_timeline(tmp_path, manifest)
    assert timeline["source"] == "mastered-turns-hash-verified"
    assert timeline["turns"][-1]["startSec"] == pytest.approx(4.8)


@pytest.mark.parametrize("change", ["text", "pause", "clip", "program"])
def test_new_master_rejects_stale_inputs(tmp_path: Path, change: str) -> None:
    manifest, _ = fixture(tmp_path)
    clips = legacy_master(tmp_path, manifest, new_contract=True)
    if change == "text":
        manifest["turns"][0]["text"] = "Different speech."
    elif change == "pause":
        manifest["turns"][0]["pauseAfterSec"] = 0.5
    elif change == "clip":
        wav(clips[0], 2, b"\x02\x00")  # same duration, different content
    else:
        wav(artifact_paths(tmp_path, manifest["episodeId"])["masterWav"], 6.8, b"\x02\x00")
    with pytest.raises(ValueError, match="stale"):
        resolve_episode_timeline(tmp_path, manifest)


def test_existing_master_never_falls_back_to_raw_when_evidence_missing(tmp_path: Path) -> None:
    manifest, _ = fixture(tmp_path)
    wav(artifact_paths(tmp_path, manifest["episodeId"])["masterWav"], 5)
    with pytest.raises(FileNotFoundError, match="report"):
        resolve_episode_timeline(tmp_path, manifest)


def test_legacy_master_rejects_duration_drift(tmp_path: Path) -> None:
    manifest, _ = fixture(tmp_path)
    clips = legacy_master(tmp_path, manifest)
    wav(clips[0], 1)
    with pytest.raises(ValueError, match="does not match program"):
        resolve_episode_timeline(tmp_path, manifest)


@pytest.mark.parametrize("gap", [-1, float("nan"), float("inf"), True])
def test_invalid_pauses_are_not_silently_applied(tmp_path: Path, gap: float) -> None:
    manifest, _ = fixture(tmp_path)
    manifest["turns"][0]["pauseAfterSec"] = gap
    with pytest.raises(ValueError, match="finite and nonnegative"):
        manifest_gaps(manifest)


def test_tempo_budget_preserves_actual_variable_pause_total() -> None:
    card = {"format": "flagship_40", "formatContract": {"targetMinutes": [38, 42]}}
    tempo = resolve_playback_tempo(card, clip_durations_sec=[1000, 1000], gap_sec=0.3, gaps_sec=[20])
    assert tempo == pytest.approx(round(2000 / 2260, 6))


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg required")
def test_real_concat_raw_master_and_subtitle_clock_agree(tmp_path: Path) -> None:
    from check_episode import build_episode_qc_report
    from repair_episode_qc import compose_raw_wav

    manifest, clips = fixture(tmp_path)
    gaps = manifest_gaps(manifest)
    master = tmp_path / "master.wav"
    manifest_path = tmp_path / "000_episode_001.episode_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    raw = compose_raw_wav(manifest_path)
    concat_turns(clips, master, gap_sec=0.3, gaps_sec=gaps)
    alignment = align_turn_clips_scripted(clips, manifest["turns"], gaps_sec=gaps)
    qc = build_episode_qc_report(tmp_path, manifest)
    assert qc["chapter"]["composeDriftSec"] == 0
    assert wav_duration(raw) == pytest.approx(3.8, abs=0.003)
    assert wav_duration(master) == pytest.approx(3.8, abs=0.003)
    assert alignment["durationSec"] == pytest.approx(3.8)
    assert alignment["turns"][-1]["words"][0]["start"] == pytest.approx(2.8)
