from __future__ import annotations

import sys
from pathlib import Path

import pytest


TOOLS = Path(__file__).resolve().parents[3] / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from episode_workspace import (  # noqa: E402
    assert_canonical_workspace,
    canonical_episode_workspace,
    normalize_episode_id,
    resolve_series,
)
from prepare_episode_manifest import manifest_coverage, parse_turns  # noqa: E402


SHOW = {
    "showId": "series_a",
    "hostLinePattern": r"^(Ethan|Nora):",
    "hosts": ["Ethan", "Nora"],
}


def test_episode_ids_and_series_are_normalized() -> None:
    assert normalize_episode_id("16") == "episode_016"
    assert normalize_episode_id("episode_016") == "episode_016"
    assert resolve_series("all") == ("series_a", "series_b", "series_c")
    with pytest.raises(ValueError):
        normalize_episode_id("../../016")


def test_workspace_contract_rejects_free_form_path(tmp_path: Path) -> None:
    expected = canonical_episode_workspace(tmp_path, "series_b", 16)
    assert assert_canonical_workspace(tmp_path, "series_b", 16, expected) == expected
    with pytest.raises(ValueError, match="Non-canonical workspace"):
        assert_canonical_workspace(tmp_path, "series_b", 16, tmp_path / "somewhere-else")


def test_manifest_includes_host_lines_before_first_section() -> None:
    draft = """Ethan: This opening used to disappear.
Nora: It is part of the spoken episode.

[Teaching Plan]
Ethan: This planning note must not be rendered.

[Cold Open]
Ethan: This line belongs in the manifest too.
"""
    turns = parse_turns(draft, SHOW)
    assert [turn["text"] for turn in turns] == [
        "This opening used to disappear.",
        "It is part of the spoken episode.",
        "This line belongs in the manifest too.",
    ]
    coverage = manifest_coverage(draft, SHOW, turns)
    assert coverage["ratio"] == 1.0
