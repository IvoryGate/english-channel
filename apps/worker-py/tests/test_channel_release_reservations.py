from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.channel.repo import RepositoryError, SqliteChannelRepository
from worker.channel.schema import parse_channel_policy, parse_release_policy
from worker.channel.service import ChannelIdentityService, ReleaseReservationService
from worker.channel.transport import main as channel_main


NOW = "2026-08-24T00:00:00+00:00"
REPO = Path(__file__).resolve().parents[3]


def channel_policy():
    return parse_channel_policy(
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


def release_payload(*, capacity: int = 2) -> dict[str, object]:
    return {
        "schema": "youtube-channel-release-policy-v1",
        "timezone": "Asia/Shanghai",
        "authority": {
            "defaultPrivacy": "private",
            "publicSchedulingEnabled": False,
            "explicitApprovalRequired": True,
        },
        "capacity": {
            "maxChannelUploadsPerRolling7Days": capacity,
            "reservationRequired": True,
        },
        "programs": {
            "dialogue_active": {
                "productLine": "dialogue",
                "status": "active",
                "startsOn": "2026-08-24",
                "endsOn": "2026-08-31",
                "preferredDailyWindows": ["20:30"],
            },
            "dialogue_blocked": {
                "productLine": "dialogue",
                "status": "reconciliation_required",
                "preferredDailyWindows": [],
            },
            "shorts_active": {
                "productLine": "shorts",
                "status": "active",
                "preferredDailyWindows": ["08:00"],
            },
        },
    }


def build_service(tmp_path: Path, *, capacity: int = 2) -> ReleaseReservationService:
    policy = channel_policy()
    repository = SqliteChannelRepository(tmp_path / "channel.sqlite")
    identity = ChannelIdentityService(policy, repository, now=lambda: NOW)
    ledger = tmp_path / "dialogue.json"
    ledger.write_text(
        json.dumps(
            {
                "schema": "elr-publication-ledger-v1",
                "publications": [
                    {
                        "showId": "series_a",
                        "episodeId": index,
                        "title": f"Episode {index}",
                        "status": "approved",
                    }
                    for index in range(1, 5)
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    identity.import_dialogue(ledger)
    return ReleaseReservationService(
        policy, parse_release_policy(release_payload(capacity=capacity)),
        repository, now=lambda: NOW,
    )


def reserve(
    service: ReleaseReservationService,
    episode: int,
    when: str,
    key: str,
):
    return service.reserve(
        content_id=f"content:series_a:episode_{episode:03d}",
        program_id="dialogue_active",
        scheduled_at=when,
        idempotency_key=key,
    )


def test_reservation_is_idempotent_and_cancellation_retains_history(tmp_path: Path) -> None:
    service = build_service(tmp_path)
    first, inserted = reserve(service, 1, "2026-08-25T20:30:00+08:00", "release-1")
    repeated, repeated_inserted = reserve(
        service, 1, "2026-08-25T20:30:00+08:00", "release-1"
    )

    assert inserted is True
    assert repeated_inserted is False
    assert repeated.reservation_id == first.reservation_id
    with pytest.raises(RepositoryError, match="different intent"):
        reserve(service, 2, "2026-08-26T20:30:00+08:00", "release-1")

    cancelled = service.cancel(first.reservation_id, reason="portfolio changed")
    replacement, replacement_inserted = reserve(
        service, 1, "2026-08-26T20:30:00+08:00", "release-1-replacement"
    )

    assert cancelled.cancelled_at is not None
    assert cancelled.cancellation_reason == "portfolio changed"
    assert replacement_inserted is True
    assert service.list() == (replacement,)
    assert len(service.list(active_only=False)) == 2


def test_program_identity_and_date_gates_fail_closed(tmp_path: Path) -> None:
    service = build_service(tmp_path)

    with pytest.raises(ValueError, match="not active"):
        service.reserve(
            content_id="content:series_a:episode_001",
            program_id="dialogue_blocked",
            scheduled_at="2026-08-25T20:30:00+08:00",
            idempotency_key="blocked",
        )
    with pytest.raises(ValueError, match="not release program shorts"):
        service.reserve(
            content_id="content:series_a:episode_001",
            program_id="shorts_active",
            scheduled_at="2026-08-25T08:00:00+08:00",
            idempotency_key="wrong-product",
        )
    with pytest.raises(ValueError, match="after program"):
        reserve(service, 1, "2026-09-01T20:30:00+08:00", "outside-window")
    with pytest.raises(ValueError, match="timezone-aware"):
        reserve(service, 1, "2026-08-25T20:30:00", "naive")


def test_exact_slot_and_rolling_capacity_conflicts_are_transactional(tmp_path: Path) -> None:
    service = build_service(tmp_path, capacity=2)
    reserve(service, 1, "2026-08-25T20:30:00+08:00", "one")

    with pytest.raises(RepositoryError, match="already reserved"):
        reserve(service, 2, "2026-08-25T20:30:00+08:00", "same-time")

    reserve(service, 2, "2026-08-27T20:30:00+08:00", "two")
    with pytest.raises(RepositoryError, match="rolling seven-day"):
        reserve(service, 3, "2026-08-29T20:30:00+08:00", "three")
    assert len(service.list()) == 2


def test_release_commands_reserve_report_and_cancel_without_remote_authority(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    service = build_service(tmp_path)
    reserve(service, 1, "2026-08-25T20:30:00+08:00", "cli-status")
    policy_path = tmp_path / "control-plane.json"
    release_path = tmp_path / "release-policy.json"
    policy_path.write_text(
        json.dumps(
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
        ),
        encoding="utf-8",
        newline="\n",
    )
    cli_release_payload = release_payload()
    cli_program = cli_release_payload["programs"]["dialogue_active"]
    cli_program["startsOn"] = "2099-08-24"
    cli_program["endsOn"] = "2099-08-31"
    release_path.write_text(
        json.dumps(cli_release_payload), encoding="utf-8", newline="\n"
    )

    common = [
        "--repo-root", str(REPO),
        "--policy", str(policy_path),
        "--database", str(service.repository.database),
        "--release-policy", str(release_path),
    ]
    reserve_exit = channel_main(
        [
            *common,
            "release", "reserve",
            "--content-id", "content:series_a:episode_002",
            "--program", "dialogue_active",
            "--scheduled-at", "2099-08-26T20:30:00+08:00",
            "--idempotency-key", "cli-reserve",
        ]
    )
    reserve_output = json.loads(capsys.readouterr().out)
    reservation_id = reserve_output["reservation"]["reservationId"]

    status_exit = channel_main(
        [
            *common,
            "release", "status",
        ]
    )
    status_output = json.loads(capsys.readouterr().out)

    cancel_exit = channel_main(
        [
            *common,
            "release", "cancel",
            "--reservation-id", reservation_id,
            "--reason", "fixture complete",
        ]
    )
    cancel_output = json.loads(capsys.readouterr().out)

    assert reserve_exit == status_exit == cancel_exit == 0
    assert reserve_output["inserted"] is True
    assert len(status_output["reservations"]) == 2
    assert cancel_output["reservation"]["cancelledAt"] is not None
    for output in (reserve_output, status_output, cancel_output):
        assert output["publicSchedulingAuthority"] is False
        assert output["remoteMutationAuthority"] is False
