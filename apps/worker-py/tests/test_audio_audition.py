from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from worker.tts import audition, audition_audio
from worker.tts.dialogue import dialogue_turn_spec
from worker.tts.schema import ProviderConfigError, effective_turn_settings, resolve_provider_config
from worker.tts.trace import sha256_file


ROOT = Path(__file__).resolve().parents[3]


def plan() -> dict:
    return json.loads((ROOT / "configs/quality/audio-audition-v1.json").read_text(encoding="utf-8"))


def fixture(root: Path) -> tuple[dict, dict, Path]:
    config = plan()
    voice = root / "voices/reference.wav"
    voice.parent.mkdir()
    voice.write_bytes(b"reference")
    hosts = {key: {"voice": {"kind": "clone", "referencePath": "voices/reference.wav",
        "referenceSha256": sha256_file(voice)}} for key in ("host_a", "host_b")}
    output = root / "audition"
    output.mkdir()
    return config, {"status": "prepared", "frozen": {"voiceMapping": hosts},
        "elapsedSec": 0, "attemptedUtterances": 0, "completedUtterances": 0}, output


def test_round_one_has_equal_seeds_and_only_declared_acoustic_change(tmp_path: Path) -> None:
    config, state, output = fixture(tmp_path)
    rows = audition.tasks(tmp_path, config, state, output)
    assert len(rows) == 26
    for left, right in zip(rows[::2], rows[1::2]):
        assert left["request"]["text"] == right["request"]["text"]
        assert left["request"]["seed"] == right["request"]["seed"]
        assert "deliveryCue" not in left["request"]
        a, b = left["spec"]["effectiveSettings"], right["spec"]["effectiveSettings"]
        assert {key for key in a if a[key] != b[key]} == {"exaggeration"}
        assert left["spec"]["identity"]["sha256"] != right["spec"]["identity"]["sha256"]


def test_invalid_confound_and_generation_budget_fail_before_render() -> None:
    config = plan()
    config["candidates"][1]["providerSettings"]["cfgWeight"] = .3
    with pytest.raises(ValueError, match="exactly"):
        audition.round_one(config)
    config = plan()
    config["budget"]["maximumInitialUtteranceGenerations"] = 2
    with pytest.raises(ValueError, match="budget"):
        audition.round_one(config)


def test_turn_controls_change_identity_but_editorial_cues_do_not(tmp_path: Path) -> None:
    config, state, _ = fixture(tmp_path)
    manifest = {"hosts": state["frozen"]["voiceMapping"], "renderSettings": config["candidates"][0]}
    turn = {"id": "p001", "order": 1, "speaker": "host_a", "text": "Hello."}
    baseline = dialogue_turn_spec(tmp_path, manifest, turn)
    cue = dialogue_turn_spec(tmp_path, manifest, {**turn, "deliveryCue": "reassuring"})
    changed = dialogue_turn_spec(tmp_path, manifest, {**turn, "providerSettings": {"exaggeration": .7}})
    assert cue["identity"] == baseline["identity"]
    assert cue["deliveryCueStatus"] == "editorial_only"
    assert changed["effectiveSettings"]["exaggeration"] == .7
    assert changed["identity"] != baseline["identity"]


@pytest.mark.parametrize("overrides", [{"emotion": "happy"}, {"exaggeration": float("nan")},
    {"cfgWeight": 2}, {"temperature": 0}, {"topP": float("inf")}, []])
def test_unsupported_or_nonfinite_controls_fail(overrides) -> None:
    base = plan()["candidates"][0]["providerSettings"]
    with pytest.raises(ProviderConfigError):
        effective_turn_settings("chatterbox_500m", base, overrides)


def test_kokoro_allows_speed_not_a_new_loaded_language() -> None:
    base = {"languageCode": "a", "speed": .95}
    assert effective_turn_settings("kokoro", base, {"speed": 1.05})["speed"] == 1.05
    with pytest.raises(ProviderConfigError):
        effective_turn_settings("kokoro", base, {"languageCode": "b"})


def test_failed_batch_preserves_attempt_budget_and_never_claims_review(tmp_path: Path, monkeypatch) -> None:
    config, state, output = fixture(tmp_path)
    config["budget"]["minimumFreeDiskGiB"] = 0
    def fail(*args, **kwargs):
        assert kwargs["offline"] is True
        assert kwargs["timeout_sec"] <= 300
        raise RuntimeError("simulated model crash")
    monkeypatch.setattr(audition, "run_provider_batch", fail)
    with pytest.raises(RuntimeError, match="simulated"):
        audition.render(tmp_path, config, state, output)
    saved = audition.read_json(output / "run.json")
    assert saved["status"] == "incomplete"
    assert saved["attemptedUtterances"] == 2
    assert saved["completedUtterances"] == 0
    assert not (output / "review.json").exists()


