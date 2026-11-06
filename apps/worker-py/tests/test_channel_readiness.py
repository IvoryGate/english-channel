from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

from worker.channel.readiness_repo import ReadinessRepository
from worker.channel.readiness_schema import aware_timestamp
from worker.channel.readiness_service import ReadinessService
from worker.channel.transport import main


AS_OF = "2026-11-06T10:00:00+08:00"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) + "\n", encoding="utf-8", newline="\n")


def report(root: Path, as_of: str = AS_OF) -> dict:
    repo = ReadinessRepository(root, root / "workspace/channel/channel.sqlite",
                               root / "configs/channel/release-policy.json")
    return ReadinessService(repo, aware_timestamp(as_of)).report()


def codes(result: dict) -> set[str]:
    return {item["code"] for item in result["findings"]}


def policy(root: Path, *, ends_on: str = "2026-11-05") -> None:
    write_json(root / "configs/channel/release-policy.json", {
        "schema": "youtube-channel-release-policy-v1", "timezone": "Asia/Shanghai",
        "authority": {"defaultPrivacy": "private", "publicSchedulingEnabled": True,
                      "explicitApprovalRequired": True},
        "capacity": {"maxChannelUploadsPerRolling7Days": 42, "reservationRequired": True},
        "programs": {"dialogue": {"productLine": "dialogue", "status": "active",
                                  "startsOn": "2026-08-01", "endsOn": ends_on}},
    })


def database(root: Path) -> Path:
    path = root / "workspace/channel/channel.sqlite"
    path.parent.mkdir(parents=True)
    with sqlite3.connect(path) as db:
        db.executescript("""
            CREATE TABLE schema_migrations(version INTEGER, name TEXT);
            INSERT INTO schema_migrations VALUES(1, '0001_identity.sql');
            INSERT INTO schema_migrations VALUES(5, '0005_unknown.sql');
            CREATE TABLE publications(id TEXT);
            INSERT INTO publications VALUES('local-record');
            CREATE TABLE analytics_observations(id TEXT);
            CREATE TABLE remote_captures(capture_id TEXT, provider TEXT, scope TEXT,
                collected_at TEXT, item_count INTEGER);
            INSERT INTO remote_captures VALUES('old', 'youtube', 'public_recent_15_no_private',
                '2026-08-24T03:13:00+00:00', 15);
        """)
    return path


def test_missing_database_is_reported_without_creating_any_files(tmp_path: Path) -> None:
    before = list(tmp_path.rglob("*"))
    result = report(tmp_path)
    assert result["database"]["status"] == "missing"
    assert result["database"]["counts"] == {}
    assert result["releasePolicy"]["status"] == "missing"
    assert result["activePlans"]["count"] is None
    assert result["community"]["recordedCommentIds"] is None
    assert result["community"]["explicitlyVerifiedCommentIds"] is None
    assert result["community"]["futureScheduledRecords"] is None
    assert result["community"]["evidenceCoverage"] == {
        "comments": "unavailable", "postSchedules": "unavailable", "documents": "unavailable",
    }
    assert result["releaseApproval"] is False
    assert result["remoteMutationAuthority"] is False
    assert list(tmp_path.rglob("*")) == before


def test_unknown_schema_and_historical_scope_do_not_mutate_database(tmp_path: Path) -> None:
    path = database(tmp_path)
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    result = report(tmp_path)
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
    assert path.is_file()
    assert "unknown_migrations" in codes(result)
    assert "analytics_empty" in codes(result)
    assert result["database"]["counts"]["publications"] == 1
    assert result["database"]["counts"]["analytics_observations"] == 0
    assert result["database"]["counts"]["analytics_captures"] is None
    capture = result["database"]["captures"][0]
    assert capture["scope"] == "public_recent_15_no_private"
    assert capture["observation"]["freshness"] == "stale"
    assert result["database"]["completeRemoteInventory"] is False


def test_expiry_uses_policy_local_calendar_day_inclusively(tmp_path: Path) -> None:
    policy(tmp_path)
    same_day = report(tmp_path, "2026-11-05T15:59:59Z")
    following_day = report(tmp_path, "2026-11-05T16:00:00Z")
    assert same_day["releasePolicy"]["programs"][0]["windowState"] == "in_window"
    assert following_day["releasePolicy"]["programs"][0]["windowState"] == "expired"
    assert "active_program_outside_window" in codes(following_day)


