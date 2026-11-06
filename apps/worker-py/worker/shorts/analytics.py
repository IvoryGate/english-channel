from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .workspace import atomic_write_json, operation_root


ANALYTICS_SCHEMA = "elr-shorts-analytics-snapshot-v2"
LEGACY_ANALYTICS_SCHEMA = "elr-shorts-analytics-snapshot-v1"
AVAILABILITY_STATES = {"observed", "missing", "not_returned", "unsupported", "legacy_unverified"}
NUMERIC_FIELDS = (
    "views",
    "engaged_views",
    "average_percentage_viewed",
    "subscribers_gained",
    "likes",
    "comments",
    "shares",
    "long_form_views",
)


def _parse_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid analytics date {value!r}; expected YYYY-MM-DD") from exc


def _number(value: Any, field: str) -> float | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric, not boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return number


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    short_id = str(row.get("short_id") or row.get("shortId") or "").strip()
    if not short_id:
        raise ValueError("Analytics row is missing short_id")
    observed_on = _parse_date(str(row.get("date") or row.get("observedOn") or ""))
    normalized: dict[str, Any] = {"shortId": short_id, "observedOn": observed_on}
    supplied_states = row.get("metricAvailability", {})
    if not isinstance(supplied_states, dict):
        raise ValueError("metricAvailability must be an object")
    states = {}
    for field in NUMERIC_FIELDS:
        value = _number(row.get(field), field)
        state = supplied_states.get(field, "observed" if value is not None else "missing")
        if not isinstance(state, str) or state not in AVAILABILITY_STATES:
            raise ValueError(f"Invalid availability state for {field}")
        if (state == "observed") != (value is not None):
            raise ValueError(f"{field} value and availability disagree")
        normalized[field] = value
        states[field] = state
    normalized["metricAvailability"] = states
    if (normalized["engaged_views"] is not None and normalized["views"] is not None
            and normalized["engaged_views"] > normalized["views"]):
        raise ValueError(f"{short_id}: engaged_views cannot exceed views")
    if normalized["average_percentage_viewed"] is not None and normalized["average_percentage_viewed"] > 500:
        raise ValueError(f"{short_id}: average_percentage_viewed is implausibly high")
    return normalized


def read_rows(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.casefold()
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = [normalize_row(dict(row)) for row in csv.DictReader(stream)]
    elif suffix == ".json":
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("schema") == LEGACY_ANALYTICS_SCHEMA:
            raise ValueError("V1 snapshots lost missing-value provenance; reimport the original source")
        source_rows = raw.get("rows") if isinstance(raw, dict) else raw
        if not isinstance(source_rows, list):
            raise ValueError("Analytics JSON must be a list or an object with rows")
        rows = [normalize_row(dict(row)) for row in source_rows]
    else:
        raise ValueError("Analytics input must be .csv or .json")
    if not rows:
        raise ValueError("Analytics input has no rows")
    unique = {(row["shortId"], row["observedOn"]) for row in rows}
    if len(unique) != len(rows):
        raise ValueError("Analytics input contains duplicate short_id/date rows")
    return rows


def store_snapshot(repo_root: Path, rows: list[dict[str, Any]], *, source: str,
                   source_sha256: str | None = None,
                   window: dict[str, str] | None = None) -> Path:
    """Keep imports idempotent; give fresh collections their own capture time."""
    rows = [normalize_row(row) for row in rows]
    if not rows:
        raise ValueError("Analytics snapshot has no rows")
    payload = {
        "schema": ANALYTICS_SCHEMA,
        "snapshotDate": max(str(row["observedOn"]) for row in rows),
        "sourceFile": source,
        "sourceSha256": source_sha256,
        "window": window,
        "rows": sorted(rows, key=lambda item: (str(item["shortId"]), str(item["observedOn"]))),
    }
    imported_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    # A source-file hash identifies a repeat import. A live collection is a
    # new event even when values recover to an earlier identical response.
    if source_sha256 is None:
        payload["capturedAt"] = imported_at
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()
    path = operation_root(repo_root) / "analytics" / f"{payload['snapshotDate']}.v2-{digest}.json"
    if not path.exists():
        payload["importedAt"] = imported_at
        atomic_write_json(path, payload)
    return path


def ingest_snapshot(repo_root: Path, input_path: Path) -> Path:
    return store_snapshot(repo_root, read_rows(input_path), source=input_path.name,
                          source_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest())


def load_latest_metrics(repo_root: Path, cutoff: str | None = None) -> dict[str, dict[str, Any]]:
    analytics_dir = repo_root / "workspace" / "shorts" / "ops" / "analytics"
    if not analytics_dir.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    priorities: dict[str, tuple[str, int, str, str]] = {}
    for path in sorted(analytics_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema = payload.get("schema")
        if schema not in {ANALYTICS_SCHEMA, LEGACY_ANALYTICS_SCHEMA}:
            continue
        for row in payload.get("rows", []):
            observed = _parse_date(str(row.get("observedOn", "")))
            if cutoff and observed > cutoff:
                continue
            short_id = str(row.get("shortId", ""))
            priority = (observed, int(schema == ANALYTICS_SCHEMA), str(payload.get("importedAt", "")), path.name)
            if short_id and (short_id not in latest or priority > priorities[short_id]):
                if schema == LEGACY_ANALYTICS_SCHEMA:
                    # V1 zero may mean absent or observed. Never reverse-engineer it.
                    normalized = normalize_row({"shortId": short_id, "observedOn": observed,
                        "metricAvailability": {field: "legacy_unverified" for field in NUMERIC_FIELDS}})
                    normalized["legacyValues"] = {field: row.get(field) for field in NUMERIC_FIELDS}
                else:
                    normalized = normalize_row(row)
                normalized["sourceSchema"] = schema
                normalized["sourceSnapshot"] = path.name
                normalized["window"] = payload.get("window")
                latest[short_id] = normalized
                priorities[short_id] = priority
    return latest


def derived_metrics(row: dict[str, Any]) -> dict[str, float | None]:
    values = {field: _number(row.get(field), field) for field in NUMERIC_FIELDS}
    views, engaged = values["views"], values["engaged_views"]
    interaction_values = [values[field] for field in ("likes", "comments", "shares")]
    interactions = sum(interaction_values) if all(value is not None for value in interaction_values) else None

    def rate(numerator: float | None, denominator: float | None, factor: int = 1) -> float | None:
        if numerator is None or denominator is None or denominator <= 0:
            return None
        result = numerator / denominator * factor
        return result if math.isfinite(result) else None

    return {
        "engaged_view_rate": rate(engaged, views),
        "average_percentage_viewed": values["average_percentage_viewed"],
        "subscribers_per_1000_engaged": rate(values["subscribers_gained"], engaged, 1000),
        "long_form_views_per_1000_engaged": rate(values["long_form_views"], engaged, 1000),
        "interactions_per_1000_engaged": rate(interactions, engaged, 1000),
    }


def median_metrics(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    derived = [derived_metrics(row) for row in rows]
    if not derived:
        return {}
    return {
        key: (statistics.median(item[key] for item in derived)
              if all(item[key] is not None for item in derived) else None)
        for key in derived[0]
    }
