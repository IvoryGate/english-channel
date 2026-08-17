from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.channel_ops.repo import JsonPublicationRepository, LocalEpisodeRepository
from worker.channel_ops.service import PublicationPreflightService, validate_release_plan
from worker.channel_ops.types import PublicationRecord, ReleaseSlot, ShowPolicy


POLICY = ShowPolicy("series_b", "First Steps", "A2-B1", "playlist-b")


def write_candidate(repo: Path, *, title: str = "Fast English | A2-B1") -> None:
    workspace = repo / "workspace" / "shows" / "series_b" / "episode_020"
    (workspace / "reports").mkdir(parents=True)
    (workspace / "video").mkdir()
    (workspace / "subtitles").mkdir()
    (workspace / "000_episode_020.youtube.json").write_text(
        json.dumps({"showId": "series_b", "title": title, "description": "Description"}),
        encoding="utf-8",
    )
    (workspace / "reports" / "000_episode_020.youtube_title.txt").write_text(
        title, encoding="utf-8"
    )
    (workspace / "reports" / "000_episode_020.youtube_description.txt").write_text(
        "Description", encoding="utf-8"
    )
    (workspace / "reports" / "000_episode_020.video_report.json").write_text(
        json.dumps({"verification": {"durationSec": 600, "width": 2560, "height": 1440}}),
        encoding="utf-8",
    )
    (workspace / "video" / "000_episode_020.mp4").write_bytes(b"video")
    (workspace / "video" / "000_episode_020.thumbnail.png").write_bytes(b"png")
    (workspace / "subtitles" / "000_episode_020.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8"
    )


def service(repo: Path, ledger: Path) -> PublicationPreflightService:
    return PublicationPreflightService(
        LocalEpisodeRepository(repo),
        JsonPublicationRepository(ledger),
        {"series_b": POLICY},
    )


def test_preflight_builds_fingerprinted_candidate(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    result = service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)
    assert result.ok
    assert result.candidate.episode_id == "episode_020"
    assert len(result.candidate.fingerprint("mp4").sha256) == 64
    assert len(result.candidate.fingerprint("description").sha256) == 64


def test_preflight_blocks_cjk_in_public_metadata(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    description = (
        tmp_path
        / "workspace"
        / "shows"
        / "series_b"
        / "episode_020"
        / "reports"
        / "000_episode_020.youtube_description.txt"
    )
    description.write_text("9:09 Mixed Role-Play - 转", encoding="utf-8")
    with pytest.raises(ValueError, match="Description contains CJK"):
        service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)


def test_preflight_blocks_metadata_description_mismatch(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    metadata = (
        tmp_path
        / "workspace"
        / "shows"
        / "series_b"
        / "episode_020"
        / "000_episode_020.youtube.json"
    )
    metadata.write_text(
        json.dumps(
            {
                "showId": "series_b",
                "title": "Fast English | A2-B1",
                "description": "Different description",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="description does not match"):
        service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)


def test_preflight_blocks_video_below_2k(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    report = (
        tmp_path
        / "workspace"
        / "shows"
        / "series_b"
        / "episode_020"
        / "reports"
        / "000_episode_020.video_report.json"
    )
    report.write_text(
        json.dumps({"verification": {"durationSec": 600, "width": 1920, "height": 1080}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="minimum 2560x1440"):
        service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)


def test_preflight_blocks_duplicate_title_and_media(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    initial = service(tmp_path, tmp_path / "ledger.json").build_candidate("series_b", 20)
    JsonPublicationRepository(tmp_path / "ledger.json").save(
        (
            PublicationRecord(
                "series_a",
                "episode_019",
                initial.title,
                "playlist-a",
                initial.fingerprint("mp4").sha256,
                "video-1",
                "published",
            ),
        )
    )
    result = service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)
    assert not result.ok
    assert any("Title is already mapped" in error for error in result.errors)
    assert any("MP4 fingerprint is already mapped" in error for error in result.errors)


def test_preflight_returns_existing_video_for_idempotent_resume(tmp_path: Path) -> None:
    write_candidate(tmp_path)
    initial = service(tmp_path, tmp_path / "ledger.json").build_candidate("series_b", 20)
    JsonPublicationRepository(tmp_path / "ledger.json").save(
        (
            PublicationRecord(
                "series_b",
                "episode_020",
                initial.title,
                initial.playlist_id,
                initial.fingerprint("mp4").sha256,
                "video-20",
                "private",
            ),
        )
    )
    result = service(tmp_path, tmp_path / "ledger.json").preflight("series_b", 20)
    assert result.ok
    assert result.existing_video_id == "video-20"
    assert "do not upload again" in result.warnings[0]


def test_release_plan_enforces_channel_and_series_spacing() -> None:
    slots = (
        ReleaseSlot("series_b", "episode_020", "2026-08-18T20:00:00+08:00"),
        ReleaseSlot("series_a", "episode_020", "2026-08-20T20:00:00+08:00"),
        ReleaseSlot("series_b", "episode_021", "2026-08-25T20:00:00+08:00"),
    )
    assert not validate_release_plan(
        slots, min_channel_spacing_hours=48, min_same_series_spacing_hours=168
    )
    invalid = slots[:2] + (
        ReleaseSlot("series_b", "episode_021", "2026-08-20T21:00:00+08:00"),
    )
    errors = validate_release_plan(
        invalid, min_channel_spacing_hours=48, min_same_series_spacing_hours=168
    )
    assert errors
