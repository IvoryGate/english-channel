from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from worker.shorts.analytics import (
    ANALYTICS_SCHEMA, LEGACY_ANALYTICS_SCHEMA, NUMERIC_FIELDS,
    derived_metrics, ingest_snapshot, load_latest_metrics, median_metrics,
    normalize_row, read_rows, store_snapshot,
)
from worker.shorts.review import build_review, score, write_review
import worker.shorts.youtube as youtube


def row(short_id: str = "one", **changes) -> dict:
    return {"shortId": short_id, "observedOn": "2026-11-01", "views": 1000,
            "engaged_views": 700, "average_percentage_viewed": 100,
            "subscribers_gained": 5, "likes": 10, "comments": 2, "shares": 1,
            "long_form_views": 10, **changes}


def contracts() -> tuple[dict, dict]:
    product = {"experiments": {"minimumEntriesPerVariant": 3,
                "minimumEngagedViewsPerVariant": 200, "winnerRelativeLift": .1,
                "secondaryGuardrailDrop": .1, "allocation": {}},
               "formatAllocation": {"dialogue": 4, "micro_story": 4}, "pilotSize": 8,
               "publishing": {"releasePolicyRef": "policy", "releaseProgramId": "program"}}
    portfolio = {"cycleId": "test", "entries": [
        {"shortId": str(n), "format": "dialogue" if n < 4 else "micro_story",
         "experimentAssignments": {"hook": "A" if n < 4 else "B"}} for n in range(8)]}
    return product, portfolio


def winner_rows() -> list[dict]:
    return [row(str(n), engaged_views=800 if n < 4 else 400,
                average_percentage_viewed=110 if n < 4 else 60,
                subscribers_gained=20 if n < 4 else 1,
                long_form_views=100 if n < 4 else 1) for n in range(8)]


def test_missing_empty_and_explicit_zero_are_distinct() -> None:
    normalized = normalize_row(row(likes="", shares=None, long_form_views="  ", comments="0"))
    assert normalized["likes"] is None
    assert normalized["shares"] is None
    assert normalized["comments"] == 0
    assert normalized["metricAvailability"]["comments"] == "observed"
    assert normalized["metricAvailability"]["likes"] == "missing"
    metrics = derived_metrics(normalized)
    assert metrics["interactions_per_1000_engaged"] is None
    assert metrics["long_form_views_per_1000_engaged"] is None


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), "-Infinity", -1, True, "not a number"])
def test_invalid_numeric_values_are_rejected(invalid) -> None:
    with pytest.raises(ValueError):
        normalize_row(row(likes=invalid))


def test_zero_is_preserved_but_zero_denominator_has_no_ratio() -> None:
    metrics = derived_metrics(normalize_row(row(subscribers_gained=0, long_form_views=0)))
    assert metrics["subscribers_per_1000_engaged"] == 0
    assert metrics["long_form_views_per_1000_engaged"] == 0
    all_zero = normalize_row(row(**{name: 0 for name in NUMERIC_FIELDS}))
    assert all_zero["views"] == 0
    assert derived_metrics(all_zero)["engaged_view_rate"] is None
    assert derived_metrics(all_zero)["subscribers_per_1000_engaged"] is None
    assert score(all_zero, median_metrics([all_zero])) is None
    with pytest.raises(ValueError):
        normalize_row(row(views=0, engaged_views=1))


def test_missing_metric_cannot_be_reweighted_into_a_score() -> None:
    complete = normalize_row(row())
    missing = normalize_row(row(long_form_views=None))
    baseline = median_metrics([complete, missing])
    assert baseline["long_form_views_per_1000_engaged"] is None
    assert score(missing, median_metrics([complete])) is None
    assert score(complete, baseline) is None


def test_availability_cannot_claim_observed_missing_or_unsupported_number() -> None:
    with pytest.raises(ValueError):
        normalize_row(row(likes=None, metricAvailability={"likes": "observed"}))
    with pytest.raises(ValueError):
        normalize_row(row(metricAvailability={"likes": "unsupported"}))


