from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "build_youtube_release.py"
SPEC = importlib.util.spec_from_file_location("build_youtube_release", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@pytest.mark.parametrize(
    ("content_id", "expected_video"),
    [
        (
            "content:classic_listening:persuasion_chapter_005",
            "workspace/classics/persuasion/chapter_005/video/000_chapter_005.mp4",
        ),
        (
            "content:series_b:episode_026",
            "workspace/shows/series_b/episode_026/video/000_episode_026.mp4",
        ),
        (
            "content:shorts_main:elr-s-068",
            "workspace/shorts/elr-s-068/video/elr-s-068.mp4",
        ),
    ],
)
def test_build_release_item_maps_canonical_artifact_paths(
    content_id: str, expected_video: str
) -> None:
    item = MODULE.build_release_item(
        {"contentId": content_id, "scheduledAt": "2026-09-14T08:00:00+08:00"}
    )
    assert item["video"] == expected_video
    assert item["qcStatus"] == "pass"


def test_build_release_item_rejects_unknown_content() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        MODULE.build_release_item(
            {"contentId": "content:unknown:x", "scheduledAt": "2026-09-14T08:00:00+08:00"}
        )
