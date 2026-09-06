from __future__ import annotations

import importlib.util
import json
import sys
from types import SimpleNamespace
from pathlib import Path

from worker.classics import audio_render
from worker.classics.audio_render import parse_segment_ids, tts_text


def test_parse_segment_ids_normalizes_numeric_ids() -> None:
    assert parse_segment_ids("8, 009,10") == {"008", "009", "010"}
    assert parse_segment_ids(None) == set()


def test_tts_input_contains_source_text_only() -> None:
    segment = {
        "spokenText": "Vanity was the beginning and the end.",
        "deliveryCue": "calm reflective literary narration",
    }

    assert tts_text(segment) == "Vanity was the beginning and the end."


def test_tts_input_converts_parentheses_to_pauses_without_dropping_words() -> None:
    segment = {"spokenText": "a father (having met disappointment), continued"}

    assert tts_text(segment) == "a father , having met disappointment, , continued"


def test_persuasion_manifest_routes_every_segment_to_one_voice() -> None:
    repo = Path(__file__).resolve().parents[3]
    manifest_path = (
        repo / "workspace" / "classics" / "persuasion" / "chapter_001" / "000_chapter_001.segments.json"
    )
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["voiceMode"] == "single"
    assert {segment["voiceProfile"] for segment in manifest["segments"]} == {
        "classic-listening-mia-narrator"
    }


def test_legacy_renderer_accepts_canonical_spoken_text() -> None:
    repo = Path(__file__).resolve().parents[3]
    module_path = (
        repo
        / ".cursor"
        / "skills"
        / "audiobook-chapter-tts"
        / "scripts"
        / "audiobook_workspace.py"
    )
    spec = importlib.util.spec_from_file_location("legacy_audiobook_workspace", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    manifest = {"segments": [{"id": "1", "spokenText": "A clean canonical line."}]}
    normalized = module.ensure_segment_defaults(manifest)

    assert normalized["segments"][0]["text"] == "A clean canonical line."
    assert normalized["segments"][0]["wordCount"] == 4


def test_default_model_factory_applies_low_memory_patch(monkeypatch) -> None:
    events: list[str] = []

    class FakeVoxCPM:
        @staticmethod
        def from_pretrained(*_args, **_kwargs):
            events.append("load")
            return "model"

    monkeypatch.setattr(
        audio_render, "patch_voxcpm_low_memory_load", lambda: events.append("patch")
    )
    monkeypatch.setitem(sys.modules, "voxcpm", SimpleNamespace(VoxCPM=FakeVoxCPM))
    monkeypatch.setenv("CLASSICS_VOXCPM_OPTIMIZE", "0")

    assert audio_render._default_model_factory("model", "cpu") == "model"
    assert events == ["patch", "load"]
