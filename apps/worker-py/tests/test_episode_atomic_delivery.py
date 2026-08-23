from __future__ import annotations

import sys
from pathlib import Path

import pytest


TOOLS = Path(__file__).resolve().parents[3] / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from export_episode_to_youtube_dir import promote_export, verify_export_package  # noqa: E402


def test_promotion_replaces_final_only_after_staging_is_ready(tmp_path: Path) -> None:
    final = tmp_path / "episode17"
    staging = tmp_path / "episode17.incomplete"
    final.mkdir()
    (final / "old.txt").write_text("old", encoding="utf-8")
    staging.mkdir()
    (staging / "new.txt").write_text("new", encoding="utf-8")

    promote_export(staging, final)

    assert (final / "new.txt").read_text(encoding="utf-8") == "new"
    assert not (final / "old.txt").exists()
    assert not staging.exists()
    assert not (tmp_path / "episode17.previous").exists()


def test_verification_rejects_incomplete_package_before_media_probe(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Incomplete export package"):
        verify_export_package(tmp_path, "episode17")
