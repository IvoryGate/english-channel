from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

from .schema import canonical_content_id, canonical_json, payload_sha256
from .types import (
    ChannelPolicy,
    CollisionRecord,
    ImportRequest,
    ImportSummary,
    InventorySummary,
    NormalizedIdentityRecord,
    ReconciliationReport,
    ReleaseReservation,
    RemoteInventoryCapture,
    ResourceLease,
)


class RepositoryError(RuntimeError):
    pass


class PolicyMismatchError(RepositoryError):
    pass


class SqliteChannelRepository:
    def __init__(self, database: Path, migrations: Path | None = None) -> None:
        self.database = database
        self.migrations = migrations or Path(__file__).with_name("migrations")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        try:
            yield connection
        finally:
            connection.close()

    def migrate(self, applied_at: str) -> int:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            applied = {
                int(row["version"])
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for path in sorted(self.migrations.glob("[0-9][0-9][0-9][0-9]_*.sql")):
                version = int(path.name.split("_", 1)[0])
                if version in applied:
                    continue
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    statement = ""
                    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
                        statement += line
                        if sqlite3.complete_statement(statement):
                            connection.execute(statement)
                            statement = ""
                    if statement.strip():
                        raise RepositoryError(f"Migration has an incomplete statement: {path.name}")
                    connection.execute(
                        "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                        (version, path.name, applied_at),
                    )
                    connection.commit()
                except BaseException as exc:
                    connection.rollback()
                    if isinstance(exc, RepositoryError):
                        raise
                    if not isinstance(exc, sqlite3.Error):
                        raise
                    raise RepositoryError(f"Migration failed: {path.name}: {exc}") from exc
            row = connection.execute("SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations").fetchone()
            return int(row["version"])

    def seed_policy(self, policy: ChannelPolicy, now: str) -> None:
        with self._connect() as connection:
            try:
                existing_channels = connection.execute(
                    "SELECT channel_id, public_name FROM channels"
                ).fetchall()
                if existing_channels and any(row["channel_id"] != policy.channel_id for row in existing_channels):
                    raise PolicyMismatchError("Database already belongs to a different channel")
                connection.execute(
                    """
                    INSERT INTO channels(channel_id, public_name, created_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(channel_id) DO UPDATE SET public_name = excluded.public_name
                    """,
                    (policy.channel_id, policy.public_name, now),
                )
                for item in policy.product_lines:
                    row = connection.execute(
                        "SELECT channel_id FROM product_lines WHERE product_line_id = ?",
                        (item.product_line_id,),
                    ).fetchone()
                    if row and row["channel_id"] != policy.channel_id:
                        raise PolicyMismatchError(
                            f"Product line {item.product_line_id} belongs to a different channel"
                        )
                    connection.execute(
                        """
                        INSERT INTO product_lines(product_line_id, channel_id, name, created_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(product_line_id) DO UPDATE SET name = excluded.name
                        """,
                        (item.product_line_id, policy.channel_id, item.name, now),
                    )
                for item in policy.series:
                    row = connection.execute(
                        "SELECT channel_id, product_line_id FROM series WHERE series_id = ?",
                        (item.series_id,),
                    ).fetchone()
                    if row and (
                        row["channel_id"] != policy.channel_id
                        or row["product_line_id"] != item.product_line_id
                    ):
                        raise PolicyMismatchError(
                            f"Series {item.series_id} ownership differs from tracked policy"
                        )
                    connection.execute(
                        """
                        INSERT INTO series(series_id, channel_id, product_line_id, name, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(series_id) DO UPDATE SET name = excluded.name
                        """,
                        (item.series_id, policy.channel_id, item.product_line_id, item.name, now),
                    )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise


    @staticmethod
    def _normalized_payload(record: NormalizedIdentityRecord) -> dict[str, object | None]:
        return {
            "sourceSystem": record.source_system,
            "sourceItemId": record.source_item_id,
            "sourceLocator": record.source_locator,
            "productLineId": record.product_line_id,
            "seriesId": record.series_id,
            "localItemId": record.local_item_id,
            "title": record.title,
            "sourceState": record.source_state,
            "mediaSha256": record.media_sha256,
            "youtubeVideoId": record.youtube_video_id,
            "publicationStatus": record.publication_status,
        }

    @staticmethod
    def _collision_candidates(
        connection: sqlite3.Connection,
        record: NormalizedIdentityRecord,
        content_id: str,
    ) -> list[tuple[str, str, str | None, str]]:
        collisions: list[tuple[str, str, str | None, str]] = []
        alias = connection.execute(
            """
            SELECT content_id FROM source_aliases
            WHERE source_system = ? AND source_item_id = ?
            """,
            (record.source_system, record.source_item_id),
        ).fetchone()
        if alias and alias["content_id"] != content_id:
            collisions.append(
                (
                    "source_alias",
                    f"{record.source_system}:{record.source_item_id}",
                    str(alias["content_id"]),
                    "Source alias already resolves to another canonical content item",
                )
            )
        content = connection.execute(
            "SELECT product_line_id, series_id, local_item_id FROM content_items WHERE content_id = ?",
            (content_id,),
        ).fetchone()
        if content and (
            content["product_line_id"] != record.product_line_id
            or content["series_id"] != record.series_id
            or content["local_item_id"] != record.local_item_id
        ):
            collisions.append(
                (
                    "canonical_content",
                    content_id,
                    content_id,
                    "Canonical content identity attributes disagree with stored state",
                )
            )
        if record.media_sha256:
            artifact = connection.execute(
                "SELECT content_id FROM artifacts WHERE sha256 = ?",
                (record.media_sha256,),
            ).fetchone()
            if artifact and artifact["content_id"] != content_id:
                collisions.append(
                    (
                        "artifact_fingerprint",
                        record.media_sha256,
                        str(artifact["content_id"]),
                        "Media fingerprint already resolves to another canonical content item",
                    )
                )
        if record.youtube_video_id:
            publication = connection.execute(
                "SELECT content_id FROM publications WHERE provider = 'youtube' AND remote_id = ?",
                (record.youtube_video_id,),
            ).fetchone()
            if publication and publication["content_id"] != content_id:
                collisions.append(
                    (
                        "remote_video_id",
                        record.youtube_video_id,
                        str(publication["content_id"]),
                        "YouTube video ID already resolves to another canonical content item",
                    )
                )
        return collisions

    @staticmethod
    def _apply_record(
        connection: sqlite3.Connection,
        policy: ChannelPolicy,
        record: NormalizedIdentityRecord,
        content_id: str,
        now: str,
    ) -> str:
        existing = connection.execute(
            "SELECT title FROM content_items WHERE content_id = ?", (content_id,)
        ).fetchone()
        changed = False
        if existing is None:
            connection.execute(
                """
                INSERT INTO content_items(
                    content_id, channel_id, product_line_id, series_id,
                    local_item_id, title, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    policy.channel_id,
                    record.product_line_id,
                    record.series_id,
                    record.local_item_id,
                    record.title,
                    now,
                    now,
                ),
            )
            outcome = "inserted"
        else:
            outcome = "unchanged"
            if record.title and record.title != existing["title"]:
                connection.execute(
                    "UPDATE content_items SET title = ?, updated_at = ? WHERE content_id = ?",
                    (record.title, now, content_id),
                )
                changed = True
        alias = connection.execute(
            """
            SELECT source_locator, last_source_state FROM source_aliases
            WHERE source_system = ? AND source_item_id = ?
            """,
            (record.source_system, record.source_item_id),
        ).fetchone()
        if alias is None:
            connection.execute(
                """
                INSERT INTO source_aliases(
                    source_system, source_item_id, content_id, source_locator,
                    last_source_state, first_seen_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.source_system,
                    record.source_item_id,
                    content_id,
                    record.source_locator,
                    record.source_state,
                    now,
                    now,
                ),
            )
            changed = existing is not None
        else:
            if (
                alias["source_locator"] != record.source_locator
                or alias["last_source_state"] != record.source_state
            ):
                changed = True
            connection.execute(
                """
                UPDATE source_aliases
                SET source_locator = ?, last_source_state = ?, last_seen_at = ?
                WHERE source_system = ? AND source_item_id = ?
                """,
                (
                    record.source_locator,
                    record.source_state,
                    now,
                    record.source_system,
                    record.source_item_id,
                ),
            )
        if record.media_sha256:
            result = connection.execute(
                """
                INSERT OR IGNORE INTO artifacts(
                    artifact_id, content_id, kind, sha256, source_locator, created_at
                ) VALUES (?, ?, 'video', ?, ?, ?)
                """,
                (
                    f"artifact:sha256:{record.media_sha256}",
                    content_id,
                    record.media_sha256,
                    record.source_locator,
                    now,
                ),
            )
            changed = changed or result.rowcount > 0
        if record.youtube_video_id:
            result = connection.execute(
                """
                INSERT OR IGNORE INTO publications(
                    publication_id, content_id, provider, remote_id, created_at
                ) VALUES (?, ?, 'youtube', ?, ?)
                """,
                (
                    f"youtube:{record.youtube_video_id}",
                    content_id,
                    record.youtube_video_id,
                    now,
                ),
            )
            changed = changed or result.rowcount > 0
        if outcome == "unchanged" and changed:
            outcome = "updated"
        return outcome

    def import_identities(self, policy: ChannelPolicy, request: ImportRequest, now: str) -> ImportSummary:
        import_run_id = f"import:{uuid.uuid4()}"
        counts = {"inserted": 0, "updated": 0, "unchanged": 0, "collision": 0}
        collision_count = 0
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO import_runs(
                        import_run_id, source_system, source_locator, source_sha256,
                        collected_at, started_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        import_run_id,
                        request.source.source_system,
                        request.source.locator,
                        request.source.sha256,
                        request.source.collected_at,
                        now,
                    ),
                )
                for record in request.records:
                    content_id = canonical_content_id(record.series_id, record.local_item_id)
                    collisions = self._collision_candidates(connection, record, content_id)
                    outcome = "collision" if collisions else self._apply_record(
                        connection, policy, record, content_id, now
                    )
                    normalized = self._normalized_payload(record)
                    cursor = connection.execute(
                        """
                        INSERT INTO import_records(
                            import_run_id, source_item_id, source_locator,
                            incoming_content_id, normalized_payload, raw_payload,
                            raw_payload_sha256, outcome, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            import_run_id,
                            record.source_item_id,
                            record.source_locator,
                            content_id,
                            canonical_json(normalized),
                            canonical_json(record.raw_payload),
                            payload_sha256(record.raw_payload),
                            outcome,
                            now,
                        ),
                    )
                    counts[outcome] += 1
                    for kind, identity_key, existing_content_id, detail in collisions:
                        connection.execute(
                            """
                            INSERT INTO identity_collisions(
                                import_run_id, import_record_id, source_system,
                                source_item_id, kind, identity_key,
                                existing_content_id, incoming_content_id, detail,
                                created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                import_run_id,
                                cursor.lastrowid,
                                record.source_system,
                                record.source_item_id,
                                kind,
                                identity_key,
                                existing_content_id,
                                content_id,
                                detail,
                                now,
                            ),
                        )
                        collision_count += 1
                connection.execute(
                    """
                    UPDATE import_runs SET
                        completed_at = ?, total_count = ?, inserted_count = ?,
                        updated_count = ?, unchanged_count = ?, collided_count = ?,
                        collision_count = ?
                    WHERE import_run_id = ?
                    """,
                    (
                        now,
                        len(request.records),
                        counts["inserted"],
                        counts["updated"],
                        counts["unchanged"],
                        counts["collision"],
                        collision_count,
                        import_run_id,
                    ),
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        return ImportSummary(
            import_run_id=import_run_id,
            source_system=request.source.source_system,
            source_locator=request.source.locator,
            source_sha256=request.source.sha256,
            total=len(request.records),
            inserted=counts["inserted"],
            updated=counts["updated"],
            unchanged=counts["unchanged"],
            collided=counts["collision"],
            collision_count=collision_count,
        )

    def inventory(self) -> InventorySummary:
        if not self.database.is_file():
            return InventorySummary(self.database, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {})
        try:
            with self._connect() as connection:
                tables = {
                    str(row["name"])
                    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                }
                if "schema_migrations" not in tables:
                    return InventorySummary(self.database, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, {})
                version = int(
                    connection.execute(
                        "SELECT COALESCE(MAX(version), 0) AS value FROM schema_migrations"
                    ).fetchone()["value"]
                )
                if "content_items" not in tables:
                    return InventorySummary(self.database, version, 0, 0, 0, 0, 0, 0, 0, 0, 0, {})

                def count(table: str, where: str = "") -> int:
                    return int(
                        connection.execute(
                            f"SELECT COUNT(*) AS value FROM {table} {where}"
                        ).fetchone()["value"]
                    )

                by_product = {
                    str(row["product_line_id"]): int(row["value"])
                    for row in connection.execute(
                        """
                        SELECT product_line_id, COUNT(*) AS value
                        FROM content_items GROUP BY product_line_id ORDER BY product_line_id
                        """
                    )
                }
                return InventorySummary(
                    database=self.database,
                    schema_version=version,
                    channel_count=count("channels"),
                    product_line_count=count("product_lines"),
                    series_count=count("series"),
                    content_item_count=count("content_items"),
                    source_alias_count=count("source_aliases"),
                    artifact_count=count("artifacts"),
                    publication_count=count("publications"),
                    import_run_count=count("import_runs"),
                    unresolved_collision_count=count(
                        "identity_collisions", "WHERE resolved_at IS NULL"
                    ),
                    content_by_product_line=by_product,
                )
        except sqlite3.Error as exc:
            raise RepositoryError(f"Cannot inspect channel database {self.database}: {exc}") from exc

    def collisions(self, *, unresolved_only: bool = True) -> tuple[CollisionRecord, ...]:
        if not self.database.is_file():
            return ()
        where = "WHERE resolved_at IS NULL" if unresolved_only else ""
        try:
            with self._connect() as connection:
                tables = {
                    str(row["name"])
                    for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
                }
                if "identity_collisions" not in tables:
                    return ()
                rows = connection.execute(
                    f"""
                    SELECT collision_id, import_run_id, source_system, source_item_id,
                           kind, identity_key, existing_content_id,
                           incoming_content_id, detail, created_at, resolved_at
                    FROM identity_collisions {where} ORDER BY collision_id
                    """
                ).fetchall()
                return tuple(
                    CollisionRecord(
                        collision_id=int(row["collision_id"]),
                        import_run_id=str(row["import_run_id"]),
                        source_system=str(row["source_system"]),
                        source_item_id=str(row["source_item_id"]),
                        kind=str(row["kind"]),
                        identity_key=str(row["identity_key"]),
                        existing_content_id=str(row["existing_content_id"])
                        if row["existing_content_id"] is not None
                        else None,
                        incoming_content_id=str(row["incoming_content_id"]),
                        detail=str(row["detail"]),
                        created_at=str(row["created_at"]),
                        resolved_at=str(row["resolved_at"])
                        if row["resolved_at"] is not None
                        else None,
                    )
                    for row in rows
                )
        except sqlite3.Error as exc:
            raise RepositoryError(f"Cannot read channel collisions {self.database}: {exc}") from exc

    def import_record_payloads(self, import_run_id: str) -> tuple[dict[str, object], ...]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT source_item_id, raw_payload, raw_payload_sha256, outcome
                FROM import_records WHERE import_run_id = ? ORDER BY import_record_id
                """,
                (import_run_id,),
            ).fetchall()
            return tuple(
                {
                    "sourceItemId": str(row["source_item_id"]),
                    "rawPayload": json.loads(row["raw_payload"]),
                    "rawPayloadSha256": str(row["raw_payload_sha256"]),
                    "outcome": str(row["outcome"]),
                }
                for row in rows
            )

    @staticmethod
    def _lease(row: sqlite3.Row) -> ResourceLease:
        return ResourceLease(
            lease_id=str(row["lease_id"]),
            resource_id=str(row["resource_id"]),
            owner_id=str(row["owner_id"]),
            owner_pid=int(row["owner_pid"]),
            parent_pid=int(row["parent_pid"]),
            label=str(row["label"]),
            intent_hash=str(row["intent_hash"]),
            priority=int(row["priority"]),
            acquired_at=str(row["acquired_at"]),
            heartbeat_at=str(row["heartbeat_at"]),
            expires_at=str(row["expires_at"]),
            released_at=str(row["released_at"]) if row["released_at"] else None,
            release_reason=str(row["release_reason"]) if row["release_reason"] else None,
        )

    def active_lease(self, resource_id: str) -> ResourceLease | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM resource_leases WHERE resource_id = ? AND released_at IS NULL",
                (resource_id,),
            ).fetchone()
            return self._lease(row) if row else None

    def try_acquire_lease(self, lease: ResourceLease) -> ResourceLease | None:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                active = connection.execute(
                    "SELECT * FROM resource_leases WHERE resource_id = ? AND released_at IS NULL",
                    (lease.resource_id,),
                ).fetchone()
                if active:
                    connection.rollback()
                    return self._lease(active)
                connection.execute(
                    """
                    INSERT INTO resource_leases(
                        lease_id, resource_id, owner_id, owner_pid, parent_pid,
                        label, intent_hash, priority, acquired_at, heartbeat_at,
                        expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lease.lease_id,
                        lease.resource_id,
                        lease.owner_id,
                        lease.owner_pid,
                        lease.parent_pid,
                        lease.label,
                        lease.intent_hash,
                        lease.priority,
                        lease.acquired_at,
                        lease.heartbeat_at,
                        lease.expires_at,
                    ),
                )
                connection.commit()
                return None
            except BaseException:
                connection.rollback()
                raise

    def heartbeat_lease(self, lease_id: str, owner_id: str, heartbeat_at: str, expires_at: str) -> ResourceLease:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE resource_leases SET heartbeat_at = ?, expires_at = ?
                WHERE lease_id = ? AND owner_id = ? AND released_at IS NULL
                """,
                (heartbeat_at, expires_at, lease_id, owner_id),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise RepositoryError(f"Active lease is no longer owned by {owner_id}: {lease_id}")
            connection.commit()
        lease = self.active_lease_by_id(lease_id)
        if lease is None:
            raise RepositoryError(f"Lease disappeared after heartbeat: {lease_id}")
        return lease

    def active_lease_by_id(self, lease_id: str) -> ResourceLease | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM resource_leases WHERE lease_id = ? AND released_at IS NULL",
                (lease_id,),
            ).fetchone()
            return self._lease(row) if row else None

    def release_lease(self, lease_id: str, owner_id: str, released_at: str, reason: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE resource_leases SET released_at = ?, release_reason = ?
                WHERE lease_id = ? AND owner_id = ? AND released_at IS NULL
                """,
                (released_at, reason, lease_id, owner_id),
            )
            connection.commit()
            return cursor.rowcount == 1

    def recover_and_acquire(
        self, stale_lease_id: str, lease: ResourceLease, recovered_at: str
    ) -> ResourceLease | None:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                active = connection.execute(
                    "SELECT * FROM resource_leases WHERE resource_id = ? AND released_at IS NULL",
                    (lease.resource_id,),
                ).fetchone()
                if not active or active["lease_id"] != stale_lease_id:
                    connection.rollback()
                    return self._lease(active) if active else None
                connection.execute(
                    """
                    UPDATE resource_leases SET released_at = ?, release_reason = 'expired_owner_dead'
                    WHERE lease_id = ?
                    """,
                    (recovered_at, stale_lease_id),
                )
                connection.execute(
                    """
                    INSERT INTO resource_leases(
                        lease_id, resource_id, owner_id, owner_pid, parent_pid,
                        label, intent_hash, priority, acquired_at, heartbeat_at,
                        expires_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lease.lease_id, lease.resource_id, lease.owner_id,
                        lease.owner_pid, lease.parent_pid, lease.label,
                        lease.intent_hash, lease.priority, lease.acquired_at,
                        lease.heartbeat_at, lease.expires_at,
                    ),
                )
                connection.commit()
                return None
            except BaseException:
                connection.rollback()
                raise

    def list_leases(self, *, active_only: bool = True) -> tuple[ResourceLease, ...]:
        where = "WHERE released_at IS NULL" if active_only else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM resource_leases {where} ORDER BY acquired_at, lease_id"
            ).fetchall()
            return tuple(self._lease(row) for row in rows)

    def import_remote_capture(self, capture: RemoteInventoryCapture) -> tuple[str, bool]:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    """
                    SELECT capture_id FROM remote_captures
                    WHERE provider = ? AND channel_id = ? AND scope = ? AND source_sha256 = ?
                    """,
                    (capture.provider, capture.channel_id, capture.scope, capture.source_sha256),
                ).fetchone()
                if existing:
                    connection.rollback()
                    return str(existing["capture_id"]), False
                connection.execute(
                    """
                    INSERT INTO remote_captures(
                        capture_id, provider, channel_id, scope, source_locator,
                        source_sha256, collected_at, item_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        capture.capture_id, capture.provider, capture.channel_id,
                        capture.scope, capture.source_locator, capture.source_sha256,
                        capture.collected_at, len(capture.items),
                    ),
                )
                for item in capture.items:
                    connection.execute(
                        """
                        INSERT INTO remote_inventory_items(
                            capture_id, remote_id, title, published_at, updated_at,
                            url, media_kind, raw_payload
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            capture.capture_id, item.remote_id, item.title,
                            item.published_at, item.updated_at, item.url,
                            item.media_kind, canonical_json(item.raw_payload),
                        ),
                    )
                connection.commit()
                return capture.capture_id, True
            except BaseException:
                connection.rollback()
                raise

    def reconcile_remote_capture(self, capture_id: str | None = None) -> ReconciliationReport:
        with self._connect() as connection:
            capture = connection.execute(
                "SELECT * FROM remote_captures WHERE capture_id = ?"
                if capture_id
                else "SELECT * FROM remote_captures ORDER BY collected_at DESC, capture_id DESC LIMIT 1",
                (capture_id,) if capture_id else (),
            ).fetchone()
            if not capture:
                raise RepositoryError("No remote inventory capture is available")
            remote_rows = connection.execute(
                "SELECT remote_id, title FROM remote_inventory_items WHERE capture_id = ?",
                (capture["capture_id"],),
            ).fetchall()
            local_rows = connection.execute(
                """
                SELECT p.remote_id, c.title
                FROM publications p JOIN content_items c ON c.content_id = p.content_id
                WHERE p.provider = 'youtube'
                """
            ).fetchall()
            remote = {str(row["remote_id"]): str(row["title"]) for row in remote_rows}
            local = {
                str(row["remote_id"]): str(row["title"]) if row["title"] is not None else ""
                for row in local_rows
            }
            matched = sorted(remote.keys() & local.keys())
            disagreements = tuple(
                {
                    "remoteId": remote_id,
                    "localTitle": local[remote_id],
                    "remoteTitle": remote[remote_id],
                }
                for remote_id in matched
                if local[remote_id] and local[remote_id] != remote[remote_id]
            )
            return ReconciliationReport(
                capture_id=str(capture["capture_id"]),
                channel_id=str(capture["channel_id"]),
                scope=str(capture["scope"]),
                remote_count=len(remote),
                local_publication_count=len(local),
                matched_remote_ids=tuple(matched),
                remote_only_ids=tuple(sorted(remote.keys() - local.keys())),
                local_outside_capture_ids=tuple(sorted(local.keys() - remote.keys())),
                title_disagreements=disagreements,
            )

    @staticmethod
    def _reservation(row: sqlite3.Row) -> ReleaseReservation:
        return ReleaseReservation(
            reservation_id=str(row["reservation_id"]),
            content_id=str(row["content_id"]),
            program_id=str(row["program_id"]),
            scheduled_at=str(row["scheduled_at"]),
            timezone=str(row["timezone"]),
            idempotency_key=str(row["idempotency_key"]),
            intent_hash=str(row["intent_hash"]),
            created_at=str(row["created_at"]),
            cancelled_at=str(row["cancelled_at"]) if row["cancelled_at"] else None,
            cancellation_reason=(
                str(row["cancellation_reason"]) if row["cancellation_reason"] else None
            ),
        )

    def content_product_line(self, content_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT product_line_id FROM content_items WHERE content_id = ?", (content_id,)
            ).fetchone()
            return str(row["product_line_id"]) if row else None

    def reserve_release(
        self, candidate: ReleaseReservation, *, max_rolling_7_days: int
    ) -> tuple[ReleaseReservation, bool]:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                repeated = connection.execute(
                    "SELECT * FROM release_reservations WHERE idempotency_key = ?",
                    (candidate.idempotency_key,),
                ).fetchone()
                if repeated:
                    if repeated["intent_hash"] != candidate.intent_hash:
                        raise RepositoryError(
                            "Release idempotency key is already bound to different intent"
                        )
                    connection.rollback()
                    return self._reservation(repeated), False
                active_content = connection.execute(
                    """
                    SELECT reservation_id FROM release_reservations
                    WHERE content_id = ? AND cancelled_at IS NULL
                    """,
                    (candidate.content_id,),
                ).fetchone()
                if active_content:
                    raise RepositoryError(
                        f"Content already has active reservation {active_content['reservation_id']}"
                    )
                active_time = connection.execute(
                    """
                    SELECT reservation_id FROM release_reservations
                    WHERE scheduled_at = ? AND cancelled_at IS NULL
                    """,
                    (candidate.scheduled_at,),
                ).fetchone()
                if active_time:
                    raise RepositoryError(
                        f"Release time is already reserved by {active_time['reservation_id']}"
                    )
                rows = connection.execute(
                    "SELECT scheduled_at FROM release_reservations WHERE cancelled_at IS NULL"
                ).fetchall()
                schedule = sorted(
                    [datetime.fromisoformat(str(row["scheduled_at"])) for row in rows]
                    + [datetime.fromisoformat(candidate.scheduled_at)]
                )
                for index, start in enumerate(schedule):
                    end = start + timedelta(days=7)
                    count = sum(start <= value < end for value in schedule[index:])
                    if count > max_rolling_7_days:
                        raise RepositoryError(
                            "Release reservation exceeds rolling seven-day channel capacity"
                        )
                connection.execute(
                    """
                    INSERT INTO release_reservations(
                        reservation_id, content_id, program_id, scheduled_at,
                        timezone, idempotency_key, intent_hash, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        candidate.reservation_id, candidate.content_id,
                        candidate.program_id, candidate.scheduled_at, candidate.timezone,
                        candidate.idempotency_key, candidate.intent_hash,
                        candidate.created_at,
                    ),
                )
                connection.commit()
                return candidate, True
            except BaseException:
                connection.rollback()
                raise

    def list_release_reservations(
        self, *, active_only: bool = True
    ) -> tuple[ReleaseReservation, ...]:
        where = "WHERE cancelled_at IS NULL" if active_only else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM release_reservations {where} ORDER BY scheduled_at, reservation_id"
            ).fetchall()
            return tuple(self._reservation(row) for row in rows)

    def cancel_release_reservation(
        self, reservation_id: str, *, cancelled_at: str, reason: str
    ) -> ReleaseReservation:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT * FROM release_reservations WHERE reservation_id = ?",
                    (reservation_id,),
                ).fetchone()
                if not row:
                    raise RepositoryError(f"Unknown release reservation: {reservation_id}")
                if row["cancelled_at"] is None:
                    connection.execute(
                        """
                        UPDATE release_reservations
                        SET cancelled_at = ?, cancellation_reason = ?
                        WHERE reservation_id = ?
                        """,
                        (cancelled_at, reason, reservation_id),
                    )
                    row = connection.execute(
                        "SELECT * FROM release_reservations WHERE reservation_id = ?",
                        (reservation_id,),
                    ).fetchone()
                connection.commit()
                return self._reservation(row)
            except BaseException:
                connection.rollback()
                raise


