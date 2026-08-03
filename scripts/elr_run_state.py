from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_SCHEMA = "elr-production-run-v1"
TERMINAL_STATUSES = {"DONE", "FAILED", "CANCELLED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RunStateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, Any] | None:
        if not self.path.is_file():
            return None
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = dict(payload)
        data.setdefault("schema", STATE_SCHEMA)
        data["updatedAt"] = utc_now()
        data["heartbeatAt"] = data["updatedAt"]
        temporary = self.path.with_suffix(self.path.suffix + f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        # Windows readers, virus scanners, and file indexers can briefly hold the
        # destination open.  Treat that as transient so a status heartbeat can
        # never abort an otherwise successful multi-hour render.
        for attempt in range(10):
            try:
                os.replace(temporary, self.path)
                break
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(min(0.05 * (2**attempt), 0.5))
        return data

    def update(self, **changes: Any) -> dict[str, Any]:
        current = self.read() or {}
        current.update(changes)
        return self.write(current)

    def heartbeat(self, detail: str = "") -> dict[str, Any]:
        changes: dict[str, Any] = {}
        if detail:
            changes["detail"] = detail[-1000:]
        return self.update(**changes)


def state_path(repo_root: Path, episode_id: str) -> Path:
    return repo_root / "logs" / "elr_runs" / f"{episode_id}.json"
