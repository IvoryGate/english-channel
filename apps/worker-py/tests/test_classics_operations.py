from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from worker.classics.repo import BookCatalogRepository, LedgerError, OperationLedgerRepository
from worker.classics.schema import parse_series_policy
from worker.classics.service import ClassicOperationsService, OperationPolicyError
from worker.classics.types import AuthorityLevel, LifecycleState


def _write_catalog(root: Path, *, rights_status: str = "verified_public_domain") -> None:
    books = root / "catalog"
    books.mkdir(parents=True)
    payload = {
        "schema": "classic-listening-catalog-book-v1",
        "book": {
            "slug": "fixture",
            "title": "Fixture",
            "author": "An Author",
            "language": "en",
            "firstPublishedYear": 1800,
            "authorDeathYear": 1810,
        },
        "rights": {
            "status": rights_status,
            "approvedTerritories": ["US"] if rights_status == "verified_public_domain" else [],
            "reviewedAt": "2026-08-17" if rights_status == "verified_public_domain" else None,
            "evidence": [
                {
                    "kind": "term_rule",
                    "territory": "US",
                    "url": "https://example.test/rule",
                    "note": "Fixture evidence.",
                }
            ]
            if rights_status == "verified_public_domain"
            else [],
        },
        "source": {"url": "https://example.test/book"},
    }
    (books / "fixture.json").write_text(json.dumps(payload), encoding="utf-8", newline="\n")


def _policy(authority: AuthorityLevel = AuthorityLevel.PACKAGE_ONLY):
    payload = {
        "schema": "classic-listening-series-v1",
        "series": {
            "slug": "classic-listening",
            "authorityLevel": authority.value,
            "publicationTerritories": ["US"],
        },
        "cadence": {"requestedChaptersPerWeek": 2, "readyBufferChapters": 3},
        "release": {
            "policyRef": "configs/channel/release-policy.json",
            "programId": "classic-listening-baseline",
            "requiredGates": ["rights", "source", "audio", "subtitles", "visuals", "media", "packaging"],
        },
        "analytics": {"snapshotWindowsHours": [6, 24, 72, 168, 336, 672]},
        "experiments": {"maxThumbnailVariants": 3, "requireSingleChangedVariable": True},
    }
    return parse_series_policy(payload)


def _service(tmp_path: Path, authority: AuthorityLevel = AuthorityLevel.PACKAGE_ONLY) -> ClassicOperationsService:
    _write_catalog(tmp_path)
    return ClassicOperationsService(
        _policy(authority),
        BookCatalogRepository(tmp_path / "catalog"),
        OperationLedgerRepository(tmp_path / "operations"),
        now=lambda: datetime(2026, 8, 17, 12, 0, tzinfo=timezone.utc),
    )


def _transition(
    service: ClassicOperationsService,
    to_state: LifecycleState,
    sequence: int,
    evidence: dict | None = None,
):
    return service.transition(
        "fixture",
        1,
        to_state,
        actor="codex",
        reason=f"Advance to {to_state.value}",
        idempotency_key=f"fixture-001-{sequence:02d}-{to_state.value.lower()}",
        evidence=evidence,
    )


def test_replays_state_from_immutable_event_history(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _transition(service, LifecycleState.DISCOVERED, 1)
    _transition(service, LifecycleState.RIGHTS_VERIFIED, 2)
    _transition(service, LifecycleState.SOURCE_LOCKED, 3, {"sourceSha256": "a" * 64})
    _transition(service, LifecycleState.PLANNED, 4)
    _transition(service, LifecycleState.PRODUCING, 5)
    _transition(service, LifecycleState.QC_FAILED, 6, {"failedGates": ["audio"]})
    _transition(service, LifecycleState.PRODUCING, 7, {"repairPlan": "replace audio provider"})
    gates = {gate: True for gate in service.policy.required_release_gates}
    _transition(service, LifecycleState.READY_TO_UPLOAD, 8, {"gates": gates})

    reconstructed = ClassicOperationsService(service.policy, service.catalog, service.ledger)

    assert reconstructed.current_state("fixture", 1) is LifecycleState.READY_TO_UPLOAD
    assert len(service.ledger.read("fixture", 1)) == 8


def test_idempotent_retry_returns_original_event(tmp_path: Path) -> None:
    service = _service(tmp_path)
    first = service.transition(
        "fixture",
        1,
        LifecycleState.DISCOVERED,
        actor="codex",
        reason="Register chapter",
        idempotency_key="register-fixture-001",
    )
    retried = service.transition(
        "fixture",
        1,
        LifecycleState.DISCOVERED,
        actor="codex",
        reason="Register chapter",
        idempotency_key="register-fixture-001",
    )

    assert retried.event_id == first.event_id
    assert len(service.ledger.read("fixture", 1)) == 1


def test_reused_idempotency_key_with_new_intent_is_rejected(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _transition(service, LifecycleState.DISCOVERED, 1)

    with pytest.raises(OperationPolicyError, match="different transition"):
        service.transition(
            "fixture",
            1,
            LifecycleState.RIGHTS_VERIFIED,
            actor="codex",
            reason="Different operation",
            idempotency_key="fixture-001-01-discovered",
        )


def test_rights_and_release_gates_fail_closed(tmp_path: Path) -> None:
    _write_catalog(tmp_path, rights_status="review_required")
    service = ClassicOperationsService(
        _policy(),
        BookCatalogRepository(tmp_path / "catalog"),
        OperationLedgerRepository(tmp_path / "operations"),
    )
    _transition(service, LifecycleState.DISCOVERED, 1)
    with pytest.raises(OperationPolicyError, match="Rights are not verified"):
        _transition(service, LifecycleState.RIGHTS_VERIFIED, 2)

    approved = replace(service.catalog.get("fixture"), rights_status=service.catalog.get("fixture").rights_status)
    assert approved.rights_status.value == "review_required"


def test_package_only_authority_cannot_upload(tmp_path: Path) -> None:
    service = _service(tmp_path)
    states = [
        (LifecycleState.DISCOVERED, None),
        (LifecycleState.RIGHTS_VERIFIED, None),
        (LifecycleState.SOURCE_LOCKED, {"sourceSha256": "f" * 64}),
        (LifecycleState.PLANNED, None),
        (LifecycleState.PRODUCING, None),
        (
            LifecycleState.READY_TO_UPLOAD,
            {"gates": {gate: True for gate in service.policy.required_release_gates}},
        ),
    ]
    for sequence, (state, evidence) in enumerate(states, start=1):
        _transition(service, state, sequence, evidence)

    with pytest.raises(OperationPolicyError, match="Authority level 0"):
        _transition(
            service,
            LifecycleState.UPLOADED_PRIVATE,
            7,
            {"youtubeVideoId": "video-1", "privacyStatus": "private"},
        )


def test_ledger_detects_tampered_history(tmp_path: Path) -> None:
    service = _service(tmp_path)
    _transition(service, LifecycleState.DISCOVERED, 1)
    path = tmp_path / "operations" / "fixture" / "chapter_001" / "events.jsonl"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["reason"] = "Tampered after the fact"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8", newline="\n")

    with pytest.raises(LedgerError, match="Event hash mismatch"):
        service.ledger.read("fixture", 1)
