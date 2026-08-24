from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from worker.channel.repo import SqliteChannelRepository
from worker.channel.schema import parse_channel_policy, payload_sha256
from worker.channel.service import ChannelIdentityService
from worker.channel.transport import main


NOW = "2026-08-24T12:00:00+00:00"


def policy():
    return parse_channel_policy(
        {
            "schema": "youtube-channel-control-plane-v1",
            "channel": {"id": "test_channel", "publicName": "Test Channel"},
            "productLines": [
                {"id": "dialogue", "name": "Dialogue"},
                {"id": "shorts", "name": "Shorts"},
                {"id": "classic_listening", "name": "Classics"},
            ],
            "series": [
                {"id": "series_a", "productLineId": "dialogue", "name": "Series A"},
                {"id": "series_b", "productLineId": "dialogue", "name": "Series B"},
                {"id": "shorts_main", "productLineId": "shorts", "name": "Shorts"},
                {
                    "id": "classic_listening",
                    "productLineId": "classic_listening",
                    "name": "Classic Listening",
                },
            ],
        }
    )


def service(tmp_path: Path) -> ChannelIdentityService:
    return ChannelIdentityService(
        policy(), SqliteChannelRepository(tmp_path / "channel.sqlite"), now=lambda: NOW
    )


def write_json(path: Path, payload: dict) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return data


def dialogue_payload(
    *,
    show: str = "series_a",
    episode: int = 1,
    video_id: str = "dialogue-video-1",
    media_sha256: str = "a" * 64,
    title: str = "Dialogue episode",
) -> dict:
    return {
        "schema": "elr-publication-ledger-v1",
        "publications": [
            {
                "showId": show,
                "episodeId": episode,
                "title": title,
                "playlistId": "playlist-1",
                "mp4Sha256": media_sha256,
                "videoId": video_id,
                "status": "published",
            }
        ],
    }


def write_classics(root: Path, *, video_id: str = "classic-video-1") -> bytes:
    path = root / "persuasion" / "chapter_001" / "events.jsonl"
    path.parent.mkdir(parents=True)
    event = {
        "schema": "classic-listening-operation-event-v1",
        "eventId": "event-1",
        "sequence": 1,
        "bookSlug": "persuasion",
        "chapter": 1,
        "occurredAt": NOW,
        "actor": "test",
        "eventType": "STATE_TRANSITION",
        "fromState": None,
        "toState": "UPLOADED_PRIVATE",
        "reason": "fixture",
        "idempotencyKey": "fixture-1",
        "intentHash": "b" * 64,
        "previousEventHash": None,
        "eventHash": "c" * 64,
        "evidence": {"youtubeVideoId": video_id, "privacyStatus": "private"},
    }
    data = json.dumps(event, sort_keys=True).encode("utf-8") + b"\n"
    path.write_bytes(data)
    return data


def test_initializes_versioned_policy_identity_store(tmp_path: Path) -> None:
    identity = service(tmp_path)

    inventory = identity.initialize()
    repeated = identity.initialize()

    assert inventory.schema_version == 4
    assert inventory.channel_count == 1
    assert inventory.product_line_count == 3
    assert inventory.series_count == 4
    assert repeated.schema_version == 4
    assert repeated.import_run_count == 0


def test_failed_migration_rolls_back_the_whole_file(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0001_stable.sql").write_text(
        "CREATE TABLE stable(value TEXT);\n", encoding="utf-8", newline="\n"
    )
    (migrations / "0002_broken.sql").write_text(
        "CREATE TABLE should_rollback(value TEXT);\nCREATE TABL invalid(value TEXT);\n",
        encoding="utf-8",
        newline="\n",
    )
    database = tmp_path / "migration.sqlite"
    repository = SqliteChannelRepository(database, migrations)

    with pytest.raises(RuntimeError, match="0002_broken.sql"):
        repository.migrate(NOW)

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations")]
    assert "stable" in tables
    assert "should_rollback" not in tables
    assert versions == [1]


