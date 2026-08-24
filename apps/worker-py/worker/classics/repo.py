from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .schema import (
    SLUG_PATTERN,
    calculate_event_hash,
    event_to_payload,
    load_json_object,
    parse_book_record,
    parse_event,
)
from .types import BookCatalogRecord, OperationEvent


class CatalogError(LookupError):
    pass


class LedgerError(RuntimeError):
    pass


class LedgerBusyError(LedgerError):
    pass


class BookCatalogRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def get(self, slug: str) -> BookCatalogRecord:
        if not SLUG_PATTERN.fullmatch(slug):
            raise CatalogError(f"Invalid book slug: {slug!r}")
        path = self.root / f"{slug}.json"
        if not path.is_file():
            raise CatalogError(f"Book is not in the rights catalog: {slug}")
        record = parse_book_record(load_json_object(path))
        if record.slug != slug:
            raise CatalogError(f"Catalog slug mismatch in {path}")
        return record

    def list(self) -> tuple[BookCatalogRecord, ...]:
        records = [parse_book_record(load_json_object(path)) for path in sorted(self.root.glob("*.json"))]
        return tuple(records)


class OperationLedgerRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _event_path(self, book_slug: str, chapter: int) -> Path:
        if not SLUG_PATTERN.fullmatch(book_slug):
            raise LedgerError(f"Invalid book slug: {book_slug!r}")
        if not isinstance(chapter, int) or isinstance(chapter, bool) or chapter < 1:
            raise LedgerError("chapter must be a positive integer")
        return self.root / book_slug / f"chapter_{chapter:03d}" / "events.jsonl"

    def read(self, book_slug: str, chapter: int) -> tuple[OperationEvent, ...]:
        path = self._event_path(book_slug, chapter)
        if not path.is_file():
            return ()
        events: list[OperationEvent] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise LedgerError(f"Event line {line_number} is not an object: {path}")
            event = parse_event(payload)
            expected = len(events) + 1
            if event.sequence != expected:
                raise LedgerError(f"Expected event sequence {expected}, found {event.sequence}: {path}")
            if event.book_slug != book_slug or event.chapter != chapter:
                raise LedgerError(f"Event identity mismatch on line {line_number}: {path}")
            if events and event.from_state != events[-1].to_state:
                raise LedgerError(f"Broken state chain on line {line_number}: {path}")
            if not events and event.from_state is not None:
                raise LedgerError(f"First event must have no fromState: {path}")
            expected_previous_hash = events[-1].event_hash if events else None
            if event.previous_event_hash != expected_previous_hash:
                raise LedgerError(f"Broken event hash chain on line {line_number}: {path}")
            if event.event_hash != calculate_event_hash(event):
                raise LedgerError(f"Event hash mismatch on line {line_number}: {path}")
            events.append(event)
        keys = [event.idempotency_key for event in events]
        if len(keys) != len(set(keys)):
            raise LedgerError(f"Duplicate idempotency key: {path}")
        return tuple(events)

    def find_by_idempotency_key(
        self, book_slug: str, chapter: int, idempotency_key: str
    ) -> OperationEvent | None:
        return next(
            (event for event in self.read(book_slug, chapter) if event.idempotency_key == idempotency_key),
            None,
        )

    @contextmanager
    def _lock(self, path: Path) -> Iterator[None]:
        lock_path = path.with_suffix(path.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = lock_path.open("a+b")
        if lock_path.stat().st_size == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            handle.close()
            raise LedgerBusyError(f"Ledger is locked: {lock_path}") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def append(self, event: OperationEvent) -> OperationEvent:
        path = self._event_path(event.book_slug, event.chapter)
        with self._lock(path):
            events = self.read(event.book_slug, event.chapter)
            expected_sequence = len(events) + 1
            expected_from = events[-1].to_state if events else None
            if event.sequence != expected_sequence:
                raise LedgerError(f"Expected sequence {expected_sequence}, received {event.sequence}")
            if event.from_state != expected_from:
                raise LedgerError(f"Expected fromState {expected_from}, received {event.from_state}")
            expected_previous_hash = events[-1].event_hash if events else None
            if event.previous_event_hash != expected_previous_hash:
                raise LedgerError("Event does not extend the current hash chain")
            if event.event_hash != calculate_event_hash(event):
                raise LedgerError("Event hash is invalid")
            if any(item.idempotency_key == event.idempotency_key for item in events):
                raise LedgerError(f"Duplicate idempotency key: {event.idempotency_key}")
            lines = [json.dumps(event_to_payload(item), ensure_ascii=False, sort_keys=True) for item in (*events, event)]
            self._atomic_write(path, "\n".join(lines) + "\n")
        return event

    @staticmethod
    def _atomic_write(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise
