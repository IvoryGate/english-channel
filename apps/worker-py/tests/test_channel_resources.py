from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from worker.channel.repo import SqliteChannelRepository
from worker.channel.schema import parse_resource_policies
from worker.channel.service import ResourceBusyError, ResourceLeaseService


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self.value.isoformat(timespec="seconds")

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def policies():
    return parse_resource_policies(
        {
            "schema": "youtube-channel-resources-v1",
            "resources": [
                {
                    "id": "gpu_heavy",
                    "capacity": 1,
                    "leaseTtlSec": 120,
                    "heartbeatIntervalSec": 30,
                    "recovery": "expired_and_owner_dead",
                }
            ],
        }
    )


def lease_service(tmp_path: Path, clock: Clock, alive: dict[int, bool]):
    repository = SqliteChannelRepository(tmp_path / "channel.sqlite")
    repository.migrate(clock())
    return ResourceLeaseService(
        repository, policies(), now=clock, is_pid_alive=lambda pid: alive.get(pid, False)
    )


def acquire(service: ResourceLeaseService, owner: str, pid: int):
    return service.acquire(
        "gpu_heavy", owner_id=owner, owner_pid=pid, parent_pid=1,
        label=f"job:{owner}",
    )


def test_exclusive_lease_rejects_a_second_owner(tmp_path: Path) -> None:
    clock = Clock()
    service = lease_service(tmp_path, clock, {100: True, 200: True})
    first = acquire(service, "owner-1", 100)

    with pytest.raises(ResourceBusyError) as error:
        acquire(service, "owner-2", 200)

    assert error.value.lease.lease_id == first.lease_id
    assert service.repository.active_lease("gpu_heavy") == first


def test_live_owner_cannot_be_evicted_after_expiry(tmp_path: Path) -> None:
    clock = Clock()
    alive = {100: True, 200: True}
    service = lease_service(tmp_path, clock, alive)
    first = acquire(service, "owner-1", 100)
    clock.advance(121)

    with pytest.raises(ResourceBusyError):
        acquire(service, "owner-2", 200)

    assert service.repository.active_lease("gpu_heavy").lease_id == first.lease_id


def test_expired_dead_owner_is_recovered_with_history(tmp_path: Path) -> None:
    clock = Clock()
    alive = {100: True, 200: True}
    service = lease_service(tmp_path, clock, alive)
    first = acquire(service, "owner-1", 100)
    clock.advance(121)
    alive[100] = False

    second = acquire(service, "owner-2", 200)
    history = service.repository.list_leases(active_only=False)

    assert second.lease_id != first.lease_id
    assert history[0].released_at is not None
    assert history[0].release_reason == "expired_owner_dead"
    assert history[1].lease_id == second.lease_id


def test_heartbeat_extends_and_release_closes_lease(tmp_path: Path) -> None:
    clock = Clock()
    service = lease_service(tmp_path, clock, {100: True})
    first = acquire(service, "owner-1", 100)
    clock.advance(30)

    renewed = service.heartbeat(first)

    assert renewed.expires_at > first.expires_at
    assert service.release(renewed)
    assert service.repository.active_lease("gpu_heavy") is None


def test_legacy_gpu_api_uses_sqlite_lease_and_compatibility_mirror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    configs = repo / "configs" / "channel"
    configs.mkdir(parents=True)
    (configs / "control-plane.json").write_text(
        json.dumps(
            {
                "schema": "youtube-channel-control-plane-v1",
                "channel": {"id": "test_channel", "publicName": "Test"},
                "productLines": [{"id": "dialogue", "name": "Dialogue"}],
                "series": [
                    {"id": "series_a", "productLineId": "dialogue", "name": "A"}
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    (configs / "resources.json").write_text(
        json.dumps(
            {
                "schema": "youtube-channel-resources-v1",
                "resources": [
                    {
                        "id": "gpu_heavy",
                        "capacity": 1,
                        "leaseTtlSec": 120,
                        "heartbeatIntervalSec": 30,
                        "recovery": "expired_and_owner_dead",
                    }
                ],
            }
        ),
        encoding="utf-8",
        newline="\n",
    )
    scripts = Path(__file__).resolve().parents[3] / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    lock = importlib.import_module("gpu_production_lock")
    monkeypatch.setattr(lock, "REPO", repo)
    monkeypatch.setattr(lock, "LOCK_PATH", repo / "logs" / "gpu_production.lock")

    with lock.GpuProductionLock("fixture-heavy-job"):
        repository = SqliteChannelRepository(repo / "workspace" / "channel" / "channel.sqlite")
        active = repository.active_lease("gpu_heavy")
        assert active is not None
        assert active.label == "fixture-heavy-job"
        assert lock.LOCK_PATH.is_file()
        with lock.GpuProductionLock("nested-heavy-step"):
            assert repository.active_lease("gpu_heavy").lease_id == active.lease_id
        assert repository.active_lease("gpu_heavy").lease_id == active.lease_id

    assert repository.active_lease("gpu_heavy") is None
    assert not lock.LOCK_PATH.exists()
