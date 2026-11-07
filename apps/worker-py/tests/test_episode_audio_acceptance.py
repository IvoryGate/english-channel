from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[3] / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

import episode_audio_acceptance as gate  # noqa: E402
import master_episode_audio as mastering  # noqa: E402
import pack_episode as pack  # noqa: E402
import compose_episode_video as compose  # noqa: E402
from episode_artifacts import artifact_paths, master_turn_wav_path, turn_wav_path  # noqa: E402
from episode_timeline import master_timeline_record  # noqa: E402
from export_episode_to_youtube_dir import verify_export_package  # noqa: E402

MEASUREMENTS = {"integratedLufs": -16.0, "truePeakDb": -2.0, "lra": 3.0, "threshold": -26.0}
SOURCES = {"manifest": "a" * 64, "rawTurns": "b" * 64}


def record(monkeypatch, path: Path, *, stage="master", measurements=None, sources=None):
    monkeypatch.setattr(gate, "measure_loudness", lambda _: measurements or dict(MEASUREMENTS))
    monkeypatch.setattr(gate, "ffmpeg_version", lambda: "ffmpeg fixture")
    return gate.measure_audio_acceptance(path, stage=stage, sources=sources or SOURCES)


@pytest.mark.parametrize("peak", [-1.33, -1.41, -1.49])
def test_observed_over_ceiling_masters_fail_even_with_good_integrated(monkeypatch, tmp_path, peak):
    audio = tmp_path / "master.wav"
    audio.write_bytes(b"master")
    evidence = record(monkeypatch, audio, measurements={**MEASUREMENTS, "truePeakDb": peak})
    assert evidence["status"] == "failed"
    evidence["status"], evidence["errors"] = "passed", []
    with pytest.raises(ValueError, match="true peak"):
        gate.validate_audio_acceptance(evidence, audio, stage="master")


@pytest.mark.parametrize("key,value", [("integratedLufs", -17.01), ("integratedLufs", -14.99),
    ("integratedLufs", None), ("truePeakDb", float("nan")), ("truePeakDb", float("inf")),
    ("lra", True), ("threshold", "-26")])
def test_unknown_or_out_of_range_measurements_fail(key, value):
    assert gate.acceptance_errors({**MEASUREMENTS, key: value})


@pytest.mark.parametrize("integrated", [-17.0, -15.0])
def test_documented_boundaries_pass(integrated):
    assert not gate.acceptance_errors({**MEASUREMENTS, "integratedLufs": integrated, "truePeakDb": -1.5})


def test_stale_audio_sources_and_policy_cannot_reuse_pass(monkeypatch, tmp_path):
    audio = tmp_path / "master.wav"
    audio.write_bytes(b"before")
    evidence = record(monkeypatch, audio)
    gate.validate_audio_acceptance(evidence, audio, stage="master", sources=SOURCES)
    with pytest.raises(ValueError, match="source changed"):
        gate.validate_audio_acceptance(evidence, audio, stage="master", sources={**SOURCES, "manifest": "c" * 64})
    audio.write_bytes(b"after!")  # Same length replacement is still stale.
    with pytest.raises(ValueError, match="artifact changed"):
        gate.validate_audio_acceptance(evidence, audio, stage="master")
    audio.write_bytes(b"before")
    evidence["policy"]["truePeakDb"] = 0.0
    with pytest.raises(ValueError, match="policy"):
        gate.validate_audio_acceptance(evidence, audio, stage="master")


def test_mastering_preserves_failed_output_and_report_then_stops(monkeypatch, tmp_path):
    episode = "episode_001"
    manifest_path = tmp_path / f"000_{episode}.episode_manifest.json"
    manifest_path.write_text(json.dumps({"episodeId": episode, "turns": [{"id": "t1", "filename": "turn.wav"}]}), encoding="utf-8")
    paths = artifact_paths(tmp_path, episode)
    (tmp_path / "audio" / "turns").mkdir(parents=True)
    (tmp_path / "audio" / "turns" / "turn.wav").write_bytes(b"raw")
    monkeypatch.setattr(mastering, "master_sources", lambda *_: dict(SOURCES))
    monkeypatch.setattr(mastering, "probe_duration_sec", lambda _: 4.0)
    monkeypatch.setattr(mastering, "master_turn", lambda src, dest, **_: dest.write_bytes(b"clean"))
    monkeypatch.setattr(mastering, "concat_turns", lambda clips, dest, **_: dest.write_bytes(b"concat"))
    monkeypatch.setattr(mastering, "loudnorm_two_pass", lambda src, dest, **_: (dest.write_bytes(b"failed master") and {}))
    monkeypatch.setattr(mastering, "master_timeline_record", lambda *_: {})
    monkeypatch.setattr(mastering, "measure_loudness", lambda _: dict(MEASUREMENTS))
    monkeypatch.setattr(gate, "measure_loudness", lambda _: {**MEASUREMENTS, "truePeakDb": -1.33})
    monkeypatch.setattr(gate, "ffmpeg_version", lambda: "ffmpeg fixture")
    with pytest.raises(ValueError, match="true peak"):
        mastering.master_episode(manifest_path=manifest_path)
    assert paths["masterWav"].read_bytes() == b"failed master"
    assert json.loads(paths["masterReport"].read_text(encoding="utf-8"))["audioAcceptance"]["status"] == "failed"


