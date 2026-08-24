from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.channel.repo import SqliteChannelRepository
from worker.channel.schema import SchemaError, parse_channel_policy
from worker.channel.service import ChannelIdentityService


NOW = "2026-08-24T03:09:11+00:00"


def service(tmp_path: Path) -> ChannelIdentityService:
    policy = parse_channel_policy(
        {
            "schema": "youtube-channel-control-plane-v1",
            "channel": {"id": "test_channel", "publicName": "Test"},
            "productLines": [
                {"id": "dialogue", "name": "Dialogue"},
                {"id": "shorts", "name": "Shorts"},
            ],
            "series": [
                {"id": "series_a", "productLineId": "dialogue", "name": "A"},
                {"id": "shorts_main", "productLineId": "shorts", "name": "Shorts"},
            ],
        }
    )
    return ChannelIdentityService(
        policy, SqliteChannelRepository(tmp_path / "channel.sqlite"), now=lambda: NOW
    )


def write_dialogue(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "elr-publication-ledger-v1",
                "publications": [
                    {
                        "showId": "series_a",
                        "episodeId": 1,
                        "title": "Matched title",
                        "playlistId": "playlist",
                        "mp4Sha256": "a" * 64,
                        "videoId": "video-local",
                        "status": "published",
                    }
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )


def write_rss(path: Path, *, matched_title: str = "Matched title") -> bytes:
    value = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <yt:channelId>UCchannel-fixture</yt:channelId>
  <entry>
    <yt:videoId>video-local</yt:videoId>
    <yt:channelId>UCchannel-fixture</yt:channelId>
    <title>{matched_title}</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=video-local"/>
    <published>2026-08-16T00:00:00+00:00</published>
    <updated>2026-08-17T00:00:00+00:00</updated>
  </entry>
  <entry>
    <yt:videoId>remote-short</yt:videoId>
    <yt:channelId>UCchannel-fixture</yt:channelId>
    <title>Remote short</title>
    <link rel="alternate" href="https://www.youtube.com/shorts/remote-short"/>
    <published>2026-08-19T00:00:00+00:00</published>
    <updated>2026-08-19T00:00:00+00:00</updated>
  </entry>
</feed>
""".encode("utf-8")
    path.write_bytes(value)
    return value


def write_shorts(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "elr-shorts-publication-ledger-v1",
                "entries": [
                    {
                        "shortId": "short_001",
                        "title": "Remote short",
                        "status": "published",
                        "youtubeId": "remote-short",
                    }
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )


def test_remote_capture_is_idempotent_and_preserves_scope(tmp_path: Path) -> None:
    identity = service(tmp_path)
    dialogue = tmp_path / "dialogue.json"
    rss = tmp_path / "rss.xml"
    write_dialogue(dialogue)
    original = write_rss(rss)
    identity.import_dialogue(dialogue)

    capture_id, inserted, count = identity.import_youtube_rss(
        rss, scope="public_rss_recent_max_15_no_private_unlisted"
    )
    repeated_id, repeated_inserted, repeated_count = identity.import_youtube_rss(
        rss, scope="public_rss_recent_max_15_no_private_unlisted"
    )

    assert inserted is True
    assert count == 2
    assert repeated_id == capture_id
    assert repeated_inserted is False
    assert repeated_count == 2
    assert rss.read_bytes() == original


def test_reconciliation_keeps_remote_only_identity_explicit(tmp_path: Path) -> None:
    identity = service(tmp_path)
    dialogue = tmp_path / "dialogue.json"
    rss = tmp_path / "rss.xml"
    write_dialogue(dialogue)
    write_rss(rss)
    identity.import_dialogue(dialogue)
    capture_id, _, _ = identity.import_youtube_rss(
        rss, scope="public_rss_recent_max_15_no_private_unlisted"
    )

    report = identity.reconcile(capture_id)

    assert report.matched_remote_ids == ("video-local",)
    assert report.remote_only_ids == ("remote-short",)
    assert report.local_outside_capture_ids == ()
    assert report.title_disagreements == ()
    assert report.scope == "public_rss_recent_max_15_no_private_unlisted"


def test_reconciliation_reports_title_disagreement_without_remapping(tmp_path: Path) -> None:
    identity = service(tmp_path)
    dialogue = tmp_path / "dialogue.json"
    rss = tmp_path / "rss.xml"
    write_dialogue(dialogue)
    write_rss(rss, matched_title="Changed remote title")
    identity.import_dialogue(dialogue)
    capture_id, _, _ = identity.import_youtube_rss(rss, scope="public_rss_recent")

    report = identity.reconcile(capture_id)

    assert report.matched_remote_ids == ("video-local",)
    assert report.title_disagreements == (
        {
            "remoteId": "video-local",
            "localTitle": "Matched title",
            "remoteTitle": "Changed remote title",
        },
    )


def test_shorts_recovery_uses_stable_id_and_retains_title(tmp_path: Path) -> None:
    identity = service(tmp_path)
    dialogue = tmp_path / "dialogue.json"
    shorts = tmp_path / "shorts.json"
    rss = tmp_path / "rss.xml"
    write_dialogue(dialogue)
    write_shorts(shorts)
    write_rss(rss)
    identity.import_dialogue(dialogue)
    identity.import_shorts(shorts)
    capture_id, _, _ = identity.import_youtube_rss(rss, scope="public_rss_recent")

    report = identity.reconcile(capture_id)

    assert report.matched_remote_ids == ("remote-short", "video-local")
    assert report.remote_only_ids == ()
    assert report.title_disagreements == ()


def test_remote_capture_requires_scope_and_one_channel(tmp_path: Path) -> None:
    identity = service(tmp_path)
    rss = tmp_path / "rss.xml"
    original = write_rss(rss)
    rss.write_bytes(
        original.replace(
            b"<yt:channelId>UCchannel-fixture</yt:channelId>",
            b"<yt:channelId>UCdifferent-channel</yt:channelId>",
            1,
        )
    )

    with pytest.raises(SchemaError, match="more than one channel ID"):
        identity.import_youtube_rss(rss, scope="public_rss_recent")

    rss.write_bytes(original)
    with pytest.raises(ValueError, match="scope must not be empty"):
        identity.import_youtube_rss(rss, scope="   ")
