from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .providers import LegacyLedgerProvider
from .repo import SqliteChannelRepository
from .schema import (
    normalize_classics_ledgers,
    normalize_dialogue_ledger,
    normalize_shorts_ledger,
)
from .types import ChannelPolicy, ImportRequest, ImportSummary, InventorySummary


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ChannelIdentityService:
    def __init__(
        self,
        policy: ChannelPolicy,
        repository: SqliteChannelRepository,
        legacy_provider: LegacyLedgerProvider | None = None,
        *,
        now: Callable[[], str] = utc_now,
    ) -> None:
        self.policy = policy
        self.repository = repository
        self.legacy_provider = legacy_provider or LegacyLedgerProvider()
        self.now = now

    def initialize(self) -> InventorySummary:
        now = self.now()
        self.repository.migrate(now)
        self.repository.seed_policy(self.policy, now)
        return self.repository.inventory()

    def _validate_request(self, request: ImportRequest) -> None:
        for record in request.records:
            if record.source_system != request.source.source_system:
                raise ValueError("Normalized record source system differs from import source")
            try:
                series = self.policy.series_policy(record.series_id)
            except KeyError as exc:
                raise ValueError(f"Import references unknown series {record.series_id}") from exc
            if series.product_line_id != record.product_line_id:
                raise ValueError(
                    f"Series {record.series_id} belongs to {series.product_line_id}, "
                    f"not {record.product_line_id}"
                )

    def _import(self, request: ImportRequest) -> ImportSummary:
        self.initialize()
        self._validate_request(request)
        return self.repository.import_identities(self.policy, request, self.now())

    def import_dialogue(self, path: Path) -> ImportSummary:
        source = self.legacy_provider.read_json(
            path, source_system="dialogue_publications_v1", collected_at=self.now()
        )
        return self._import(ImportRequest(source, normalize_dialogue_ledger(source)))

    def import_shorts(self, path: Path) -> ImportSummary:
        source = self.legacy_provider.read_json(
            path, source_system="shorts_publications_v1", collected_at=self.now()
        )
        return self._import(ImportRequest(source, normalize_shorts_ledger(source)))

    def import_classics(self, root: Path) -> ImportSummary:
        source = self.legacy_provider.read_classics(root, collected_at=self.now())
        return self._import(ImportRequest(source, normalize_classics_ledgers(source)))

    def inventory(self) -> InventorySummary:
        return self.repository.inventory()