def test_success_uses_existing_trace_identity_and_reuses_blind_assignment(tmp_path: Path, monkeypatch) -> None:
    config, state, output = fixture(tmp_path)
    config["budget"]["minimumFreeDiskGiB"] = 0
    calls = []
    def generate(root, provider, requests, **kwargs):
        calls.append(requests)
        result = []
        for request in requests:
            target = Path(request["outputPath"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"test wav")
            result.append({"id": request["id"], "effectiveSettings": request["providerSettings"],
                "outputSha256": sha256_file(target), "durationSec": 1, "packageVersion": "fixture"})
        return result
    monkeypatch.setattr(audition, "run_provider_batch", generate)
    assemblies = []
    monkeypatch.setattr(audition, "assemble", lambda *args, **kwargs: assemblies.append(True))
    verification = []
    monkeypatch.setattr(audition, "verify_review", lambda *args: verification.append(True))
    result = audition.render(tmp_path, config, state, output)
    assert result["completedUtterances"] == 26
    assert result["status"] == "awaiting_blind_review"
    assert len(calls) == 13 and all(len(batch) == 2 for batch in calls)
    audition.render(tmp_path, config, result, output)
    assert len(calls) == 13 and len(assemblies) == 1
    assert verification == [True]


def test_model_hash_mismatch_fails_without_loading_a_model(tmp_path: Path) -> None:
    source = {"sha": "revision", "siblings": [{"rfilename": "conds.pt", "lfs": {"sha256": "0" * 64}}]}
    (tmp_path / "source.json").write_text(json.dumps(source), encoding="utf-8")
    (tmp_path / "conds.pt").write_bytes(b"changed")
    with pytest.raises(ValueError, match="fingerprint"):
        audition.model_hashes(tmp_path, "revision")


def test_completed_resume_rejects_deleted_listening_output(tmp_path: Path) -> None:
    config = plan()
    pairs, mapping = [], {}
    for snippet in config["snippets"]:
        files = [f"listen/{snippet['id']}-{code}.wav" for code in ("A", "B")]
        for name in files:
            path = tmp_path / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"listening copy")
        pairs.append({"snippetId": snippet["id"], "files": files,
            "outputSha256": [sha256_file(tmp_path / name) for name in files]})
        mapping[snippet["id"]] = {"A": "cb-baseline", "B": "cb-expression"}
    (tmp_path / "review.json").write_text(json.dumps({"pairs": pairs}), encoding="utf-8")
    (tmp_path / "private-code-map.json").write_text(json.dumps(mapping), encoding="utf-8")
    audition.verify_review(config, tmp_path)
    (tmp_path / pairs[0]["files"][0]).unlink()
    with pytest.raises(ValueError, match="missing or invalid"):
        audition.verify_review(config, tmp_path)


def test_invalid_controls_do_not_start_provider(tmp_path: Path, monkeypatch) -> None:
    from worker.tts import process
    provider = resolve_provider_config(tmp_path, plan()["candidates"][0])
    monkeypatch.setattr(process.subprocess, "run", lambda *args, **kwargs: pytest.fail("must not launch"))
    with pytest.raises(ProviderConfigError, match="Unsupported"):
        process.run_provider_batch(tmp_path, provider, [{"providerSettings": {"emotion": "sad"}}], label="invalid")
    assert not (tmp_path / "workspace").exists()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg unavailable")
def test_review_audio_preserves_timing_and_matches_loudness_without_compression(tmp_path: Path) -> None:
    import numpy as np
    import soundfile as sf

    rate = 24000
    tone = np.sin(np.arange(rate * 2) * 2 * np.pi * 220 / rate).astype("float32")
    sources, copies = [], []
    for name, level in (("control", .1), ("candidate", .25)):
        turn = tmp_path / f"{name}.wav"
        sf.write(turn, tone * level, rate, subtype="FLOAT")
        source = tmp_path / f"{name}-joined.wav"
        audition_audio.concatenate([turn, turn], source, .28)
        assert sf.info(source).frames == rate * 4 + round(.28 * rate)
        sources.append(source)
        copies.append(tmp_path / f"{name}-listen.wav")
    result = audition_audio.match_pair(sources, copies, target=-16, peak=-1.5, maximum_difference=.5)
    assert abs(result[0]["after"]["integratedLufs"] - result[1]["after"]["integratedLufs"]) <= .5
    assert all(row["after"]["truePeakDbtp"] <= -1.5 for row in result)
    for source, copy in zip(sources, copies):
        assert sf.info(source).frames == sf.info(copy).frames


def test_provider_watchdog_terminates_timed_out_child_and_cleans_request(tmp_path: Path, monkeypatch) -> None:
    from worker.tts import process

    provider = resolve_provider_config(tmp_path, plan()["candidates"][0])
    provider.interpreter.parent.mkdir(parents=True)
    provider.interpreter.write_bytes(b"stub")
    provider.local_model_path.mkdir(parents=True)
    killed = []
    class Child:
        pid = 12345
        returncode = -1
        calls = 0
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def communicate(self, timeout=None):
            self.calls += 1
            if self.calls == 1:
                raise subprocess.TimeoutExpired("worker", timeout)
            return "", None
        def poll(self): return -1
        def kill(self): killed.append("kill")
    monkeypatch.setattr(process.subprocess, "Popen", lambda *a, **kw: Child())
    monkeypatch.setattr(process.subprocess, "run", lambda command, **kw: killed.append(command))
    monkeypatch.setattr(process.os, "killpg", lambda pid, sig: killed.append(pid), raising=False)
    with pytest.raises(process.ProviderProcessError, match="batch budget"):
        process.run_provider_batch(tmp_path, provider, [{"id": "test"}], label="watchdog-test", timeout_sec=.1, offline=True)
    assert killed
    assert list((tmp_path / "workspace/runtime/tmp/tts-provider").glob("*.json")) == []
