from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from worker.channel.repo import RepositoryError, YouTubeReleaseJournal
from worker.channel.schema import SchemaError, load_youtube_release_manifest
from worker.channel.service import YouTubeReleaseService
from worker.channel.types import YouTubeRemoteVideo


CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"
NOW = "2026-08-28T12:00:00+00:00"


class FakeYouTubeProvider:
    def __init__(self, *, processing_status: str = "succeeded") -> None:
        self.processing_status = processing_status
        self.remote: dict[str, YouTubeRemoteVideo] = {}
        self.uploads = 0
        self.thumbnails = 0
        self.captions = 0
        self.playlists = 0
        self.schedules = 0

    def channel_id(self) -> str:
        return CHANNEL_ID

    def upload_private(self, spec) -> str:
        self.uploads += 1
        video_id = "video-1"
        self.remote[video_id] = YouTubeRemoteVideo(
            video_id=video_id,
            title=spec.title,
            privacy_status="private",
            publish_at=None,
            upload_status="processed" if self.processing_status == "succeeded" else "uploaded",
            processing_status=self.processing_status,
        )
        return video_id

    def set_thumbnail(self, video_id: str, path: Path) -> None:
        self.thumbnails += 1

    def upsert_captions(self, video_id: str, path: Path, *, language: str) -> str:
        self.captions += 1
        return "caption-1"

    def add_to_playlist(self, video_id: str, playlist_id: str) -> str:
        self.playlists += 1
        return "playlist-item-1"

    def fetch(self, video_id: str) -> YouTubeRemoteVideo:
        return self.remote[video_id]

    def schedule(self, video_id: str, scheduled_at_utc: str, spec) -> None:
        self.schedules += 1
        self.remote[video_id] = replace(
            self.remote[video_id], privacy_status="private", publish_at=scheduled_at_utc
        )


def release_manifest(tmp_path: Path) -> Path:
    video = tmp_path / "video.mp4"
    thumbnail = tmp_path / "thumbnail.png"
    captions = tmp_path / "captions.srt"
    video.write_bytes(b"video")
    thumbnail.write_bytes(b"png")
    captions.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    path = tmp_path / "release.json"
    path.write_text(
        json.dumps(
            {
                "schema": "youtube-release-manifest-v1",
                "youtubeChannelId": CHANNEL_ID,
                "items": [
                    {
                        "contentId": "content:series_a:episode_022",
                        "video": str(video),
                        "thumbnail": str(thumbnail),
                        "captions": str(captions),
                        "title": "A useful English lesson",
                        "description": "A complete lesson.",
                        "scheduledAt": "2026-09-04T20:00:00+08:00",
                        "playlistId": "playlist-1",
                        "categoryId": "27",
                        "language": "en",
                        "madeForKids": False,
                        "qcStatus": "pass",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_manifest_and_preflight_require_release_ready_artifacts(tmp_path: Path) -> None:
    spec = load_youtube_release_manifest(release_manifest(tmp_path), tmp_path)[0]
    service = YouTubeReleaseService(
        None,
        YouTubeReleaseJournal(tmp_path / "journal.json"),
        expected_channel_id=CHANNEL_ID,
        now=lambda: NOW,
    )

    fingerprint = service.preflight(spec)

    assert len(fingerprint) == 64
    with pytest.raises(ValueError, match="QC has not passed"):
        service.preflight(replace(spec, qc_status="pending"))


def test_manifest_can_reuse_pipeline_youtube_metadata(tmp_path: Path) -> None:
    path = release_manifest(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata_path = tmp_path / "youtube.json"
    metadata_path.write_text(
        json.dumps(
            {
                "title": "Title from the production package",
                "description": "Description from the production package.",
                "tags": ["English listening"],
                "language": "en-GB",
                "madeForKids": False,
            }
        ),
        encoding="utf-8",
    )
    item = payload["items"][0]
    item.pop("title")
    item.pop("description")
    item.pop("language")
    item["metadataFile"] = str(metadata_path)
    path.write_text(json.dumps(payload), encoding="utf-8")

    spec = load_youtube_release_manifest(path, tmp_path)[0]

    assert spec.title == "Title from the production package"
    assert spec.description == "Description from the production package."
    assert spec.tags == ("English listening",)
    assert spec.language == "en-GB"


def test_manifest_rejects_naive_schedule(tmp_path: Path) -> None:
    path = release_manifest(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["items"][0]["scheduledAt"] = "2026-09-04T20:00:00"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(SchemaError, match="timezone-aware"):
        load_youtube_release_manifest(path, tmp_path)


def test_sync_uploads_assets_schedules_and_retries_idempotently(tmp_path: Path) -> None:
    spec = load_youtube_release_manifest(release_manifest(tmp_path), tmp_path)[0]
    provider = FakeYouTubeProvider()
    service = YouTubeReleaseService(
        provider,
        YouTubeReleaseJournal(tmp_path / "journal.json"),
        expected_channel_id=CHANNEL_ID,
        now=lambda: NOW,
    )

    first = service.sync(spec, apply_upload=True, apply_schedule=True)
    second = service.sync(spec, apply_upload=True, apply_schedule=True)

    assert first.state == second.state == "scheduled"
    assert first.video_id == second.video_id == "video-1"
    assert (provider.uploads, provider.thumbnails, provider.captions) == (1, 1, 1)
    assert (provider.playlists, provider.schedules) == (1, 1)


def test_sync_adopts_manifest_video_without_duplicate_upload(tmp_path: Path) -> None:
    manifest_path = release_manifest(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["items"][0]["youtubeVideoId"] = "existing-1"
    payload["items"][0]["assetsAlreadySet"] = True
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    spec = load_youtube_release_manifest(manifest_path, tmp_path)[0]
    provider = FakeYouTubeProvider()
    provider.remote["existing-1"] = YouTubeRemoteVideo(
        video_id="existing-1",
        title=spec.title,
        privacy_status="private",
        publish_at=None,
        upload_status="processed",
        processing_status="succeeded",
    )
    service = YouTubeReleaseService(
        provider,
        YouTubeReleaseJournal(tmp_path / "journal.json"),
        expected_channel_id=CHANNEL_ID,
        now=lambda: NOW,
    )

    result = service.sync(spec, apply_upload=True, apply_schedule=True)

    assert result.video_id == "existing-1"
    assert result.state == "scheduled"
    assert provider.uploads == 0
    assert provider.thumbnails == 0
    assert provider.captions == 0


def test_sync_waits_for_processing_before_scheduling(tmp_path: Path) -> None:
    spec = load_youtube_release_manifest(release_manifest(tmp_path), tmp_path)[0]
    provider = FakeYouTubeProvider(processing_status="processing")
    service = YouTubeReleaseService(
        provider,
        YouTubeReleaseJournal(tmp_path / "journal.json"),
        expected_channel_id=CHANNEL_ID,
        now=lambda: NOW,
    )

    result = service.sync(spec, apply_upload=True, apply_schedule=True)

    assert result.state == "awaiting_processing"
    assert provider.schedules == 0


def test_journal_blocks_content_changes_and_remote_id_collisions(tmp_path: Path) -> None:
    journal = YouTubeReleaseJournal(tmp_path / "journal.json")
    journal.record("content:a", videoFingerprint="a" * 64, youtubeVideoId="video-1")

    with pytest.raises(RepositoryError, match="changed after upload began"):
        journal.record("content:a", videoFingerprint="b" * 64)
    with pytest.raises(RepositoryError, match="already assigned"):
        journal.record("content:b", videoFingerprint="c" * 64, youtubeVideoId="video-1")
