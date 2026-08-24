from __future__ import annotations

import json
from pathlib import Path

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
