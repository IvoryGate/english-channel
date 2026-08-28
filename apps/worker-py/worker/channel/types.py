from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProductLinePolicy:
    product_line_id: str
    name: str


@dataclass(frozen=True)
class SeriesPolicy:
    series_id: str
    product_line_id: str
    name: str


@dataclass(frozen=True)
class ChannelPolicy:
    channel_id: str
    public_name: str
    product_lines: tuple[ProductLinePolicy, ...]
    series: tuple[SeriesPolicy, ...]

    def product_line(self, product_line_id: str) -> ProductLinePolicy:
        for item in self.product_lines:
            if item.product_line_id == product_line_id:
                return item
        raise KeyError(product_line_id)

    def series_policy(self, series_id: str) -> SeriesPolicy:
        for item in self.series:
            if item.series_id == series_id:
                return item
        raise KeyError(series_id)


@dataclass(frozen=True)
class LegacySource:
    source_system: str
    locator: str
    sha256: str
    collected_at: str
    payload: Any


@dataclass(frozen=True)
class NormalizedIdentityRecord:
    source_system: str
    source_item_id: str
    source_locator: str
    product_line_id: str
    series_id: str
    local_item_id: str
    title: str | None
    source_state: str | None
    media_sha256: str | None
    youtube_video_id: str | None
    publication_status: str | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class ImportRequest:
    source: LegacySource
    records: tuple[NormalizedIdentityRecord, ...]


@dataclass(frozen=True)
class ImportSummary:
    import_run_id: str
    source_system: str
    source_locator: str
    source_sha256: str
    total: int
    inserted: int
    updated: int
    unchanged: int
    collided: int
    collision_count: int


@dataclass(frozen=True)
class CollisionRecord:
    collision_id: int
    import_run_id: str
    source_system: str
    source_item_id: str
    kind: str
    identity_key: str
    existing_content_id: str | None
    incoming_content_id: str
    detail: str
    created_at: str
    resolved_at: str | None = None


@dataclass(frozen=True)
class InventorySummary:
    database: Path
    schema_version: int
    channel_count: int
    product_line_count: int
    series_count: int
    content_item_count: int
    source_alias_count: int
    artifact_count: int
    publication_count: int
    import_run_count: int
    unresolved_collision_count: int
    content_by_product_line: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ResourcePolicy:
    resource_id: str
    capacity: int
    lease_ttl_sec: int
    heartbeat_interval_sec: int
    recovery: str


@dataclass(frozen=True)
class ResourceLease:
    lease_id: str
    resource_id: str
    owner_id: str
    owner_pid: int
    parent_pid: int
    label: str
    intent_hash: str
    priority: int
    acquired_at: str
    heartbeat_at: str
    expires_at: str
    released_at: str | None = None
    release_reason: str | None = None


@dataclass(frozen=True)
class RemoteInventoryItem:
    remote_id: str
    title: str
    published_at: str | None
    updated_at: str | None
    url: str
    media_kind: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class RemoteInventoryCapture:
    capture_id: str
    provider: str
    channel_id: str
    scope: str
    source_locator: str
    source_sha256: str
    collected_at: str
    items: tuple[RemoteInventoryItem, ...]


@dataclass(frozen=True)
class ReconciliationReport:
    capture_id: str
    channel_id: str
    scope: str
    remote_count: int
    local_publication_count: int
    matched_remote_ids: tuple[str, ...]
    remote_only_ids: tuple[str, ...]
    local_outside_capture_ids: tuple[str, ...]
    title_disagreements: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class ReleaseProgramPolicy:
    program_id: str
    product_line_id: str
    status: str
    starts_on: str | None
    ends_on: str | None
    preferred_daily_windows: tuple[str, ...]


@dataclass(frozen=True)
class ReleasePolicy:
    timezone: str
    default_privacy: str
    public_scheduling_enabled: bool
    explicit_approval_required: bool
    max_uploads_per_rolling_7_days: int
    reservation_required: bool
    programs: tuple[ReleaseProgramPolicy, ...]

    def program(self, program_id: str) -> ReleaseProgramPolicy:
        for item in self.programs:
            if item.program_id == program_id:
                return item
        raise KeyError(program_id)


@dataclass(frozen=True)
class ReleaseReservation:
    reservation_id: str
    content_id: str
    program_id: str
    scheduled_at: str
    timezone: str
    idempotency_key: str
    intent_hash: str
    created_at: str
    cancelled_at: str | None = None
    cancellation_reason: str | None = None


@dataclass(frozen=True)
class YouTubeReleaseSpec:
    content_id: str
    video_path: Path
    title: str
    description: str
    scheduled_at: str
    thumbnail_path: Path | None = None
    captions_path: Path | None = None
    tags: tuple[str, ...] = ()
    playlist_id: str | None = None
    related_video_id: str | None = None
    category_id: str = "27"
    language: str = "en"
    made_for_kids: bool = False
    contains_synthetic_media: bool = True
    notify_subscribers: bool = False
    qc_status: str = "pending"
    youtube_video_id: str | None = None
    assets_already_set: bool = False


@dataclass(frozen=True)
class YouTubeRemoteVideo:
    video_id: str
    title: str
    privacy_status: str
    publish_at: str | None
    upload_status: str
    processing_status: str | None
    failure_reason: str | None = None
    rejection_reason: str | None = None


@dataclass(frozen=True)
class YouTubeReleaseResult:
    content_id: str
    video_id: str | None
    state: str
    scheduled_at: str | None
    uploaded: bool
    thumbnail_set: bool
    captions_set: bool
    detail: str | None = None