def test_snapshots_preserve_v1_and_reuse_identical_v2(tmp_path: Path) -> None:
    folder = tmp_path / "workspace/shorts/ops/analytics"
    folder.mkdir(parents=True)
    legacy_path = folder / "2026-11-01.json"
    original = json.dumps({"schema": LEGACY_ANALYTICS_SCHEMA, "rows": [row()]})
    legacy_path.write_text(original, encoding="utf-8")
    legacy = load_latest_metrics(tmp_path)["one"]
    assert legacy["views"] is None
    assert legacy["legacyValues"]["views"] == 1000
    assert legacy["metricAvailability"]["views"] == "legacy_unverified"
    with pytest.raises(ValueError, match="original source"):
        read_rows(legacy_path)
    first = store_snapshot(tmp_path, [row()], source="fixture", source_sha256="a" * 64)
    original_v2 = first.read_bytes()
    assert first == store_snapshot(tmp_path, [row()], source="fixture", source_sha256="a" * 64)
    assert first.read_bytes() == original_v2
    assert legacy_path.read_text(encoding="utf-8") == original
    assert load_latest_metrics(tmp_path)["one"]["views"] == 1000
    second = store_snapshot(tmp_path, [row(long_form_views=None)], source="new capture")
    assert second != first
    assert first.read_bytes() == original_v2
    assert load_latest_metrics(tmp_path)["one"]["long_form_views"] is None


def test_later_legacy_record_does_not_fall_back_to_old_complete_data(tmp_path: Path) -> None:
    first = store_snapshot(tmp_path, [row()], source="fixture")
    path = first.parent / "2026-11-02.json"
    path.write_text(json.dumps({"schema": LEGACY_ANALYTICS_SCHEMA,
                               "rows": [row(observedOn="2026-11-02")]}), encoding="utf-8")
    latest = load_latest_metrics(tmp_path)["one"]
    assert latest["observedOn"] == "2026-11-02"
    assert latest["views"] is None
    assert load_latest_metrics(tmp_path, cutoff="2026-11-01")["one"]["views"] == 1000


def test_complete_csv_retains_real_zeros_and_source_hash(tmp_path: Path) -> None:
    source = tmp_path / "export.csv"
    source.write_text("short_id,date,views,engaged_views,likes\none,2026-11-01,100,50,0\n", encoding="utf-8")
    saved = ingest_snapshot(tmp_path, source)
    payload = json.loads(saved.read_text(encoding="utf-8"))
    assert payload["schema"] == ANALYTICS_SCHEMA
    assert len(payload["sourceSha256"]) == 64
    assert payload["rows"][0]["likes"] == 0
    assert payload["rows"][0]["long_form_views"] is None


def test_legacy_rows_are_recorded_but_not_measured_or_scored(tmp_path: Path) -> None:
    product, portfolio = contracts()
    folder = tmp_path / "workspace/shorts/ops/analytics"
    folder.mkdir(parents=True)
    (folder / "old.json").write_text(json.dumps({"schema": LEGACY_ANALYTICS_SCHEMA,
                                                "rows": winner_rows()}), encoding="utf-8")
    result = build_review(tmp_path, product, portfolio, cutoff="2026-11-01")
    assert result["coverage"] == {"planned": 8, "recorded": 8, "measured": 0, "completeScoreEntries": 0}
    assert result["experiments"][0]["decision"] == "hold"
    assert result["nextPlan"]["formatAllocation"] == product["formatAllocation"]


def test_complete_evidence_can_still_scale(tmp_path: Path) -> None:
    product, portfolio = contracts()
    store_snapshot(tmp_path, winner_rows(), source="fixture")
    result = build_review(tmp_path, product, portfolio, cutoff="2026-11-01")
    assert result["experiments"][0]["decision"] == "scale"
    assert result["experiments"][0]["winner"] == "A"
    assert result["nextPlan"]["allocationEvidenceComplete"] is True
    assert result["nextPlan"]["formatAllocation"] == {"dialogue": 5, "micro_story": 3}


