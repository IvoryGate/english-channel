from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .types import (
    AudioAcceptanceCase,
    AudioAcceptancePolicy,
    BookCatalogRecord,
    AuthorityLevel,
    LifecycleState,
    OperationEvent,
    RightsEvidence,
    RightsStatus,
    SeriesPolicy,
)


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SERIES_SCHEMA = "classic-listening-series-v1"
BOOK_SCHEMA = "classic-listening-catalog-book-v1"
AUDIO_ACCEPTANCE_SCHEMA = "classic-listening-audio-acceptance-v1"
EVENT_SCHEMA = "classic-listening-operation-event-v1"
REQUIRED_AUDIO_DIMENSIONS = {
    "narration",
    "dialogue",
    "fragile_short_line",
    "long_sentence",
    "names_and_dates",
    "sibilants",
}


class SchemaError(ValueError):
    pass


def _object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise SchemaError(f"{key} must be an object")
    return value


def _string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{key} must be a non-empty string")
    return value.strip()


def _positive_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SchemaError(f"{key} must be a positive integer")
    return value


def _string_list(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise SchemaError(f"{key} must be a non-empty string list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise SchemaError(f"{key} must be a non-empty string list")
    normalized = tuple(item.strip() for item in value)
    if len(set(normalized)) != len(normalized):
        raise SchemaError(f"{key} must not contain duplicates")
    return normalized


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SchemaError(f"Expected a JSON object: {path}")
    return payload


def parse_series_policy(payload: dict[str, Any]) -> SeriesPolicy:
    if payload.get("schema") != SERIES_SCHEMA:
        raise SchemaError(f"Unsupported series schema: {payload.get('schema')!r}")
    series = _object(payload, "series")
    cadence = _object(payload, "cadence")
    release = _object(payload, "release")
    analytics = _object(payload, "analytics")
    experiments = _object(payload, "experiments")
    slug = _string(series, "slug")
    if not SLUG_PATTERN.fullmatch(slug):
        raise SchemaError(f"Invalid series slug: {slug!r}")
    try:
        authority = AuthorityLevel(series.get("authorityLevel"))
    except (TypeError, ValueError) as exc:
        raise SchemaError("series.authorityLevel must be an integer from 0 to 3") from exc
    windows = analytics.get("snapshotWindowsHours")
    if not isinstance(windows, list) or not windows or not all(
        isinstance(item, int) and not isinstance(item, bool) and item > 0 for item in windows
    ):
        raise SchemaError("analytics.snapshotWindowsHours must be positive integers")
    if windows != sorted(set(windows)):
        raise SchemaError("analytics.snapshotWindowsHours must be unique and increasing")
    variants = _positive_int(experiments, "maxThumbnailVariants")
    if variants > 3:
        raise SchemaError("experiments.maxThumbnailVariants cannot exceed 3")
    single_variable = experiments.get("requireSingleChangedVariable")
    if not isinstance(single_variable, bool):
        raise SchemaError("experiments.requireSingleChangedVariable must be boolean")
    return SeriesPolicy(
        slug=slug,
        authority=authority,
        publication_territories=_string_list(series, "publicationTerritories"),
        chapters_per_week=_positive_int(cadence, "requestedChaptersPerWeek"),
        ready_buffer_chapters=_positive_int(cadence, "readyBufferChapters"),
        release_policy_ref=_string(release, "policyRef"),
        release_program_id=_string(release, "programId"),
        required_release_gates=_string_list(release, "requiredGates"),
        analytics_windows_hours=tuple(windows),
        max_thumbnail_variants=variants,
        require_single_changed_variable=single_variable,
    )


def parse_book_record(payload: dict[str, Any]) -> BookCatalogRecord:
    if payload.get("schema") != BOOK_SCHEMA:
        raise SchemaError(f"Unsupported book schema: {payload.get('schema')!r}")
    book = _object(payload, "book")
    rights = _object(payload, "rights")
    source = _object(payload, "source")
    slug = _string(book, "slug")
    if not SLUG_PATTERN.fullmatch(slug):
        raise SchemaError(f"Invalid book slug: {slug!r}")
    try:
        status = RightsStatus(_string(rights, "status"))
    except ValueError as exc:
        raise SchemaError(f"Invalid rights.status: {rights.get('status')!r}") from exc
    raw_evidence = rights.get("evidence")
    if not isinstance(raw_evidence, list):
        raise SchemaError("rights.evidence must be a list")
    evidence: list[RightsEvidence] = []
    for index, item in enumerate(raw_evidence):
        if not isinstance(item, dict):
            raise SchemaError(f"rights.evidence[{index}] must be an object")
        evidence.append(
            RightsEvidence(
                kind=_string(item, "kind"),
                territory=_string(item, "territory"),
                url=_string(item, "url"),
                note=_string(item, "note"),
            )
        )
    reviewed_at = rights.get("reviewedAt")
    if reviewed_at is not None and (not isinstance(reviewed_at, str) or not reviewed_at.strip()):
        raise SchemaError("rights.reviewedAt must be null or a non-empty string")
    territories = _string_list(rights, "approvedTerritories") if status is RightsStatus.VERIFIED_PUBLIC_DOMAIN else ()
    if status is RightsStatus.VERIFIED_PUBLIC_DOMAIN and (not evidence or not reviewed_at):
        raise SchemaError("Verified public-domain records require evidence and reviewedAt")
    return BookCatalogRecord(
        slug=slug,
        title=_string(book, "title"),
        author=_string(book, "author"),
        language=_string(book, "language"),
        first_published_year=_positive_int(book, "firstPublishedYear"),
        author_death_year=_positive_int(book, "authorDeathYear"),
        rights_status=status,
        approved_territories=territories,
        reviewed_at=reviewed_at.strip() if isinstance(reviewed_at, str) else None,
        evidence=tuple(evidence),
        source_url=_string(source, "url"),
    )


def parse_audio_acceptance_policy(payload: dict[str, Any]) -> AudioAcceptancePolicy:
    if payload.get("schema") != AUDIO_ACCEPTANCE_SCHEMA:
        raise SchemaError(f"Unsupported audio acceptance schema: {payload.get('schema')!r}")
    thresholds = _object(payload, "thresholds")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise SchemaError("cases must be a non-empty list")
    cases: list[AudioAcceptanceCase] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_cases):
        if not isinstance(item, dict):
            raise SchemaError(f"cases[{index}] must be an object")
        case_id = _string(item, "id")
        if case_id in seen:
            raise SchemaError(f"Duplicate audio case id: {case_id}")
        seen.add(case_id)
        cases.append(AudioAcceptanceCase(case_id, _string(item, "dimension"), _string(item, "text")))
    dimensions = {case.dimension for case in cases}
    missing = sorted(REQUIRED_AUDIO_DIMENSIONS - dimensions)
    if missing:
        raise SchemaError(f"Audio acceptance cases are missing dimensions: {', '.join(missing)}")
    similarity = thresholds.get("minimumAsrSimilarity")
    peak = thresholds.get("maximumTruePeakDbtp")
    clipped = thresholds.get("maximumClippedSamples")
    reviewers = thresholds.get("requiredBlindReviewers")
    if not isinstance(similarity, (int, float)) or isinstance(similarity, bool) or not 0 <= similarity <= 1:
        raise SchemaError("thresholds.minimumAsrSimilarity must be between 0 and 1")
    if not isinstance(peak, (int, float)) or isinstance(peak, bool) or peak > 0:
        raise SchemaError("thresholds.maximumTruePeakDbtp must be at most 0")
    if not isinstance(clipped, int) or isinstance(clipped, bool) or clipped < 0:
        raise SchemaError("thresholds.maximumClippedSamples must be a non-negative integer")
    if not isinstance(reviewers, int) or isinstance(reviewers, bool) or reviewers < 1:
        raise SchemaError("thresholds.requiredBlindReviewers must be a positive integer")
    return AudioAcceptancePolicy(tuple(cases), float(similarity), float(peak), clipped, reviewers)


def event_to_payload(event: OperationEvent) -> dict[str, Any]:
    return {
        "schema": EVENT_SCHEMA,
        "eventId": event.event_id,
        "sequence": event.sequence,
        "bookSlug": event.book_slug,
        "chapter": event.chapter,
        "occurredAt": event.occurred_at,
        "actor": event.actor,
        "eventType": event.event_type,
        "fromState": event.from_state.value if event.from_state else None,
        "toState": event.to_state.value,
        "reason": event.reason,
        "idempotencyKey": event.idempotency_key,
        "intentHash": event.intent_hash,
        "previousEventHash": event.previous_event_hash,
        "eventHash": event.event_hash,
        "evidence": event.evidence,
    }


def calculate_event_hash(event: OperationEvent) -> str:
    payload = event_to_payload(event)
    payload.pop("eventHash")
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_event(payload: dict[str, Any]) -> OperationEvent:
    if payload.get("schema") != EVENT_SCHEMA:
        raise SchemaError(f"Unsupported event schema: {payload.get('schema')!r}")
    from_value = payload.get("fromState")
    try:
        from_state = LifecycleState(from_value) if from_value is not None else None
        to_state = LifecycleState(payload.get("toState"))
    except ValueError as exc:
        raise SchemaError("Event contains an invalid lifecycle state") from exc
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        raise SchemaError("event.evidence must be an object")
    chapter = payload.get("chapter")
    sequence = payload.get("sequence")
    if not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1:
        raise SchemaError("event.chapter must be a positive integer")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise SchemaError("event.sequence must be a positive integer")
    previous_event_hash = payload.get("previousEventHash")
    if previous_event_hash is not None and (
        not isinstance(previous_event_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", previous_event_hash)
    ):
        raise SchemaError("event.previousEventHash must be null or a SHA-256 digest")
    event_hash = _string(payload, "eventHash")
    if not re.fullmatch(r"[0-9a-f]{64}", event_hash):
        raise SchemaError("event.eventHash must be a SHA-256 digest")
    return OperationEvent(
        event_id=_string(payload, "eventId"),
        sequence=sequence,
        book_slug=_string(payload, "bookSlug"),
        chapter=chapter,
        occurred_at=_string(payload, "occurredAt"),
        actor=_string(payload, "actor"),
        event_type=_string(payload, "eventType"),
        from_state=from_state,
        to_state=to_state,
        reason=_string(payload, "reason"),
        idempotency_key=_string(payload, "idempotencyKey"),
        intent_hash=_string(payload, "intentHash"),
        previous_event_hash=previous_event_hash,
        event_hash=event_hash,
        evidence=dict(evidence),
    )
