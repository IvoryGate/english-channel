from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.studio.upload import UploadSpec, StudioUploadError, extract_video_id, load_manifest_specs


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _short_fixture(tmp_path: Path, short_id: str) -> dict:
    video = _write(tmp_path / "workspace" / "shorts" / short_id / "video" / f"{short_id}.mp4", "v")
    _write(tmp_path / "workspace" / "shorts" / short_id / "package" / f"{short_id}.thumbnail.png", "t")
    _write(
        tmp_path / "workspace" / "shorts" / short_id / "package" / "title.txt",
        "Workplace Idiom: Get the Ball Rolling",
    )
    _write(tmp_path / "workspace" / "shorts" / short_id / "package" / "description.txt", "Practice B1 listening.")
    _write(
        tmp_path / "workspace" / "shorts" / short_id / "package" / "upload.json",
        json.dumps(
            {
                "schema": "elr-short-package-v1",
                "upload": {
                    "title": "Fallback Title",
                    "description": "Fallback description",
                    "madeForKids": False,
                    "categoryId": "27",
                },
            }
        ),
    )
    return {
        "contentId": f"content:shorts_main:{short_id}",
        "video": str(video),
        "thumbnail": str(tmp_path / "workspace" / "shorts" / short_id / "package" / f"{short_id}.thumbnail.png"),
        "metadataFile": str(tmp_path / "workspace" / "shorts" / short_id / "package" / "upload.json"),
        "titleFile": str(tmp_path / "workspace" / "shorts" / short_id / "package" / "title.txt"),
        "descriptionFile": str(tmp_path / "workspace" / "shorts" / short_id / "package" / "description.txt"),
    }


def _classic_fixture(tmp_path: Path) -> dict:
    video = _write(tmp_path / "workspace" / "classics" / "chapter_009" / "video" / "000_chapter_009.mp4", "v")
    _write(tmp_path / "workspace" / "classics" / "chapter_009" / "video" / "000_chapter_009.thumbnail.png", "t")
    _write(
        tmp_path / "workspace" / "classics" / "chapter_009" / "subtitles" / "000_chapter_009.youtube.srt",
        "1\n00:00:00,000 --> 00:00:02,000\nhello\n",
    )
    meta_path = _write(
        tmp_path / "workspace" / "classics" / "chapter_009" / "reports" / "000_chapter_009.youtube.json",
        json.dumps(
            {
                "title": "Persuasion Chapter 9: One Small Kindness",
                "description": "Settle in for Chapter 9.",
                "tags": ["Persuasion audiobook", "Jane Austen audiobook"],
            }
        ),
    )
    return {
        "contentId": "content:classic_listening:persuasion_chapter_009",
        "video": str(video),
        "thumbnail": str(tmp_path / "workspace" / "classics" / "chapter_009" / "video" / "000_chapter_009.thumbnail.png"),
        "captions": str(tmp_path / "workspace" / "classics" / "chapter_009" / "subtitles" / "000_chapter_009.youtube.srt"),
        "metadataFile": str(meta_path),
        "playlistId": "PLbM2xsP8plRg",
        "categoryId": "27",
    }


def _series_fixture(tmp_path: Path) -> dict:
    base = tmp_path / "workspace" / "shows" / "series_c" / "episode_029"
    video = _write(base / "video" / "000_episode_029.mp4", "v")
    _write(base / "video" / "000_episode_029.thumbnail.png", "t")
    _write(base / "subtitles" / "000_episode_029.srt", "1\n00:00:00,000 --> 00:00:02,000\nhi\n")
    _write(base / "reports" / "000_episode_029.youtube_title.txt", "10 Workplace Idioms | B2-C1")
    _write(base / "reports" / "000_episode_029.youtube_description.txt", "Infer ten idioms.")
    return {
        "contentId": "content:series_c:episode_029",
        "video": str(video),
        "thumbnail": str(base / "video" / "000_episode_029.thumbnail.png"),
        "captions": str(base / "subtitles" / "000_episode_029.srt"),
        "titleFile": str(base / "reports" / "000_episode_029.youtube_title.txt"),
        "descriptionFile": str(base / "reports" / "000_episode_029.youtube_description.txt"),
        "playlistId": "PLeDOm-qygJM4",
        "categoryId": "27",
    }


def _manifest(tmp_path: Path, items: list[dict]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"schema": "elr-youtube-release-v1", "items": items}), encoding="utf-8")
    return path


def test_load_manifest_specs_prefers_title_files_and_short_flags(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, [_short_fixture(tmp_path, "elr-s-161"), _series_fixture(tmp_path)])
    specs = load_manifest_specs(manifest)
    short, series = specs
    assert short.is_short is True
    assert short.title == "Workplace Idiom: Get the Ball Rolling"
    assert short.description == "Practice B1 listening."
    assert short.made_for_kids is False
    assert short.thumbnail_path is not None and short.thumbnail_path.is_file()
    assert series.is_short is False
    assert series.title == "10 Workplace Idioms | B2-C1"
    assert series.playlist_id == "PLeDOm-qygJM4"
    assert series.captions_path is not None and series.captions_path.is_file()


def test_load_manifest_specs_reads_classic_metadata_file(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, [_classic_fixture(tmp_path)])
    (spec,) = load_manifest_specs(manifest)
    assert spec.title == "Persuasion Chapter 9: One Small Kindness"
    assert spec.tags == ["Persuasion audiobook", "Jane Austen audiobook"]
    assert spec.playlist_id == "PLbM2xsP8plRg"
    assert spec.is_short is False


def test_load_manifest_specs_filters_and_reports_missing_ids(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, [_short_fixture(tmp_path, "elr-s-161")])
    specs = load_manifest_specs(manifest, only=["content:shorts_main:elr-s-161"])
    assert [spec.content_id for spec in specs] == ["content:shorts_main:elr-s-161"]
    with pytest.raises(StudioUploadError, match="not found"):
        load_manifest_specs(manifest, only=["content:shorts_main:elr-s-999"])


def test_validate_rejects_missing_artifacts(tmp_path: Path) -> None:
    spec = UploadSpec(
        content_id="content:shorts_main:elr-s-161",
        video_path=tmp_path / "missing.mp4",
        title="A title",
    )
    with pytest.raises(StudioUploadError, match="Missing video file"):
        spec.validate()
    video = _write(tmp_path / "video.mp4", "v")
    spec = UploadSpec(content_id="x", video_path=video, title="  ", description="d")
    with pytest.raises(StudioUploadError, match="empty title"):
        spec.validate()
    spec = UploadSpec(content_id="x", video_path=video, title="t", description="")
    with pytest.raises(StudioUploadError, match="empty description"):
        spec.validate()


def test_extract_video_id_matches_studio_and_watch_urls() -> None:
    assert extract_video_id("https://studio.youtube.com/video/sffU4D6r-xs/edit") == "sffU4D6r-xs"
    assert extract_video_id("https://studio.youtube.com/channel/UC123/videos") is None
    assert extract_video_id("https://www.youtube.com/watch?v=abcdefghijk") is None
