from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from worker.tts.dialogue import dialogue_turn_is_reusable, dialogue_turn_spec
from worker.tts.process import run_provider_batch
from worker.tts.schema import ProviderConfigError, resolve_provider_config
from worker.tts.trace import TRACE_SCHEMA, atomic_write_json, sha256_file, turn_trace_path


KOKORO_REVISION = "f3ff3571791e39611d31c381e3a41a3af07b4987"
CHATTERBOX_REVISION = "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18"


def _kokoro_settings(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "ttsProvider": "kokoro",
        "modelRevision": KOKORO_REVISION,
        "providerPython": "runtime/kokoro/python.exe",
        "localModelPath": "runtime/kokoro/model",
        "seedBase": 10,
        "providerSettings": {"languageCode": "a", "speed": 0.95},
    }
    value.update(changes)
    return value


def test_provider_config_uses_pinned_revision_and_h_drive_relative_paths(tmp_path: Path) -> None:
    config = resolve_provider_config(tmp_path, _kokoro_settings())

    assert config.provider_id == "kokoro"
    assert config.model_revision == KOKORO_REVISION
    assert config.interpreter == (tmp_path / "runtime/kokoro/python.exe").resolve()
    assert config.to_trace(tmp_path)["outputFormat"] == {
        "container": "wav",
        "sampleType": "float32",
    }
    with pytest.raises(ProviderConfigError, match="pinned revision"):
        resolve_provider_config(tmp_path, _kokoro_settings(modelRevision="latest"))
    with pytest.raises(ProviderConfigError, match="project-relative"):
        resolve_provider_config(tmp_path, _kokoro_settings(providerPython="../python.exe"))


def test_turbo_rejects_settings_it_does_not_implement(tmp_path: Path) -> None:
    with pytest.raises(ProviderConfigError, match="does not support"):
        resolve_provider_config(
            tmp_path,
            {
                "ttsProvider": "chatterbox_turbo",
                "providerPython": "runtime/turbo/python.exe",
                "localModelPath": "runtime/turbo/model",
                "providerSettings": {"temperature": 0.8, "exaggeration": 0.5},
            },
        )


def test_dialogue_host_mapping_and_trace_identity_control_reuse(tmp_path: Path) -> None:
    reference = tmp_path / "voices" / "ethan.wav"
    reference.parent.mkdir(parents=True)
    reference.write_bytes(b"reference-audio")
    digest = hashlib.sha256(reference.read_bytes()).hexdigest()
    manifest = {
        "episodeId": "episode_025",
        "renderSettings": {
            "ttsProvider": "chatterbox_500m",
            "modelRevision": CHATTERBOX_REVISION,
            "providerPython": "runtime/chatterbox/python.exe",
            "localModelPath": "runtime/chatterbox/model",
            "seedBase": 100,
        },
        "hosts": {
            "Ethan": {
                "referenceText": "Reference words.",
                "voice": {
                    "kind": "clone",
                    "referencePath": "voices/ethan.wav",
                    "referenceSha256": digest,
                },
            }
        },
    }
    turn = {"id": "p001", "order": 1, "speaker": "Ethan", "text": "  Hello   there. "}
    spec = dialogue_turn_spec(tmp_path, manifest, turn)

    assert spec["voice"]["referencePath"] == "voices/ethan.wav"
    assert spec["workerVoice"]["referencePath"] == str(reference.resolve())
    assert spec["normalizedText"] == "Hello there."
    assert spec["seed"] == 101

    retry_spec = dialogue_turn_spec(tmp_path, manifest, {**turn, "ttsSeedOffset": 1000})
    assert retry_spec["seed"] == 1101
    assert retry_spec["identity"]["sha256"] != spec["identity"]["sha256"]

    output = tmp_path / "audio" / "turn.wav"
    output.parent.mkdir()
    output.write_bytes(b"wav-a")
    atomic_write_json(
        turn_trace_path(output),
        {
            "schema": TRACE_SCHEMA,
            "identitySha256": spec["identity"]["sha256"],
            "outputSha256": sha256_file(output),
        },
    )
    assert dialogue_turn_is_reusable(tmp_path, manifest, turn, output)

    changed_turn = {**turn, "text": "Hello again."}
    assert not dialogue_turn_is_reusable(tmp_path, manifest, changed_turn, output)
    output.write_bytes(b"wav-b")
    assert not dialogue_turn_is_reusable(tmp_path, manifest, turn, output)


def test_provider_failure_cleans_transient_request(monkeypatch, tmp_path: Path) -> None:
    settings = _kokoro_settings()
    interpreter = tmp_path / "runtime" / "kokoro" / "python.exe"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_bytes(b"")
    (tmp_path / "runtime" / "kokoro" / "model").mkdir()
    provider = resolve_provider_config(tmp_path, settings)

    def fail(*_args, **_kwargs):
        raise OSError("launch failed")

    monkeypatch.setattr("worker.tts.process.subprocess.run", fail)
    with pytest.raises(OSError, match="launch failed"):
        run_provider_batch(
            tmp_path,
            provider,
            [{"id": "p001"}],
            label="test-provider-failure",
        )
    transient = tmp_path / "workspace" / "runtime" / "tmp" / "tts-provider"
    assert list(transient.glob("*.json")) == []
