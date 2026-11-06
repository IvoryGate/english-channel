"""Values for local diagnostics; none of these grant release authority."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Finding:
    code: str
    source: str
    detail: str


@dataclass(frozen=True)
class JsonEvidence:
    source: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatabaseEvidence:
    source: str
    status: str
    counts: dict[str, int | None] = field(default_factory=dict)
    migrations: tuple[tuple[int, str], ...] = ()
    captures: tuple[dict[str, Any], ...] = ()
    unavailable: tuple[str, ...] = ()
