from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_json(relative_path: str) -> dict:
    return json.loads((REPO_ROOT / relative_path).read_text(encoding="utf-8"))


def test_programming_defines_a_real_40_minute_flagship_lane() -> None:
    programming = _load_json("configs/channel/programming.json")
    dialogue = programming["dialogueFormat"]

    assert dialogue["flagship40DurationMinutes"] == [35, 45]
    assert dialogue["flagship40TargetMinutes"] == [38, 42]
    assert dialogue["weeklyMix"] == {
        "standardEpisodes": 6,
        "extendedEpisodes": 0,
        "flagship40Episodes": 2,
    }
    assert len(dialogue["requiredFlagshipBeats"]) >= 8


def test_programming_requires_a_diverse_evidence_backed_topic_portfolio() -> None:
    programming = _load_json("configs/channel/programming.json")
    portfolio = programming["topicPortfolio"]
    pillar_ids = {pillar["id"] for pillar in portfolio["pillars"]}

    assert portfolio["weeklyMinimumDistinctPillars"] >= 4
    assert {
        "practical_english",
        "everyday_life",
        "relationships",
        "psychology",
        "resilience",
        "philosophy",
    } <= pillar_ids
    assert programming["trendResearch"]["trendEvidenceMaxAgeDays"] == 7
    assert programming["trendResearch"]["minimumCandidateScore"] >= 65


def test_next_week_plan_has_two_flagships_and_six_standard_episodes() -> None:
    plan = _load_json("configs/channel/weekly-plan-2026-09-07.json")
    briefs = plan["dialogueBriefs"]
    formats = [brief["format"] for brief in briefs]

    assert formats.count("standard") == 6
    assert formats.count("extended") == 0
    assert formats.count("flagship_40") == 2
    assert len({brief["topicPillar"] for brief in briefs}) >= 4

    flagships = [brief for brief in briefs if brief["format"] == "flagship_40"]
    contract = plan["formatContracts"]["flagship_40"]
    assert contract["durationMinutes"] == [35, 45]
    assert contract["targetMinutes"] == [38, 42]
    assert contract["measuredMediaDurationRequired"] is True
    assert all(flagship["candidateScore"] >= 65 for flagship in flagships)
    assert all("40-Minute" in flagship["workingTitle"] for flagship in flagships)


def test_next_week_plan_expands_to_eight_dialogue_slots_and_fourteen_shorts() -> None:
    plan = _load_json("configs/channel/weekly-plan-2026-09-07.json")
    slots = plan["publicationSlots"]
    dialogue_slots = [slot for slot in slots if slot["contentId"].startswith("content:series_")]
    shorts_slots = [slot for slot in slots if slot["contentId"].startswith("content:shorts_main:")]
    classic_slots = [slot for slot in slots if slot["contentId"].startswith("content:classic_listening:")]

    assert len(dialogue_slots) == 8
    assert len(shorts_slots) == 14
    assert len(classic_slots) == 2
    assert plan["portfolio"]["longFormCount"] == len(dialogue_slots) + len(classic_slots)


def test_flagship_release_gate_rejects_a_standard_length_render() -> None:
    plan = _load_json("configs/channel/weekly-plan-2026-09-07.json")
    flagship_gates = plan["releaseGates"]["flagship_40"]

    assert "measured_duration_35_to_45_minutes" in flagship_gates
    assert "stimulus_change_gap_no_more_than_4_minutes" in flagship_gates
    assert "three_native_ab_packaging_variants_ready" in flagship_gates


def test_first_flagship_brief_has_runtime_story_safety_and_packaging_contracts() -> None:
    brief = _load_json("configs/channel/flagship-40-series-b-overthinking-2026-09.json")

    assert brief["runtimeContract"]["allowedMinutes"] == [35, 45]
    assert brief["runtimeContract"]["measuredRenderRequired"] is True
    assert len(brief["structure"]) == 8
    assert sum(segment["words"][0] for segment in brief["structure"]) >= 5200
    assert brief["editorialSafety"]["scope"] == "education_and_reflection_not_therapy"
    assert brief["packagingExperiment"]["nativeYouTubeTest"] is True
    assert len(brief["packagingExperiment"]["variants"]) == 3


def test_failed_deep_pilot_is_recorded_as_invalid_treatment() -> None:
    pilot = _load_json("configs/channel/deep-practice-pilot-series-b-2026-09.json")

    assert pilot["formatResult"] == "standard"
    assert pilot["deepPracticeContractPass"] is False
    assert pilot["experiment"]["treatmentValidity"] == "invalid_duration_below_25_minutes"
