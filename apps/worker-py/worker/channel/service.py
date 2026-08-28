from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import uuid
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from .providers import LegacyLedgerProvider, pid_alive
from .repo import SqliteChannelRepository, YouTubeReleaseJournal
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
    YouTubeReleaseResult,
    YouTubeReleaseSpec,
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


class YouTubeReleaseService:
    def __init__(
        self,
        provider: Any,
        journal: YouTubeReleaseJournal,
        *,
        expected_channel_id: str,
        now: Callable[[], str] = utc_now,
    ) -> None:
        self.provider = provider
        self.journal = journal
        self.expected_channel_id = expected_channel_id
        self.now = now

    @staticmethod
    def _fingerprint(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def preflight(self, spec: YouTubeReleaseSpec) -> str:
        if spec.qc_status != "pass":
            raise ValueError(f"Release QC has not passed for {spec.content_id}: {spec.qc_status}")
        for label, path in (
            ("video", spec.video_path),
            ("thumbnail", spec.thumbnail_path),
            ("captions", spec.captions_path),
        ):
            if path is not None and not path.is_file():
                raise FileNotFoundError(f"YouTube {label} artifact is missing: {path}")
        scheduled = datetime.fromisoformat(spec.scheduled_at)
        if scheduled.tzinfo is None:
            raise ValueError(f"Scheduled time must be timezone-aware: {spec.scheduled_at}")
        if scheduled <= datetime.fromisoformat(self.now()):
            raise ValueError(f"Scheduled time is not in the future: {spec.scheduled_at}")
        return self._fingerprint(spec.video_path)

    def _assert_channel(self) -> None:
        actual = self.provider.channel_id()
        if actual != self.expected_channel_id:
            raise PermissionError(
                f"OAuth channel mismatch: expected {self.expected_channel_id}, got {actual}"
            )

    def adopt(self, spec: YouTubeReleaseSpec, video_id: str) -> YouTubeReleaseResult:
        fingerprint = self.preflight(spec)
        self._assert_channel()
        remote = self.provider.fetch(video_id)
        if remote.title != spec.title:
            raise ValueError(
                f"Remote title mismatch for {spec.content_id}: {remote.title!r} != {spec.title!r}"
            )
        self.journal.record(
            spec.content_id,
            videoFingerprint=fingerprint,
            youtubeVideoId=video_id,
            state="adopted_private",
            updatedAt=self.now(),
        )
        return YouTubeReleaseResult(
            content_id=spec.content_id,
            video_id=video_id,
            state="adopted_private",
            scheduled_at=remote.publish_at,
            uploaded=False,
            thumbnail_set=False,
            captions_set=False,
        )

    def sync(
        self,
        spec: YouTubeReleaseSpec,
        *,
        apply_upload: bool,
        apply_schedule: bool,
    ) -> YouTubeReleaseResult:
        fingerprint = self.preflight(spec)
        existing = self.journal.entry(spec.content_id) or {}
        if existing.get("videoFingerprint") not in {None, fingerprint}:
            raise ValueError(f"Video fingerprint changed for {spec.content_id}")
        video_id = existing.get("youtubeVideoId")
        if not video_id and spec.youtube_video_id:
            self._assert_channel()
            adopted = self.provider.fetch(spec.youtube_video_id)
            if adopted.title != spec.title:
                raise ValueError(
                    f"Remote title mismatch for {spec.content_id}: "
                    f"{adopted.title!r} != {spec.title!r}"
                )
            video_id = spec.youtube_video_id
            existing.update(
                {
                    "videoFingerprint": fingerprint,
                    "youtubeVideoId": video_id,
                    "state": "adopted_private",
                    "thumbnailSet": spec.assets_already_set and spec.thumbnail_path is not None,
                    "captionsSet": spec.assets_already_set and spec.captions_path is not None,
                }
            )
            existing["updatedAt"] = self.now()
            self.journal.record(spec.content_id, **existing)
        if not video_id and not apply_upload:
            return YouTubeReleaseResult(
                content_id=spec.content_id,
                video_id=None,
                state="ready_to_upload",
                scheduled_at=None,
                uploaded=False,
                thumbnail_set=False,
                captions_set=False,
            )
        self._assert_channel()
        uploaded = False
        if not video_id:
            video_id = self.provider.upload_private(spec)
            uploaded = True
            self.journal.record(
                spec.content_id,
                videoFingerprint=fingerprint,
                youtubeVideoId=video_id,
                state="uploaded_private",
                uploadedAt=self.now(),
                updatedAt=self.now(),
            )
        remote = self.provider.fetch(str(video_id))
        if remote.title != spec.title:
            raise ValueError(
                f"Remote title mismatch for {spec.content_id}: {remote.title!r} != {spec.title!r}"
            )
        if remote.failure_reason or remote.rejection_reason:
            raise RuntimeError(
                f"YouTube rejected {spec.content_id}: "
                f"{remote.failure_reason or remote.rejection_reason}"
            )
        thumbnail_set = bool(existing.get("thumbnailSet"))
        captions_set = bool(existing.get("captionsSet"))
        playlist_set = bool(existing.get("playlistItemId"))
        if apply_upload and spec.thumbnail_path is not None and not thumbnail_set:
            self.provider.set_thumbnail(str(video_id), spec.thumbnail_path)
            thumbnail_set = True
        if apply_upload and spec.captions_path is not None and not captions_set:
            caption_id = self.provider.upsert_captions(
                str(video_id), spec.captions_path, language=spec.language
            )
            captions_set = True
            existing["captionId"] = caption_id
        if apply_upload and spec.playlist_id and not playlist_set:
            existing["playlistItemId"] = self.provider.add_to_playlist(
                str(video_id), spec.playlist_id
            )
            playlist_set = True
        state = "uploaded_private"
        detail = None
        scheduled_at = remote.publish_at
        if apply_schedule:
            if remote.upload_status != "processed" or remote.processing_status != "succeeded":
                state = "awaiting_processing"
                detail = (
                    f"uploadStatus={remote.upload_status}; "
                    f"processingStatus={remote.processing_status}"
                )
            else:
                scheduled_utc = datetime.fromisoformat(spec.scheduled_at).astimezone(timezone.utc)
                normalized = scheduled_utc.isoformat(timespec="seconds").replace("+00:00", "Z")
                already_scheduled = False
                if remote.publish_at:
                    remote_time = datetime.fromisoformat(remote.publish_at.replace("Z", "+00:00"))
                    already_scheduled = remote_time == scheduled_utc
                if not already_scheduled:
                    self.provider.schedule(str(video_id), normalized, spec)
                verified = remote if already_scheduled else self.provider.fetch(str(video_id))
                if verified.privacy_status != "private" or verified.publish_at is None:
                    raise RuntimeError(f"YouTube schedule did not persist for {spec.content_id}")
                state = "scheduled"
                scheduled_at = verified.publish_at
        if spec.related_video_id:
            detail = (
                (detail + "; " if detail else "")
                + "Studio fallback required for the Shorts Related Video field"
            )
        journal_changes = dict(existing)
        journal_changes.update(
            {
                "videoFingerprint": fingerprint,
                "youtubeVideoId": str(video_id),
                "state": state,
                "scheduledAt": scheduled_at,
                "thumbnailSet": thumbnail_set,
                "captionsSet": captions_set,
                "playlistSet": playlist_set,
                "relatedVideoId": spec.related_video_id,
                "updatedAt": self.now(),
            }
        )
        self.journal.record(spec.content_id, **journal_changes)
        return YouTubeReleaseResult(
            content_id=spec.content_id,
            video_id=str(video_id),
            state=state,
            scheduled_at=scheduled_at,
            uploaded=uploaded,
            thumbnail_set=thumbnail_set,
            captions_set=captions_set,
            detail=detail,
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
