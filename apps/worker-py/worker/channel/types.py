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