def test_community_old_observation_stays_stale_after_touch_and_schedule(tmp_path: Path) -> None:
    community = tmp_path / "workspace/community"
    write_json(community / "operations.json", {
        "schema": "community-operations-v1", "automation": {"status": "ACTIVE"},
        "videoComments": [{"commentId": "same-comment", "status": "published",
                           "date": "2026-10-18"}],
    })
    write_json(community / "backfill.json", {
        "schema": "video-comment-backfill-v1", "date": "2026-10-18",
        "comments": [{"commentId": "same-comment", "status": "published_verified"}],
    })
    write_json(community / "posts.json", {"schema": "community-post-buffer-v1", "posts": [
        {"status": "scheduled", "scheduledAt": "2026-11-07T12:00:00+08:00"}
    ]})
    write_json(community / "inventory.json", {
        "schema": "video-comment-backfill-queue-v1", "captureComplete": False,
    })
    os.utime(community / "operations.json", None)
    result = report(tmp_path)
    observed = result["community"]["latestRecordedPublication"]
    assert observed["recordedAt"] == "2026-10-18"
    assert observed["precision"] == "date"
    assert observed["freshness"] == "stale"
    assert result["community"]["futureScheduledRecords"] == 1
    assert result["community"]["recordedCommentIds"] == 1
    assert result["community"]["explicitlyVerifiedCommentIds"] == 1
    assert result["community"]["automationCurrentState"] == "unknown"
    assert "community_inventory_partial" in codes(result)


def test_invalid_and_future_evidence_never_become_current(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "videoComments": [
            {"status": "published_verified", "commentId": "future", "verifiedAt": "2026-11-07T01:00:00Z"},
            {"status": "published", "commentId": "invalid-date", "date": "not a date"},
        ], "posts": [{"status": "scheduled", "scheduledAt": "2026-11-07T12:00:00"}],
    })
    result = report(tmp_path)
    assert result["community"]["latestRecordedPublication"] is None
    assert {"evidence_future", "invalid_observation_date", "community_schedule_invalid"} <= codes(result)


def test_corrupt_inputs_are_findings_and_other_sections_survive(tmp_path: Path) -> None:
    path = database(tmp_path)
    path.write_bytes(b"not sqlite")
    policy(tmp_path)
    (tmp_path / "configs/channel/release-policy.json").write_text("{broken", encoding="utf-8")
    write_json(tmp_path / "workspace/community/operations.json", {"schema": "unknown"})
    result = report(tmp_path)
    assert result["database"]["status"] == "unreadable_or_invalid"
    assert result["releasePolicy"]["status"] == "invalid_json"
    assert "community_schema_unknown" in codes(result)


def test_invalid_shapes_and_expired_buffer_are_reported(tmp_path: Path) -> None:
    write_json(tmp_path / "configs/channel/release-policy.json", {"schema": "bad"})
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "videoComments": "bad",
        "posts": [{"status": "scheduled", "scheduledAt": "2026-10-25T12:00:00+08:00"}],
    })
    result = report(tmp_path)
    assert {"release_policy_invalid", "community_rows_invalid", "community_buffer_unverified"} <= codes(result)


def test_malformed_community_fields_are_not_an_unhandled_exception(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {"schema": []})
    write_json(tmp_path / "workspace/community/posts.json", {
        "schema": "community-post-buffer-v1", "posts": [{"status": {}}],
    })
    result = report(tmp_path)
    assert {"community_schema_unknown", "community_rows_invalid"} <= codes(result)
    assert result["community"]["recordedCommentIds"] is None
    assert result["community"]["explicitlyVerifiedCommentIds"] is None
    assert result["community"]["futureScheduledRecords"] is None


def test_explicit_supported_empty_arrays_are_measured_zero(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "videoComments": [], "posts": [],
    })
    community = report(tmp_path)["community"]
    assert community["recordedCommentIds"] == 0
    assert community["explicitlyVerifiedCommentIds"] == 0
    assert community["futureScheduledRecords"] == 0
    assert community["evidenceCoverage"] == {
        "comments": "available", "postSchedules": "available", "documents": "available",
    }


def test_unrelated_supported_inventory_does_not_imply_zero_actions(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "video-comment-backfill-queue-v1", "captureComplete": False,
    })
    community = report(tmp_path)["community"]
    assert community["recordedCommentIds"] is None
    assert community["futureScheduledRecords"] is None


