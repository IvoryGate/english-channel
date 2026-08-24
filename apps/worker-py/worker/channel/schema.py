from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .types import (
    ChannelPolicy,
    LegacySource,
    NormalizedIdentityRecord,
    ProductLinePolicy,
    ResourcePolicy,
    SeriesPolicy,
)


POLICY_SCHEMA = "youtube-channel-control-plane-v1"
IDENTIFIER_RE = re.compile(r"^[a-z0-9]+(?:[_-][a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EPISODE_RE = re.compile(r"^(?:episode[_-]?)?(\d{1,3})$", re.IGNORECASE)


class SchemaError(ValueError):
    pass


def _object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError(f"{where} must be an object")
    return value


def _string(value: dict[str, Any], key: str, where: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise SchemaError(f"{where}.{key} must be a non-empty string")
    return item.strip()


def validate_identifier(value: str, where: str) -> str:
    if not IDENTIFIER_RE.fullmatch(value):
        raise SchemaError(f"{where} must match {IDENTIFIER_RE.pattern}: {value!r}")
    return value


def validate_sha256(value: str, where: str) -> str:
    normalized = value.lower()
    if not SHA256_RE.fullmatch(normalized):
        raise SchemaError(f"{where} must be a SHA-256 digest")
    return normalized


def read_json_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return _object(json.load(handle), str(path))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_content_id(series_id: str, local_item_id: str) -> str:
    validate_identifier(series_id, "series_id")
    validate_identifier(local_item_id, "local_item_id")
    return f"content:{series_id}:{local_item_id}"


def normalize_episode_id(value: str | int) -> str:
    match = EPISODE_RE.fullmatch(str(value).strip())
    if not match:
        raise SchemaError(f"Invalid episode identity: {value!r}")
    number = int(match.group(1))
    if not 1 <= number <= 999:
        raise SchemaError(f"Episode number must be between 1 and 999: {number}")
    return f"episode_{number:03d}"


def parse_channel_policy(payload: dict[str, Any]) -> ChannelPolicy:
    if payload.get("schema") != POLICY_SCHEMA:
        raise SchemaError(f"Unsupported channel policy schema: {payload.get('schema')!r}")
    channel = _object(payload.get("channel"), "channel")
    channel_id = validate_identifier(_string(channel, "id", "channel"), "channel.id")
    public_name = _string(channel, "publicName", "channel")
    raw_product_lines = payload.get("productLines")
    if not isinstance(raw_product_lines, list) or not raw_product_lines:
        raise SchemaError("productLines must be a non-empty list")
    product_lines: list[ProductLinePolicy] = []
    product_ids: set[str] = set()
    for index, raw in enumerate(raw_product_lines):
        item = _object(raw, f"productLines[{index}]")
        item_id = validate_identifier(
            _string(item, "id", f"productLines[{index}]"), f"productLines[{index}].id"
        )
        if item_id in product_ids:
            raise SchemaError(f"Duplicate product line id: {item_id}")
        product_ids.add(item_id)
        product_lines.append(
            ProductLinePolicy(item_id, _string(item, "name", f"productLines[{index}]"))
        )
    raw_series = payload.get("series")
    if not isinstance(raw_series, list) or not raw_series:
        raise SchemaError("series must be a non-empty list")
    series: list[SeriesPolicy] = []
    series_ids: set[str] = set()
    for index, raw in enumerate(raw_series):
        item = _object(raw, f"series[{index}]")
        item_id = validate_identifier(_string(item, "id", f"series[{index}]"), f"series[{index}].id")
        product_id = validate_identifier(
            _string(item, "productLineId", f"series[{index}]"),
            f"series[{index}].productLineId",
        )
        if item_id in series_ids:
            raise SchemaError(f"Duplicate series id: {item_id}")
        if product_id not in product_ids:
            raise SchemaError(f"Series {item_id} references unknown product line {product_id}")
        series_ids.add(item_id)
        series.append(SeriesPolicy(item_id, product_id, _string(item, "name", f"series[{index}]")))
    return ChannelPolicy(channel_id, public_name, tuple(product_lines), tuple(series))


def load_channel_policy(path: Path) -> ChannelPolicy:
    return parse_channel_policy(read_json_object(path))


def parse_resource_policies(payload: dict[str, Any]) -> tuple[ResourcePolicy, ...]:
    if payload.get("schema") != "youtube-channel-resources-v1":
        raise SchemaError(f"Unsupported resource policy schema: {payload.get('schema')!r}")
    raw_resources = payload.get("resources")
    if not isinstance(raw_resources, list) or not raw_resources:
        raise SchemaError("resources must be a non-empty list")
    policies: list[ResourcePolicy] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_resources):
        item = _object(raw, f"resources[{index}]")
        resource_id = validate_identifier(
            _string(item, "id", f"resources[{index}]"), f"resources[{index}].id"
        )
        if resource_id in seen:
            raise SchemaError(f"Duplicate resource id: {resource_id}")
        seen.add(resource_id)
        capacity = item.get("capacity")
        ttl = item.get("leaseTtlSec")
        heartbeat = item.get("heartbeatIntervalSec")
        recovery = item.get("recovery")
        if capacity != 1:
            raise SchemaError(f"{resource_id}.capacity must be 1 in the initial scheduler")
        if not isinstance(ttl, int) or isinstance(ttl, bool) or ttl < 30:
            raise SchemaError(f"{resource_id}.leaseTtlSec must be at least 30")
        if not isinstance(heartbeat, int) or isinstance(heartbeat, bool) or heartbeat < 5:
            raise SchemaError(f"{resource_id}.heartbeatIntervalSec must be at least 5")
        if heartbeat * 2 >= ttl:
            raise SchemaError(f"{resource_id} heartbeat interval must be less than half its TTL")
        if recovery != "expired_and_owner_dead":
            raise SchemaError(f"Unsupported recovery policy for {resource_id}: {recovery!r}")
        policies.append(ResourcePolicy(resource_id, capacity, ttl, heartbeat, recovery))
    return tuple(policies)


def load_resource_policies(path: Path) -> tuple[ResourcePolicy, ...]:
    return parse_resource_policies(read_json_object(path))


def normalize_dialogue_ledger(source: LegacySource) -> tuple[NormalizedIdentityRecord, ...]:
    payload = _object(source.payload, source.locator)
    publications = payload.get("publications")
    if not isinstance(publications, list):
        raise SchemaError("Dialogue ledger publications must be a list")
    records: list[NormalizedIdentityRecord] = []
    for index, raw in enumerate(publications):
        item = _object(raw, f"publications[{index}]")
        series_id = validate_identifier(_string(item, "showId", f"publications[{index}]"), "showId")
        episode_id = normalize_episode_id(item.get("episodeId"))
        media_sha = item.get("mp4Sha256")
        youtube_id = item.get("videoId")
        records.append(
            NormalizedIdentityRecord(
                source_system=source.source_system,
                source_item_id=f"{series_id}/{episode_id}",
                source_locator=source.locator,
                product_line_id="dialogue",
                series_id=series_id,
                local_item_id=episode_id,
                title=str(item["title"]).strip() if item.get("title") else None,
                source_state=str(item["status"]) if item.get("status") else None,
                media_sha256=validate_sha256(str(media_sha), "mp4Sha256") if media_sha else None,
                youtube_video_id=str(youtube_id).strip() if youtube_id else None,
                publication_status=str(item["status"]) if item.get("status") else None,
                raw_payload=dict(item),
            )
        )
    return tuple(records)


def normalize_shorts_ledger(
    source: LegacySource, *, series_id: str = "shorts_main"
) -> tuple[NormalizedIdentityRecord, ...]:
    payload = _object(source.payload, source.locator)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise SchemaError("Shorts ledger entries must be a list")
    records: list[NormalizedIdentityRecord] = []
    for index, raw in enumerate(entries):
        item = _object(raw, f"entries[{index}]")
        short_id = validate_identifier(_string(item, "shortId", f"entries[{index}]"), "shortId")
        youtube_id = item.get("youtubeId")
        records.append(
            NormalizedIdentityRecord(
                source_system=source.source_system,
                source_item_id=short_id,
                source_locator=source.locator,
                product_line_id="shorts",
                series_id=series_id,
                local_item_id=short_id,
                title=None,
                source_state=str(item["status"]) if item.get("status") else None,
                media_sha256=None,
                youtube_video_id=str(youtube_id).strip() if youtube_id else None,
                publication_status=str(item["status"]) if item.get("status") else None,
                raw_payload=dict(item),
            )
        )
    return tuple(records)


def normalize_classics_ledgers(
    source: LegacySource, *, series_id: str = "classic_listening"
) -> tuple[NormalizedIdentityRecord, ...]:
    streams = source.payload
    if not isinstance(streams, list):
        raise SchemaError("Classics source payload must be a list of event streams")
    records: list[NormalizedIdentityRecord] = []
    for index, raw_stream in enumerate(streams):
        stream = _object(raw_stream, f"streams[{index}]")
        events = stream.get("events")
        if not isinstance(events, list) or not events:
            raise SchemaError(f"streams[{index}].events must be a non-empty list")
        first = _object(events[0], f"streams[{index}].events[0]")
        last = _object(events[-1], f"streams[{index}].events[-1]")
        book_slug = validate_identifier(_string(first, "bookSlug", "classics event"), "bookSlug")
        chapter = first.get("chapter")
        if not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1:
            raise SchemaError("classics event chapter must be a positive integer")
        for event_index, raw_event in enumerate(events):
            event = _object(raw_event, f"streams[{index}].events[{event_index}]")
            if event.get("bookSlug") != book_slug or event.get("chapter") != chapter:
                raise SchemaError(f"Classics event stream identity changes at event {event_index + 1}")
            if event.get("sequence") != event_index + 1:
                raise SchemaError(f"Classics event stream sequence breaks at event {event_index + 1}")
        evidence = _object(last.get("evidence", {}), "classics event evidence")
        youtube_id = evidence.get("youtubeVideoId")
        local_item_id = f"{book_slug}_chapter_{chapter:03d}"
        records.append(
            NormalizedIdentityRecord(
                source_system=source.source_system,
                source_item_id=f"{book_slug}/chapter_{chapter:03d}",
                source_locator=str(stream.get("locator", source.locator)),
                product_line_id="classic_listening",
                series_id=series_id,
                local_item_id=local_item_id,
                title=None,
                source_state=str(last.get("toState")) if last.get("toState") else None,
                media_sha256=None,
                youtube_video_id=str(youtube_id).strip() if youtube_id else None,
                publication_status=str(last.get("toState")) if youtube_id else None,
                raw_payload={"locator": stream.get("locator"), "events": events},
            )
        )
    return tuple(records)