@pytest.mark.parametrize("mode", ["partial", "all_zero", "missing_row", "none"])
def test_incomplete_or_empty_evidence_cannot_scale_or_reallocate(tmp_path: Path, mode: str) -> None:
    product, portfolio = contracts()
    rows = winner_rows()
    if mode == "partial":
        rows[0]["long_form_views"] = None
    elif mode == "all_zero":
        rows = [row(str(n), **{name: 0 for name in NUMERIC_FIELDS}) for n in range(8)]
    elif mode == "missing_row":
        rows.pop()
    if mode != "none":
        store_snapshot(tmp_path, rows, source="fixture")
    result = build_review(tmp_path, product, portfolio, cutoff="2026-11-01")
    assert result["experiments"][0]["decision"] == "hold"
    assert result["nextPlan"]["formatAllocation"] == product["formatAllocation"]
    assert result["nextPlan"]["defaultWinningVariants"] == {}
    _, markdown = write_review(tmp_path, result)
    assert "hold" in markdown.read_text(encoding="utf-8")
    if mode in {"partial", "all_zero"}:
        assert "unavailable" in markdown.read_text(encoding="utf-8")


def test_api_missing_rows_differ_from_explicit_zero() -> None:
    headers = [{"name": "views"}, {"name": "likes"}]
    assert youtube._report_values({"columnHeaders": headers}) == {"views": None, "likes": None}
    assert youtube._report_values({"columnHeaders": headers, "rows": [[0, 0]]}) == {"views": 0, "likes": 0}
    with pytest.raises(ValueError):
        youtube._report_values({"columnHeaders": headers, "rows": [[100]]})


def test_api_sync_persists_unsupported_attribution_and_unreturned_fields(tmp_path: Path, monkeypatch) -> None:
    response = {"columnHeaders": [{"name": "views"}], "rows": [[0]]}
    service = SimpleNamespace(reports=lambda: SimpleNamespace(query=lambda **_: SimpleNamespace(
        execute=lambda **_: response)))
    monkeypatch.setattr(youtube, "_google_modules", lambda: (None, None, None, lambda *a, **kw: service, None))
    monkeypatch.setattr(youtube, "credentials", lambda _: object())
    monkeypatch.setattr(youtube, "load_ledger", lambda _: {"entries": [{"shortId": "one", "youtubeId": "id"}]})
    path = youtube.sync_analytics(tmp_path, start_date="2026-10-01", end_date="2026-11-01")
    payload = json.loads(path.read_text(encoding="utf-8"))
    record = payload["rows"][0]
    assert record["views"] == 0
    assert record["engaged_views"] is None
    assert record["metricAvailability"]["engaged_views"] == "not_returned"
    assert record["long_form_views"] is None
    assert record["metricAvailability"]["long_form_views"] == "unsupported"
    assert payload["window"] == {"start": "2026-10-01", "end": "2026-11-01"}


def test_api_recovery_to_identical_values_is_a_new_capture(tmp_path: Path, monkeypatch) -> None:
    responses = iter([
        {"columnHeaders": [{"name": "views"}], "rows": [[100]]},
        {"columnHeaders": [{"name": "views"}], "rows": []},
        {"columnHeaders": [{"name": "views"}], "rows": [[100]]},
    ])
    service = SimpleNamespace(reports=lambda: SimpleNamespace(query=lambda **_: SimpleNamespace(
        execute=lambda **_: next(responses))))
    monkeypatch.setattr(youtube, "_google_modules", lambda: (None, None, None, lambda *a, **kw: service, None))
    monkeypatch.setattr(youtube, "credentials", lambda _: object())
    monkeypatch.setattr(youtube, "load_ledger", lambda _: {"entries": [{"shortId": "one", "youtubeId": "id"}]})
    first = youtube.sync_analytics(tmp_path, start_date="2026-10-01", end_date="2026-11-01")
    original = first.read_bytes()
    missing = youtube.sync_analytics(tmp_path, start_date="2026-10-01", end_date="2026-11-01")
    assert load_latest_metrics(tmp_path)["one"]["views"] is None
    recovered = youtube.sync_analytics(tmp_path, start_date="2026-10-01", end_date="2026-11-01")
    assert len({first, missing, recovered}) == 3
    latest = load_latest_metrics(tmp_path)["one"]
    assert latest["views"] == 100
    assert latest["sourceSnapshot"] == recovered.name
    assert first.read_bytes() == original
    assert json.loads(recovered.read_text(encoding="utf-8"))["capturedAt"]
