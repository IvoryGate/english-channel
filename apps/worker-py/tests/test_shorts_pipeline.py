from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from worker.shorts.analytics import ingest_snapshot
from worker.shorts.audio import _tempo_factor_for_variant, build_audio_manifest
from worker.shorts.contracts import ContractError, build_manifest, load_and_validate, validate_portfolio
from worker.shorts.ledger import load_ledger, record_publication
from worker.shorts.qc import check_audio, check_thumbnail
from worker.shorts.render import build_render_props, build_thumbnail_props
from worker.shorts.review import build_review, write_review
from worker.shorts.workspace import bootstrap_portfolio, read_json
from worker.shorts.youtube import upload_private


REPO = Path(__file__).resolve().parents[3]
PRODUCT_PATH = REPO / "configs" / "shorts" / "product.json"
PORTFOLIO_PATH = REPO / "configs" / "shorts" / "pilot-2026-08.json"


def contracts() -> tuple[dict, dict]:
    return load_and_validate(PRODUCT_PATH, PORTFOLIO_PATH)


def test_pilot_contract_has_controlled_format_mix_and_balanced_experiments() -> None:
    product, portfolio = contracts()

    assert len(portfolio["entries"]) == 12
    assert product["formatAllocation"] == {
        "micro_story": 4,
        "listen_choose": 3,
        "dialogue": 3,
        "classic_cliffhanger": 2,
    }
    hook_counts = {"question": 0, "statement": 0}
    duration_counts = {"short": 0, "long": 0}
    for entry in portfolio["entries"]:
        hook_counts[entry["experimentAssignments"]["hook"]] += 1
        duration_counts[entry["experimentAssignments"]["duration"]] += 1
    assert hook_counts == {"question": 6, "statement": 6}
    assert duration_counts == {"short": 6, "long": 6}


def test_accelerated_pilot_has_two_daily_release_slots() -> None:
    product, _ = contracts()
    publishing = product["publishing"]
    slots = publishing["slots"]

    assert publishing["timezone"] == "Asia/Shanghai"
    assert publishing["weeklyShorts"] == 14
    assert len(slots) == 14
    for weekday in (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ):
        assert [slot["time"] for slot in slots if slot["weekday"] == weekday] == [
            "08:00",
            "20:30",
        ]


def test_duplicate_content_is_rejected() -> None:
    product, portfolio = contracts()
    duplicate = json.loads(json.dumps(portfolio))
    duplicate["entries"][1]["hook"] = duplicate["entries"][0]["hook"]
    duplicate["entries"][1]["turns"] = duplicate["entries"][0]["turns"]
    duplicate["entries"][1]["prompt"] = duplicate["entries"][0]["prompt"]
    duplicate["entries"][1]["answer"] = duplicate["entries"][0]["answer"]
    duplicate["entries"][1]["hookStyle"] = duplicate["entries"][0]["hookStyle"]
    duplicate["entries"][1]["durationSec"] = duplicate["entries"][0]["durationSec"]
    duplicate["entries"][1]["experimentAssignments"] = duplicate["entries"][0][
        "experimentAssignments"
    ]

    with pytest.raises(ContractError, match="Duplicate content"):
        validate_portfolio(duplicate, product)


def test_bootstrap_is_idempotent_and_preserves_publication_state(tmp_path: Path) -> None:
    product, portfolio = contracts()
    paths = bootstrap_portfolio(tmp_path, product, portfolio)
    first = read_json(paths[0])
    first["publication"]["status"] = "uploaded_private"
    paths[0].write_text(json.dumps(first), encoding="utf-8")

    second_paths = bootstrap_portfolio(tmp_path, product, portfolio, force=True)
    regenerated = read_json(second_paths[0])

    assert len(paths) == 12
    assert regenerated["publication"]["status"] == "uploaded_private"
    assert regenerated["contentKey"] == first["contentKey"]


def test_publication_ledger_rejects_duplicate_youtube_id_and_backward_state(tmp_path: Path) -> None:
    product, portfolio = contracts()
    first = build_manifest(portfolio["entries"][0], product, portfolio["cycleId"])
    second = build_manifest(portfolio["entries"][1], product, portfolio["cycleId"])
    record_publication(
        tmp_path,
        short_id=first["shortId"],
        content_key=first["contentKey"],
        status="uploaded_private",
        youtube_id="youtube-1",
    )

    with pytest.raises(ValueError, match="already assigned"):
        record_publication(
            tmp_path,
            short_id=second["shortId"],
            content_key=second["contentKey"],
            status="uploaded_private",
            youtube_id="youtube-1",
        )
    with pytest.raises(ValueError, match="cannot move backward"):
        record_publication(
            tmp_path,
            short_id=first["shortId"],
            content_key=first["contentKey"],
            status="packaged",
            youtube_id="youtube-1",
        )
    assert len(load_ledger(tmp_path)["entries"]) == 1


def test_render_props_paginate_mobile_caption_text() -> None:
    product, portfolio = contracts()
    manifest = build_manifest(portfolio["entries"][0], product, portfolio["cycleId"])
    props = build_render_props(manifest)

    assert props["durationSec"] == manifest["durationSec"]
    assert all(len(scene["text"]) <= 50 or " " not in scene["text"] for scene in props["scenes"])
    assert props["scenes"][0]["startSec"] == 1.5
    assert props["answerStartSec"] > props["promptStartSec"]
    assert props["backgroundImage"]
    assert "shortId" not in props


def test_thumbnail_props_are_discovery_specific_and_hide_internal_id() -> None:
    product, portfolio = contracts()
    manifest = build_manifest(portfolio["entries"][4], product, portfolio["cycleId"])

    props = build_thumbnail_props(manifest)

    assert props["headline"] == "Fifteen or Fifty?"
    assert props["backgroundImage"]
    assert props["brandLogo"]
    assert "shortId" not in props


def test_thumbnail_qc_requires_vertical_png(tmp_path: Path) -> None:
    product, portfolio = contracts()
    manifest = build_manifest(portfolio["entries"][4], product, portfolio["cycleId"])
    thumbnail = tmp_path / "cover.png"
    png_header = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + (1080).to_bytes(4, "big")
        + (1920).to_bytes(4, "big")
    )
    thumbnail.write_bytes(png_header)

    report = check_thumbnail(thumbnail, manifest)

    assert report["status"] == "pass"
    assert report["width"] == 1080
    assert report["height"] == 1920


def test_audio_manifest_uses_single_narrator_and_real_answer_pause(tmp_path: Path, monkeypatch) -> None:
    product, portfolio = contracts()
    model = tmp_path / "pretrained_models" / "VoxCPM2"
    model.mkdir(parents=True)
    voice_dir = tmp_path / "assets" / "voices" / "series_b"
    voice_dir.mkdir(parents=True)
    (voice_dir / "riley_reference_clean.wav").write_bytes(b"riley")
    (voice_dir / "sam_reference_clean.wav").write_bytes(b"sam")
    monkeypatch.setenv("ELR_SHORTS_RUNTIME_ROOT", str(tmp_path))
    manifest = build_manifest(portfolio["entries"][0], product, portfolio["cycleId"])

    audio_manifest = build_audio_manifest(tmp_path, manifest)

    assert len(audio_manifest["turns"]) == 8
    assert {turn["speaker"] for turn in audio_manifest["turns"]} == {"Riley"}
    prompt = next(turn for turn in audio_manifest["turns"] if turn["sourceId"] == "prompt")
    assert prompt["pauseAfterSec"] == 2.25


def test_audio_pacing_corrects_safety_bounds_and_crossed_duration_variant() -> None:
    product, portfolio = contracts()
    short_manifest = build_manifest(portfolio["entries"][4], product, portfolio["cycleId"])
    long_manifest = build_manifest(portfolio["entries"][5], product, portfolio["cycleId"])

    assert _tempo_factor_for_variant(33.79, short_manifest) == pytest.approx(33.79 / 36.1)
    assert _tempo_factor_for_variant(49.2, short_manifest) == 1.0
    assert _tempo_factor_for_variant(33.0, long_manifest) == pytest.approx(33.0 / 54.0)
    assert _tempo_factor_for_variant(47.9, long_manifest) == pytest.approx(47.9 / 54.0)
    assert _tempo_factor_for_variant(60.5, long_manifest) == pytest.approx(60.5 / 58.9)


def test_audio_qc_rejects_stationary_sixty_hertz_hum(tmp_path: Path) -> None:
    product, portfolio = contracts()
    manifest = build_manifest(portfolio["entries"][0], product, portfolio["cycleId"])
    sample_rate = 48000
    seconds = 4
    time = np.arange(sample_rate * seconds, dtype=np.float64) / sample_rate
    audio = 0.03 * np.sin(2 * np.pi * 60.0 * time)
    audio_path = tmp_path / "hum.wav"
    sf.write(audio_path, audio, sample_rate, subtype="PCM_16")

    report = check_audio(audio_path, product, manifest)

    assert report["status"] == "fail"
    assert "ELECTRICAL_HUM_DETECTED" in report["errors"]


def test_private_upload_is_idempotent_before_google_client_is_loaded(tmp_path: Path) -> None:
    product, portfolio = contracts()
    manifest = build_manifest(portfolio["entries"][0], product, portfolio["cycleId"])
    package = tmp_path / "upload.json"
    package.write_text(json.dumps({"status": "pass", "video": "unused.mp4"}), encoding="utf-8")
    existing = record_publication(
        tmp_path,
        short_id=manifest["shortId"],
        content_key=manifest["contentKey"],
        status="uploaded_private",
        youtube_id="youtube-existing",
    )

    result = upload_private(tmp_path, product, manifest, package)

    assert result["youtubeId"] == existing["youtubeId"]


def test_analytics_review_scales_a_consistent_winner(tmp_path: Path) -> None:
    product, portfolio = contracts()
    csv_path = tmp_path / "analytics.csv"
    fields = [
        "short_id",
        "date",
        "views",
        "engaged_views",
        "average_percentage_viewed",
        "subscribers_gained",
        "likes",
        "comments",
        "shares",
        "long_form_views",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for entry in portfolio["entries"]:
            question = entry["experimentAssignments"]["hook"] == "question"
            writer.writerow(
                {
                    "short_id": entry["shortId"],
                    "date": "2026-08-24",
                    "views": 1000,
                    "engaged_views": 700 if question else 450,
                    "average_percentage_viewed": 102 if question else 78,
                    "subscribers_gained": 6 if question else 2,
                    "likes": 50 if question else 20,
                    "comments": 12 if question else 4,
                    "shares": 8 if question else 2,
                    "long_form_views": 35 if question else 10,
                }
            )

    snapshot = ingest_snapshot(tmp_path, csv_path)
    review = build_review(tmp_path, product, portfolio, cutoff="2026-08-24")
    json_path, markdown_path = write_review(tmp_path, review)
    hook = next(item for item in review["experiments"] if item["experiment"] == "hook")

    assert snapshot.is_file()
    assert hook["decision"] == "scale"
    assert hook["winner"] == "question"
    assert sum(review["nextPlan"]["formatAllocation"].values()) == 12
    assert review["nextPlan"]["defaultWinningVariants"]["hook"] == "question"
    assert json_path.is_file()
    assert "winner: question" in markdown_path.read_text(encoding="utf-8")