def test_imports_all_legacy_shapes_and_retains_exact_payloads(tmp_path: Path) -> None:
    identity = service(tmp_path)
    dialogue = tmp_path / "dialogue.json"
    shorts = tmp_path / "shorts.json"
    classics = tmp_path / "classics"
    dialogue_bytes = write_json(dialogue, dialogue_payload())
    shorts_bytes = write_json(
        shorts,
        {
            "schema": "elr-shorts-publication-ledger-v1",
            "entries": [
                {
                    "shortId": "short_001",
                    "contentKey": "fixture-content-key",
                    "status": "uploaded_private",
                    "youtubeId": "short-video-1",
                }
            ],
        },
    )
    classics_bytes = write_classics(classics)

    dialogue_result = identity.import_dialogue(dialogue)
    shorts_result = identity.import_shorts(shorts)
    classics_result = identity.import_classics(classics)

    inventory = identity.inventory()
    assert inventory.content_item_count == 3
    assert inventory.source_alias_count == 3
    assert inventory.artifact_count == 1
    assert inventory.publication_count == 3
    assert inventory.content_by_product_line == {
        "classic_listening": 1,
        "dialogue": 1,
        "shorts": 1,
    }
    assert dialogue_result.source_sha256 == hashlib.sha256(dialogue_bytes).hexdigest()
    assert shorts_result.source_sha256 == hashlib.sha256(shorts_bytes).hexdigest()
    assert classics_bytes == next(classics.glob("*/chapter_*/events.jsonl")).read_bytes()
    stored = identity.repository.import_record_payloads(dialogue_result.import_run_id)
    assert stored[0]["rawPayload"] == dialogue_payload()["publications"][0]
    assert stored[0]["rawPayloadSha256"] == payload_sha256(
        dialogue_payload()["publications"][0]
    )
    assert dialogue.read_bytes() == dialogue_bytes
    assert shorts.read_bytes() == shorts_bytes


def test_identical_reimport_is_auditable_and_idempotent(tmp_path: Path) -> None:
    identity = service(tmp_path)
    source = tmp_path / "dialogue.json"
    write_json(source, dialogue_payload())

    first = identity.import_dialogue(source)
    second = identity.import_dialogue(source)

    assert first.inserted == 1
    assert second.unchanged == 1
    assert second.inserted == 0
    inventory = identity.inventory()
    assert inventory.content_item_count == 1
    assert inventory.publication_count == 1
    assert inventory.import_run_count == 2


def test_conflicting_media_and_remote_identity_are_isolated(tmp_path: Path) -> None:
    identity = service(tmp_path)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    write_json(first, dialogue_payload())
    write_json(
        second,
        dialogue_payload(show="series_b", episode=2, title="Different episode"),
    )
    identity.import_dialogue(first)

    result = identity.import_dialogue(second)
    collisions = identity.repository.collisions()

    assert result.collided == 1
    assert result.collision_count == 2
    assert {item.kind for item in collisions} == {"artifact_fingerprint", "remote_video_id"}
    assert identity.inventory().content_item_count == 1
    stored = identity.repository.import_record_payloads(result.import_run_id)
    assert stored[0]["outcome"] == "collision"
    assert stored[0]["rawPayload"]["showId"] == "series_b"


def test_mutable_title_updates_without_changing_canonical_identity(tmp_path: Path) -> None:
    identity = service(tmp_path)
    source = tmp_path / "dialogue.json"
    write_json(source, dialogue_payload(title="First title"))
    identity.import_dialogue(source)
    write_json(source, dialogue_payload(title="Improved title"))

    result = identity.import_dialogue(source)

    assert result.updated == 1
    assert result.collided == 0
    assert identity.inventory().content_item_count == 1


def test_import_rejects_series_outside_tracked_policy(tmp_path: Path) -> None:
    identity = service(tmp_path)
    source = tmp_path / "dialogue.json"
    write_json(source, dialogue_payload(show="unknown_series"))

    with pytest.raises(ValueError, match="unknown series"):
        identity.import_dialogue(source)

    assert identity.inventory().import_run_count == 0


def test_transport_init_and_status_never_claim_remote_authority(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo_root = tmp_path / "repo"
    policy_path = repo_root / "configs" / "channel" / "control-plane.json"
    write_json(
        policy_path,
        {
            "schema": "youtube-channel-control-plane-v1",
            "channel": {"id": "test_channel", "publicName": "Test Channel"},
            "productLines": [{"id": "dialogue", "name": "Dialogue"}],
            "series": [
                {"id": "series_a", "productLineId": "dialogue", "name": "Series A"}
            ],
        },
    )
    database = tmp_path / "state" / "channel.sqlite"

    assert main(
        [
            "--repo-root",
            str(repo_root),
            "--policy",
            str(policy_path),
            "--database",
            str(database),
            "init",
        ]
    ) == 0
    capsys.readouterr()
    assert main(
        [
            "--repo-root",
            str(repo_root),
            "--policy",
            str(policy_path),
            "--database",
            str(database),
            "status",
        ]
    ) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["initialized"] is True
    assert output["remoteMutationAuthority"] is False
