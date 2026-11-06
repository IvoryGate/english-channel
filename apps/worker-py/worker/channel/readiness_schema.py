"""Small, explicit evidence-date contracts, separate from filesystem reads."""
from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Any


def aware_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Expected an ISO-8601 timestamp with a timezone offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Expected an ISO-8601 timestamp with a timezone offset")
    return parsed.astimezone(timezone.utc)


def evidence_date(value: Any) -> tuple[str, date]:
    """Keep date-only precision; never invent a midnight observation time."""
    if not isinstance(value, str):
        raise ValueError("Evidence date must be a string")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "date", date.fromisoformat(value)
    parsed = aware_timestamp(value)
    return "timestamp", parsed.date()


def plan_created_on(name: str) -> str | None:
    candidate = name[:10]
    try:
        precision, _ = evidence_date(candidate)
    except ValueError:
        return None
    return candidate if precision == "date" else None
