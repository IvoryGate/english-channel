from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from pathlib import Path
from typing import Callable

from .providers import LegacyLedgerProvider, pid_alive
from .repo import SqliteChannelRepository
from .schema import (
    normalize_classics_ledgers,
    normalize_dialogue_ledger,
    normalize_shorts_ledger,
)
from .types import (
    ChannelPolicy,
    ImportRequest,
    ImportSummary,
    InventorySummary,
    ResourceLease,
    ResourcePolicy,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ChannelIdentityService:
    def __init__(
        self,
        policy: ChannelPolicy,
        repository: SqliteChannelRepository,
        legacy_provider: LegacyLedgerProvider | None = None,
        *,
        now: Callable[[], str] = utc_now,
    ) -> None:
        self.policy = policy
        self.repository = repository
        self.legacy_provider = legacy_provider or LegacyLedgerProvider()
        self.now = now

    def initialize(self) -> InventorySummary:
        now = self.now()
        self.repository.migrate(now)
        self.repository.seed_policy(self.policy, now)
        return self.repository.inventory()

    def _validate_request(self, request: ImportRequest) -> None:
        for record in request.records:
            if record.source_system != request.source.source_system:
                raise ValueError("Normalized record source system differs from import source")
            try:
                series = self.policy.series_policy(record.series_id)
            except KeyError as exc:
                raise ValueError(f"Import references unknown series {record.series_id}") from exc
            if series.product_line_id != record.product_line_id:
                raise ValueError(
                    f"Series {record.series_id} belongs to {series.product_line_id}, "
                    f"not {record.product_line_id}"
                )

    def _import(self, request: ImportRequest) -> ImportSummary:
        self.initialize()
        self._validate_request(request)
        return self.repository.import_identities(self.policy, request, self.now())

    def import_dialogue(self, path: Path) -> ImportSummary:
        source = self.legacy_provider.read_json(
            path, source_system="dialogue_publications_v1", collected_at=self.now()
        )
        return self._import(ImportRequest(source, normalize_dialogue_ledger(source)))

    def import_shorts(self, path: Path) -> ImportSummary:
        source = self.legacy_provider.read_json(
            path, source_system="shorts_publications_v1", collected_at=self.now()
        )
        return self._import(ImportRequest(source, normalize_shorts_ledger(source)))

    def import_classics(self, root: Path) -> ImportSummary:
        source = self.legacy_provider.read_classics(root, collected_at=self.now())
        return self._import(ImportRequest(source, normalize_classics_ledgers(source)))

    def inventory(self) -> InventorySummary:
        return self.repository.inventory()


class ResourceBusyError(RuntimeError):
    def __init__(self, lease: ResourceLease) -> None:
        self.lease = lease
        super().__init__(
            f"Resource {lease.resource_id} is held by pid={lease.owner_pid} "
            f"label={lease.label} until {lease.expires_at}"
        )


class ResourceLeaseService:
    def __init__(
        self,
        repository: SqliteChannelRepository,
        policies: tuple[ResourcePolicy, ...],
        *,
        now: Callable[[], str] = utc_now,
        is_pid_alive: Callable[[int], bool] = pid_alive,
    ) -> None:
        self.repository = repository
        self.policies = {item.resource_id: item for item in policies}
        self.now = now
        self.is_pid_alive = is_pid_alive

    def policy(self, resource_id: str) -> ResourcePolicy:
        try:
            return self.policies[resource_id]
        except KeyError as exc:
            raise ValueError(f"Unknown resource: {resource_id}") from exc

    @staticmethod
    def _parse(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError(f"Lease timestamp must be timezone-aware: {value}")
        return parsed

    def _candidate(
        self, resource_id: str, owner_id: str, owner_pid: int, parent_pid: int,
        label: str, priority: int,
    ) -> ResourceLease:
        policy = self.policy(resource_id)
        now = self._parse(self.now())
        expires = now + timedelta(seconds=policy.lease_ttl_sec)
        intent = hashlib.sha256(
            f"{resource_id}\0{owner_id}\0{label}".encode("utf-8")
        ).hexdigest()
        return ResourceLease(
            lease_id=f"lease:{uuid.uuid4()}", resource_id=resource_id,
            owner_id=owner_id, owner_pid=owner_pid, parent_pid=parent_pid,
            label=label, intent_hash=intent, priority=priority,
            acquired_at=now.isoformat(timespec="seconds"),
            heartbeat_at=now.isoformat(timespec="seconds"),
            expires_at=expires.isoformat(timespec="seconds"),
        )

    def acquire(
        self, resource_id: str, *, owner_id: str, owner_pid: int,
        parent_pid: int, label: str, priority: int = 0,
    ) -> ResourceLease:
        candidate = self._candidate(
            resource_id, owner_id, owner_pid, parent_pid, label, priority
        )
        existing = self.repository.try_acquire_lease(candidate)
        if existing is None:
            return candidate
        if existing.owner_id == owner_id:
            return self.heartbeat(existing)
        now = self._parse(candidate.acquired_at)
        if now < self._parse(existing.expires_at) or self.is_pid_alive(existing.owner_pid):
            raise ResourceBusyError(existing)
        raced = self.repository.recover_and_acquire(existing.lease_id, candidate, candidate.acquired_at)
        if raced is not None:
            raise ResourceBusyError(raced)
        return candidate

    def heartbeat(self, lease: ResourceLease) -> ResourceLease:
        policy = self.policy(lease.resource_id)
        now = self._parse(self.now())
        expires = now + timedelta(seconds=policy.lease_ttl_sec)
        return self.repository.heartbeat_lease(
            lease.lease_id, lease.owner_id, now.isoformat(timespec="seconds"),
            expires.isoformat(timespec="seconds"),
        )

    def release(self, lease: ResourceLease, reason: str = "completed") -> bool:
        return self.repository.release_lease(
            lease.lease_id, lease.owner_id, self.now(), reason
        )