def test_skip_flags_cannot_bypass_final_master_gate(monkeypatch, tmp_path):
    episode = "episode_001"
    (tmp_path / f"000_{episode}.episode_manifest.json").write_text("{}", encoding="utf-8")
    paths = artifact_paths(tmp_path, episode)
    paths["masterWav"].parent.mkdir()
    paths["masterWav"].write_bytes(b"unverified master")
    invoked = []
    monkeypatch.setattr(pack, "run_step", lambda *args, **kwargs: invoked.append(args[1]) or 0)
    assert pack.pack_episode(show="series_b", episode=episode, workspace=tmp_path,
                             skip_thumbnail=True, skip_qc=True, skip_master=True, skip_export=True) == 2
    assert invoked == []


def test_composition_retains_failed_encoded_evidence(monkeypatch, tmp_path):
    episode = "episode_001"
    paths = artifact_paths(tmp_path, episode)
    for key in ("masterWav", "videoBgJpg", "karaokeAss"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
        paths[key].write_bytes(key.encode())
    (tmp_path / f"000_{episode}.episode_manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(compose, "require_episode_audio_acceptance", lambda *args, **kwargs: {})
    def fake_compose(**kwargs):
        kwargs["output_mp4"].write_bytes(b"AAC output")
        return {"verification": {"durationSec": 4}}
    monkeypatch.setattr(compose, "compose_media_video", fake_compose)
    monkeypatch.setattr(gate, "measure_loudness", lambda _: {**MEASUREMENTS, "truePeakDb": -1.41})
    monkeypatch.setattr(gate, "ffmpeg_version", lambda: "ffmpeg fixture")
    monkeypatch.setattr(sys, "argv", ["compose", "--show", "series_b", "--episode", episode,
                                      "--workspace", str(tmp_path), "--no-branding"])
    with pytest.raises(ValueError, match="true peak"):
        compose.main()
    assert paths["mp4"].read_bytes() == b"AAC output"
    assert json.loads(paths["videoReport"].read_text(encoding="utf-8"))["audioAcceptance"]["status"] == "failed"


def test_export_rejects_changed_encoded_audio_before_probe(monkeypatch, tmp_path):
    stem = "episode01"
    for suffix in ("mp4", "wav", "srt", "youtube_description.txt", "youtube_title.txt", "youtube.json"):
        (tmp_path / f"{stem}.{suffix}").write_bytes(b"fixture")
    (tmp_path / f"{stem}-封面.jpg").write_bytes(b"fixture")
    master = record(monkeypatch, tmp_path / f"{stem}.wav")
    encoded = record(monkeypatch, tmp_path / f"{stem}.mp4", stage="encoded",
                     sources={"manifest": SOURCES["manifest"], "master": master["artifact"]["sha256"]})
    (tmp_path / f"{stem}.audio_acceptance.json").write_text(json.dumps({"master": master, "encoded": encoded}), encoding="utf-8")
    (tmp_path / f"{stem}.mp4").write_bytes(b"changed")
    with pytest.raises(ValueError, match="artifact changed"):
        verify_export_package(tmp_path, stem)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg required")
def test_real_final_wav_and_aac_are_measured_independently_and_silence_fails(tmp_path):
    episode = "episode_001"
    paths = artifact_paths(tmp_path, episode)
    for key in ("audioDir", "videoDir", "reportsDir", "turnsDir", "masterTurnsDir"):
        paths[key].mkdir(parents=True, exist_ok=True)
    audio, video, silence = paths["masterWav"], paths["mp4"], tmp_path / "silence.wav"
    manifest = {"episodeId": episode, "turns": [{"id": "t1", "filename": "turn.wav", "text": "Fixture tone"}]}
    paths["manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    common = [gate.resolve_ffmpeg(), "-y", "-hide_banner", "-loglevel", "error"]
    subprocess.run(common + ["-f", "lavfi", "-i", "sine=frequency=1000:duration=4:sample_rate=48000",
                             "-af", "loudnorm=I=-16:TP=-2:LRA=11", "-ar", "48000", str(audio)], check=True)
    subprocess.run(common + ["-f", "lavfi", "-i", "color=s=32x32:r=1:d=4", "-i", str(audio),
                             "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k", "-shortest", str(video)], check=True)
    raw_turn = turn_wav_path(tmp_path, "turn.wav")
    processed_turn = master_turn_wav_path(tmp_path, "t1", "turn.wav")
    shutil.copy2(audio, raw_turn)
    shutil.copy2(audio, processed_turn)
    master = gate.measure_audio_acceptance(audio, stage="master", sources=gate.master_sources(tmp_path, episode))
    encoded = gate.measure_audio_acceptance(video, stage="encoded",
                                             sources=gate.encoded_sources(tmp_path, episode))
    gate.validate_audio_acceptance(master, audio, stage="master")
    gate.validate_audio_acceptance(encoded, video, stage="encoded")
    assert master["artifact"]["sha256"] != encoded["artifact"]["sha256"]
    assert encoded["measurements"]["truePeakDb"] is not None
    paths["masterReport"].write_text(json.dumps({"episodeId": episode, "sourceTurns": 1, "durationSec": 4.0,
        "timeline": master_timeline_record(manifest, [processed_turn], audio), "audioAcceptance": master}), encoding="utf-8")
    paths["videoReport"].write_text(json.dumps({"audioAcceptance": encoded}), encoding="utf-8")
    assert gate.require_episode_audio_acceptance(tmp_path, episode)["encoded"]["status"] == "passed"
    raw_turn.write_bytes(raw_turn.read_bytes()[:-1] + b"x")
    with pytest.raises(ValueError, match="source changed"):
        gate.require_episode_audio_acceptance(tmp_path, episode)
    subprocess.run(common + ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", "4", str(silence)], check=True)
    silent = gate.measure_audio_acceptance(silence, stage="master", sources=SOURCES)
    assert silent["status"] == "failed"
    assert silent["measurements"]["integratedLufs"] is None
    json.dumps(silent, allow_nan=False)
