"""Read-only evidence access. Deliberately independent of the migrating repo."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .readiness_types import DatabaseEvidence, JsonEvidence


COUNT_TABLES = (
    "content_items", "publications", "remote_captures", "analytics_captures",
    "analytics_observations", "packaging_experiments", "experiment_reviews",
    "native_experiment_results",
)


class ReadinessRepository:
    def __init__(self, root: Path, database: Path, release_policy: Path) -> None:
        self.root = root.resolve()
        self.database = database.resolve()
        self.release_policy = release_policy.resolve()

    def source(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def json(self, path: Path) -> JsonEvidence:
        source = self.source(path)
        try:
            # Reports intentionally omit text, credentials, and malformed input bytes.
            if path.stat().st_size > 2_000_000:
                return JsonEvidence(source, "too_large")
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(payload, dict):
                return JsonEvidence(source, "invalid_object")
            return JsonEvidence(source, "available", payload)
        except FileNotFoundError:
            return JsonEvidence(source, "missing")
        except (UnicodeError, json.JSONDecodeError):
            return JsonEvidence(source, "invalid_json")
        except OSError:
            return JsonEvidence(source, "unreadable")

    def community(self) -> tuple[JsonEvidence, ...]:
        directory = self.root / "workspace" / "community"
        try:
            paths = sorted(directory.glob("*.json"))
        except OSError:
            return (JsonEvidence(self.source(directory), "unreadable"),)
        operations = directory / "operations.json"
        if operations not in paths:
            paths.insert(0, operations)
        return tuple(self.json(path) for path in paths)

    def plans(self) -> tuple[str, ...] | None:
        directory = self.root / "docs" / "exec-plans" / "active"
        try:
            if not directory.is_dir():
                return None
            return tuple(self.source(path) for path in sorted(directory.glob("*.md")))
        except OSError:
            return None

    def known_migrations(self) -> tuple[tuple[int, str], ...]:
        paths = Path(__file__).with_name("migrations").glob("[0-9][0-9][0-9][0-9]_*.sql")
        return tuple((int(path.name[:4]), path.name) for path in sorted(paths))

    def database_snapshot(self) -> DatabaseEvidence:
        source = self.source(self.database)
        try:
            if not self.database.is_file():
                return DatabaseEvidence(source, "missing")
            with self.database.open("rb") as stream:
                header = stream.read(20)
            # Even mode=ro may create absent WAL coordination files. Refuse an
            # idle WAL database rather than changing its filesystem footprint
            # or pretending immutable=1 sees a concurrently written WAL.
            if header.startswith(b"SQLite format 3\x00") and 2 in header[18:20]:
                if not all(Path(str(self.database) + suffix).is_file()
                           for suffix in ("-wal", "-shm")):
                    return DatabaseEvidence(source, "wal_snapshot_unavailable")
            # mode=ro prevents accidental creation and writes; do not use immutable=1,
            # which would ignore a live WAL. No migrations, PRAGMA journal changes,
            # seeds, or parent-directory creation belong on this path.
            connection = sqlite3.connect(self.database.as_uri() + "?mode=ro", uri=True)
            try:
                connection.row_factory = sqlite3.Row
                connection.execute("PRAGMA query_only = ON")
                connection.execute("BEGIN")
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                counts = {name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                          if name in tables else None for name in COUNT_TABLES}
                unavailable = [name for name in COUNT_TABLES if name not in tables]
                migrations = ()
                captures = ()
                try:
                    migrations = tuple((int(row[0]), str(row[1])) for row in connection.execute(
                        "SELECT version, name FROM schema_migrations ORDER BY version"
                    ))
                except (sqlite3.Error, ValueError, TypeError):
                    unavailable.append("schema_migrations")
                if "remote_captures" in tables:
                    try:
                        captures = tuple(dict(row) for row in connection.execute(
                            "SELECT capture_id, provider, scope, collected_at, item_count "
                            "FROM remote_captures ORDER BY collected_at DESC LIMIT 20"
                        ))
                    except sqlite3.Error:
                        unavailable.append("remote_capture_fields")
                return DatabaseEvidence(source, "available", counts, migrations, captures,
                                        tuple(unavailable))
            finally:
                connection.close()
        except (OSError, sqlite3.Error):
            return DatabaseEvidence(source, "unreadable_or_invalid")
