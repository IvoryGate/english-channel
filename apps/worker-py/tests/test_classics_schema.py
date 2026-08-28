from __future__ import annotations

import json
from pathlib import Path

import pytest

from worker.classics.repo import BookCatalogRepository
from worker.classics.schema import (
    SchemaError,
    load_json_object,
    parse_audio_acceptance_policy,
    parse_book_record,
    parse_series_policy,
)
from worker.classics.service import evaluate_audio_candidate
from worker.classics.types import AudioSampleReview, AuthorityLevel, RightsStatus


def test_tracked_policy_and_catalog_are_valid() -> None:
    repo = Path(__file__).resolve().parents[3]
    policy = parse_series_policy(load_json_object(repo / "configs" / "classics" / "series.json"))
    catalog = BookCatalogRepository(repo / "configs" / "classics" / "books")
    persuasion = catalog.get("persuasion")

    assert policy.authority is AuthorityLevel.SCHEDULE
    assert policy.publication_territories == ("US", "GB")
    assert policy.chapters_per_week == 2
    assert policy.release_policy_ref == "configs/channel/release-policy.json"
    assert policy.release_program_id == "classic-listening-baseline"
    assert policy.analytics_windows_hours == (6, 24, 72, 168, 336, 672)
    assert policy.max_thumbnail_variants == 3
    assert persuasion.rights_status is RightsStatus.VERIFIED_PUBLIC_DOMAIN
    assert persuasion.approved_territories == ("US", "GB")
    assert {item.territory for item in persuasion.evidence} == {"US", "GB"}


def test_classics_release_request_is_registered_in_shared_channel_policy() -> None:
    repo = Path(__file__).resolve().parents[3]
    policy = parse_series_policy(load_json_object(repo / "configs" / "classics" / "series.json"))
    channel_policy = load_json_object(repo / policy.release_policy_ref)
    program = channel_policy["programs"][policy.release_program_id]

    assert channel_policy["authority"]["publicSchedulingEnabled"] is False
    assert program["productLine"] == "classic_listening"
    assert program["status"] == "active"
    assert program["preferredDailyWindows"] == ["08:00"]
    assert program["requestedUploadsPerWeek"] == policy.chapters_per_week
    assert program["minimumReadyInventory"] == policy.ready_buffer_chapters


def test_verified_rights_require_evidence_and_review_date() -> None:
    payload = {
        "schema": "classic-listening-catalog-book-v1",
        "book": {
            "slug": "fixture",
            "title": "Fixture",
            "author": "An Author",
            "language": "en",
            "firstPublishedYear": 1900,
            "authorDeathYear": 1910,
        },
        "rights": {
            "status": "verified_public_domain",
            "approvedTerritories": ["US"],
            "reviewedAt": None,
            "evidence": [],
        },
        "source": {"url": "https://example.test/book"},
    }

    with pytest.raises(SchemaError, match="require evidence and reviewedAt"):
        parse_book_record(payload)


def test_audio_acceptance_requires_every_dimension() -> None:
    with pytest.raises(SchemaError, match="missing dimensions"):
        parse_audio_acceptance_policy(
            {
                "schema": "classic-listening-audio-acceptance-v1",
                "thresholds": {
                    "minimumAsrSimilarity": 0.98,
                    "maximumTruePeakDbtp": -1.5,
                    "maximumClippedSamples": 0,
                    "requiredBlindReviewers": 1,
                },
                "cases": [{"id": "only", "dimension": "narration", "text": "A line."}],
            }
        )


def test_audio_candidate_fails_closed_on_electronic_artifact() -> None:
    repo = Path(__file__).resolve().parents[3]
    policy = parse_audio_acceptance_policy(
        load_json_object(repo / "configs" / "classics" / "audio-acceptance.json")
    )
    reviews = [
        AudioSampleReview(
            case_id=case.case_id,
            asr_similarity=0.995,
            true_peak_dbtp=-2.0,
            clipped_samples=0,
            electronic_artifact_detected=case.case_id == "sibilants-01",
            blind_approvals=1,
        )
        for case in policy.cases
    ]

    decision = evaluate_audio_candidate(policy, reviews)

    assert decision.accepted is False
    assert decision.failures == ("sibilants-01: electronic artifact detected",)


def test_json_configs_use_utf8_without_bom() -> None:
    repo = Path(__file__).resolve().parents[3]
    for path in (repo / "configs" / "classics").rglob("*.json"):
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")
        json.loads(raw.decode("utf-8"))