def test_partial_community_coverage_exposes_known_local_count(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "videoComments": [
            {"status": "published", "commentId": "known", "date": "2026-11-05"},
            {"status": "published"},
        ], "posts": [{"status": "scheduled", "scheduledAt": "bad"}],
    })
    community = report(tmp_path)["community"]
    assert community["recordedCommentIds"] == 1
    assert community["evidenceCoverage"]["comments"] == "partial"
    assert community["futureScheduledRecords"] is None
    assert community["evidenceCoverage"]["postSchedules"] == "unavailable"


def test_invalid_release_timezone_is_a_finding(tmp_path: Path) -> None:
    policy(tmp_path)
    path = tmp_path / "configs/channel/release-policy.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["timezone"] = "Invalid/Not_A_Zone"
    write_json(path, data)
    result = report(tmp_path)
    assert result["releasePolicy"]["status"] == "invalid_schema"
    assert "release_policy_invalid" in codes(result)


def test_read_only_snapshot_includes_committed_live_wal(tmp_path: Path) -> None:
    path = database(tmp_path)
    with sqlite3.connect(path) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO publications VALUES('committed-wal-record')")
        writer.commit()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        result = report(tmp_path)
        assert result["database"]["counts"]["publications"] == 2
        assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_idle_wal_database_does_not_create_sidecars(tmp_path: Path) -> None:
    path = database(tmp_path)
    writer = sqlite3.connect(path)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("INSERT INTO publications VALUES('idle-wal-record')")
    writer.commit()
    writer.close()
    assert not Path(str(path) + "-wal").exists()
    assert not Path(str(path) + "-shm").exists()
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    result = report(tmp_path)
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.rglob("*") if p.is_file()}
    assert result["database"]["status"] == "wal_snapshot_unavailable"
    assert before == after


def test_unidentifiable_publications_cannot_refresh_observation(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "videoComments": [
            {"status": "published", "commentId": "real", "date": "2026-10-18"},
            {"status": "published", "date": "2026-11-06"},
        ], "communityPosts": [{"status": "published", "date": "2026-11-06"}],
    })
    community = report(tmp_path)["community"]
    assert community["latestRecordedPublication"]["recordedAt"] == "2026-10-18"
    assert community["latestRecordedPublication"]["freshness"] == "stale"


def test_latest_observation_uses_exact_time_before_display(tmp_path: Path) -> None:
    write_json(tmp_path / "workspace/community/operations.json", {
        "schema": "community-operations-v1", "communityPosts": [
            {"status": "published", "id": "older", "publishedAt": "2026-11-06T01:59:00Z"},
            {"status": "published", "postId": "newer", "publishedAt": "2026-11-06T09:59:59+08:00"},
        ],
    })
    community = report(tmp_path)["community"]
    assert community["latestRecordedPublication"]["recordedAt"] == "2026-11-06T09:59:59+08:00"


def test_plan_filename_date_does_not_claim_recent_activity(tmp_path: Path) -> None:
    folder = tmp_path / "docs/exec-plans/active"
    folder.mkdir(parents=True)
    (folder / "2026-08-17-old.md").write_text("Recently updated\n", encoding="utf-8")
    (folder / "2026-02-30-invalid.md").write_text("Unknown\n", encoding="utf-8")
    result = report(tmp_path)
    assert result["activePlans"]["count"] == 2
    assert result["activePlans"]["items"][0]["createdOnFromFilename"] is None
    assert result["activePlans"]["items"][1]["createdOnFromFilename"] == "2026-08-17"
    assert all(row["lastActivityAt"] is None for row in result["activePlans"]["items"])


@pytest.mark.parametrize("value", ["2026-11-06", "2026-11-06T10:00:00", "invalid"])
def test_cli_invalid_as_of_fails_without_creating_state(tmp_path: Path, capsys, value: str) -> None:
    assert main(["--repo-root", str(tmp_path), "readiness", "--as-of", value]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
    assert not list(tmp_path.iterdir())


def test_cli_diagnostics_succeed_without_policy_or_initialization(tmp_path: Path, capsys) -> None:
    assert main(["--repo-root", str(tmp_path), "readiness", "--as-of", AS_OF]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["reportKind"] == "local_evidence_diagnostic"
    assert result["findings"]
    assert not list(tmp_path.iterdir())
