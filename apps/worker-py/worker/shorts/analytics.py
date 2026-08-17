from __future__ import annotations

import csv
import json
import statistics
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .workspace import atomic_write_json, operation_root


ANALYTICS_SCHEMA = "elr-shorts-analytics-snapshot-v1"
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


def _number(value: Any, field: str) -> float:
    if value in (None, ""):
        return 0.0
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {field}: {value!r}") from exc
    if number < 0:
        raise ValueError(f"{field} cannot be negative")
    return number


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    short_id = str(row.get("short_id") or row.get("shortId") or "").strip()
    if not short_id:
        raise ValueError("Analytics row is missing short_id")
    observed_on = _parse_date(str(row.get("date") or row.get("observedOn") or ""))
    normalized: dict[str, Any] = {"shortId": short_id, "observedOn": observed_on}
    for field in NUMERIC_FIELDS:
        normalized[field] = _number(row.get(field), field)
    if normalized["engaged_views"] > normalized["views"] and normalized["views"] > 0:
        raise ValueError(f"{short_id}: engaged_views cannot exceed views")
    if normalized["average_percentage_viewed"] > 500:
        raise ValueError(f"{short_id}: average_percentage_viewed is implausibly high")
    return normalized


def read_rows(input_path: Path) -> list[dict[str, Any]]:
    suffix = input_path.suffix.casefold()
    if suffix == ".csv":
        with input_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = [normalize_row(dict(row)) for row in csv.DictReader(stream)]
    elif suffix == ".json":
        raw = json.loads(input_path.read_text(encoding="utf-8"))
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


def ingest_snapshot(repo_root: Path, input_path: Path) -> Path:
    rows = read_rows(input_path)
    snapshot_date = max(str(row["observedOn"]) for row in rows)
    path = operation_root(repo_root) / "analytics" / f"{snapshot_date}.json"
    payload = {
        "schema": ANALYTICS_SCHEMA,
        "snapshotDate": snapshot_date,
        "importedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sourceFile": input_path.name,
        "rows": sorted(rows, key=lambda item: (str(item["shortId"]), str(item["observedOn"]))),
    }
    atomic_write_json(path, payload)
    return path


def load_latest_metrics(repo_root: Path, cutoff: str | None = None) -> dict[str, dict[str, Any]]:
    analytics_dir = operation_root(repo_root) / "analytics"
    if not analytics_dir.exists():
        return {}
    latest: dict[str, dict[str, Any]] = {}
    for path in sorted(analytics_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema") != ANALYTICS_SCHEMA:
            continue
        for row in payload.get("rows", []):
            observed = str(row.get("observedOn", ""))
            if cutoff and observed > cutoff:
                continue
            short_id = str(row.get("shortId", ""))
            current = latest.get(short_id)
            if short_id and (current is None or observed > str(current["observedOn"])):
                latest[short_id] = dict(row)
    return latest


def derived_metrics(row: dict[str, Any]) -> dict[str, float]:
    views = float(row.get("views", 0.0))
    engaged = float(row.get("engaged_views", 0.0))
    interactions = sum(float(row.get(field, 0.0)) for field in ("likes", "comments", "shares"))
    return {
        "engaged_view_rate": engaged / views if views else 0.0,
        "average_percentage_viewed": float(row.get("average_percentage_viewed", 0.0)),
        "subscribers_per_1000_engaged": float(row.get("subscribers_gained", 0.0)) * 1000 / engaged
        if engaged
        else 0.0,
        "long_form_views_per_1000_engaged": float(row.get("long_form_views", 0.0)) * 1000 / engaged
        if engaged
        else 0.0,
        "interactions_per_1000_engaged": interactions * 1000 / engaged if engaged else 0.0,
    }


def median_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    derived = [derived_metrics(row) for row in rows]
    if not derived:
        return {}
    return {
        key: statistics.median(item[key] for item in derived)
        for key in derived[0]
    }