class YouTubeReleaseJournal:
    """Crash-safe runtime journal for upload sessions and remote IDs.

    This file is operational resume state, not the canonical publication ledger.
    Canonical IDs still flow through the shared channel reconciliation path.
    """

    SCHEMA = "youtube-release-journal-v1"

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            return {"schema": self.SCHEMA, "entries": {}}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema") != self.SCHEMA or not isinstance(payload.get("entries"), dict):
            raise RepositoryError(f"Invalid YouTube release journal: {self.path}")
        return payload

    def entry(self, content_id: str) -> dict[str, Any] | None:
        value = self.load()["entries"].get(content_id)
        return dict(value) if isinstance(value, dict) else None

    def record(self, content_id: str, **changes: Any) -> dict[str, Any]:
        payload = self.load()
        entries = payload["entries"]
        existing = dict(entries.get(content_id, {}))
        incoming_fingerprint = changes.get("videoFingerprint")
        existing_fingerprint = existing.get("videoFingerprint")
        if incoming_fingerprint and existing_fingerprint and incoming_fingerprint != existing_fingerprint:
            raise RepositoryError(
                f"YouTube release content changed after upload began: {content_id}"
            )
        incoming_video_id = changes.get("youtubeVideoId")
        if incoming_video_id:
            collision = next(
                (
                    key for key, item in entries.items()
                    if key != content_id
                    and isinstance(item, dict)
                    and item.get("youtubeVideoId") == incoming_video_id
                ),
                None,
            )
            if collision:
                raise RepositoryError(
                    f"YouTube video ID {incoming_video_id} is already assigned to {collision}"
                )
        existing.update(changes)
        entries[content_id] = existing
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        temporary.replace(self.path)
        return dict(existing)
