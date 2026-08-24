from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..schema import canonical_json
from ..types import LegacySource


class LegacyLedgerProvider:
    """Read-only adapter for local legacy JSON and JSONL ledgers."""

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def read_json(self, path: Path, *, source_system: str, collected_at: str) -> LegacySource:
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Legacy ledger does not exist: {resolved}")
        with resolved.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"Legacy ledger must contain a JSON object: {resolved}")
        return LegacySource(
            source_system=source_system,
            locator=str(resolved),
            sha256=self._file_sha256(resolved),
            collected_at=collected_at,
            payload=payload,
        )

    def read_classics(self, root: Path, *, collected_at: str) -> LegacySource:
        resolved = root.resolve()
        if not resolved.is_dir():
            raise FileNotFoundError(f"Classics operations root does not exist: {resolved}")
        streams: list[dict[str, Any]] = []
        manifest: list[dict[str, str]] = []
        for path in sorted(resolved.glob("*/chapter_*/events.jsonl")):
            events: list[dict[str, Any]] = []
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError(f"Event line {line_number} is not an object: {path}")
                events.append(payload)
            if not events:
                continue
            relative = path.relative_to(resolved).as_posix()
            streams.append({"locator": f"{resolved}::{relative}", "events": events})
            manifest.append({"path": relative, "sha256": self._file_sha256(path)})
        directory_hash = hashlib.sha256(canonical_json(manifest).encode("utf-8")).hexdigest()
        return LegacySource(
            source_system="classics_events_v1",
            locator=str(resolved),
            sha256=directory_hash,
            collected_at=collected_at,
            payload=streams,
        )

    def read_bytes(self, path: Path) -> tuple[Path, bytes, str]:
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Source capture does not exist: {resolved}")
        value = resolved.read_bytes()
        return resolved, value, hashlib.sha256(value).hexdigest()
