from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from .providers import LegacyLedgerProvider, pid_alive
from .repo import SqliteChannelRepository
from .schema import (
    normalize_classics_ledgers,
    normalize_dialogue_ledger,
    normalize_shorts_ledger,
    parse_youtube_rss,
)
from .types import (
    ChannelPolicy,
    ImportRequest,
    ImportSummary,
    InventorySummary,
    ReconciliationReport,
    ReleasePolicy,
    ReleaseReservation,
    RemoteInventoryCapture,
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

    def import_youtube_rss(self, path: Path, *, scope: str) -> tuple[str, bool, int]:
        self.initialize()
        declared_scope = scope.strip()
        if not declared_scope:
            raise ValueError("Remote inventory capture scope must not be empty")
        resolved, value, source_sha256 = self.legacy_provider.read_bytes(path)
        channel_id, items = parse_youtube_rss(value)
        capture = RemoteInventoryCapture(
            capture_id=f"capture:{uuid.uuid4()}",
            provider="youtube_public_rss",
            channel_id=channel_id,
            scope=declared_scope,
            source_locator=str(resolved),
            source_sha256=source_sha256,
            collected_at=self.now(),
            items=items,
        )
        capture_id, inserted = self.repository.import_remote_capture(capture)
        return capture_id, inserted, len(items)

    def reconcile(self, capture_id: str | None = None) -> ReconciliationReport:
        return self.repository.reconcile_remote_capture(capture_id)


class ResourceBusyError(RuntimeError):
    def __init__(self, lease: ResourceLease) -> None:
        self.lease = lease
        super().__init__(
            f"Resource {lease.resource_id} is held by pid={lease.owner_pid} "
            f"label={lease.label} until {lease.expires_at}"
        )


class ReleaseReservationService:
    def __init__(
        self,
        channel_policy: ChannelPolicy,
        release_policy: ReleasePolicy,
        repository: SqliteChannelRepository,
        *,
        now: Callable[[], str] = utc_now,
    ) -> None:
        self.channel_policy = channel_policy
        self.release_policy = release_policy
        self.repository = repository
        self.now = now
        known = {item.product_line_id for item in channel_policy.product_lines}
        unknown = {
            item.product_line_id for item in release_policy.programs
            if item.product_line_id not in known
        }
        if unknown:
            raise ValueError(f"Release policy references unknown product lines: {sorted(unknown)}")

    @staticmethod
    def _timestamp(value: str, where: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{where} must be ISO-8601: {value}") from exc
        if parsed.tzinfo is None:
            raise ValueError(f"{where} must be timezone-aware: {value}")
        return parsed

    def reserve(
        self, *, content_id: str, program_id: str, scheduled_at: str,
        idempotency_key: str,
    ) -> tuple[ReleaseReservation, bool]:
        try:
            program = self.release_policy.program(program_id)
        except KeyError as exc:
            raise ValueError(f"Unknown release program: {program_id}") from exc
        if program.status != "active":
            raise ValueError(
                f"Release program {program_id} is not active: {program.status}"
            )
        key = idempotency_key.strip()
        if not key:
            raise ValueError("Release idempotency key must not be empty")
        product_line = self.repository.content_product_line(content_id)
        if product_line is None:
            raise ValueError(f"Unknown canonical content item: {content_id}")
        if product_line != program.product_line_id:
            raise ValueError(
                f"Content belongs to {product_line}, not release program {program.product_line_id}"
            )
        now = self._timestamp(self.now(), "Current time")
        scheduled = self._timestamp(scheduled_at, "Scheduled time")
        if scheduled <= now:
            raise ValueError("Release reservation must be in the future")
        local_date = scheduled.astimezone(ZoneInfo(self.release_policy.timezone)).date()
        if program.starts_on and local_date < datetime.fromisoformat(program.starts_on).date():
            raise ValueError(f"Release time is before program {program_id} starts")
        if program.ends_on and local_date > datetime.fromisoformat(program.ends_on).date():
            raise ValueError(f"Release time is after program {program_id} ends")
        normalized = scheduled.astimezone(timezone.utc).isoformat(timespec="seconds")
        intent_hash = hashlib.sha256(
            f"{content_id}\0{program_id}\0{normalized}".encode("utf-8")
        ).hexdigest()
        candidate = ReleaseReservation(
            reservation_id=f"release:{uuid.uuid4()}",
            content_id=content_id,
            program_id=program_id,
            scheduled_at=normalized,
            timezone=self.release_policy.timezone,
            idempotency_key=key,
            intent_hash=intent_hash,
            created_at=now.astimezone(timezone.utc).isoformat(timespec="seconds"),
        )
        return self.repository.reserve_release(
            candidate,
            max_rolling_7_days=self.release_policy.max_uploads_per_rolling_7_days,
        )

    def list(self, *, active_only: bool = True) -> tuple[ReleaseReservation, ...]:
        return self.repository.list_release_reservations(active_only=active_only)

    def cancel(self, reservation_id: str, *, reason: str) -> ReleaseReservation:
        detail = reason.strip()
        if not detail:
            raise ValueError("Cancellation reason must not be empty")
        cancelled = self._timestamp(self.now(), "Current time")
        return self.repository.cancel_release_reservation(
            reservation_id,
            cancelled_at=cancelled.astimezone(timezone.utc).isoformat(timespec="seconds"),
            reason=detail,
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
