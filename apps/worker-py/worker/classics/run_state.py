from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import atomic_write_json, read_json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RunStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        return read_json(self.path)

    def write(self, payload: dict[str, Any]) -> dict[str, Any]:
        value = dict(payload)
        value["updatedAt"] = utc_now()
        atomic_write_json(self.path, value)
        return value

    def update(self, **changes: Any) -> dict[str, Any]:
        current = self.read() or {}
        current.update(changes)
        return self.write(current)
