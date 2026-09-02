from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROGRAMMING = REPO_ROOT / "configs" / "channel" / "programming.json"
DEFAULT_WORKSPACE = REPO_ROOT / "workspace" / "shows"
HOSTS = {
    "series_a": ("Ethan", "Nora"),
    "series_b": ("Riley", "Sam"),
    "series_c": ("Leo", "Mia"),
}
LEVELS = {"series_a": "B1-B2", "series_b": "A2-B1", "series_c": "B2-C1"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def parse_content_id(content_id: str) -> tuple[str, int]:
    match = re.fullmatch(r"content:(series_[abc]):episode_(\d+)", content_id)
    if not match:
        raise ValueError(f"Unsupported dialogue contentId: {content_id}")
    return match.group(1), int(match.group(2))


def plan_fingerprint(plan_path: Path, programming_path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(plan_path.read_bytes())
    digest.update(programming_path.read_bytes())
    digest.update(b"long-form-scaffold-v1")
    return digest.hexdigest()


def validate_plan(plan: dict[str, Any], programming: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    briefs = plan.get("dialogueBriefs", [])
    slots = [
        slot
        for slot in plan.get("publicationSlots", [])
        if str(slot.get("contentId", "")).startswith("content:series_")
    ]
    expected = programming["dialogueFormat"]["weeklyMix"]
    expected_counts = {
        "standard": expected["standardEpisodes"],
        "extended": expected["extendedEpisodes"],
        "flagship_40": expected["flagship40Episodes"],
    }
    brief_counts = {name: 0 for name in expected_counts}
    for brief in briefs:
        fmt = brief.get("format")
        if fmt in brief_counts:
            brief_counts[fmt] += 1
        else:
            errors.append(f"unknown format {fmt!r} for {brief.get('contentId')}")
        if int(brief.get("candidateScore", 65)) < programming["trendResearch"]["minimumCandidateScore"]:
            errors.append(f"candidate score below threshold for {brief.get('contentId')}")
        try:
            parse_content_id(str(brief.get("contentId", "")))
        except ValueError as exc:
            errors.append(str(exc))
    if brief_counts != expected_counts:
        errors.append(f"brief mix {brief_counts} does not match programming {expected_counts}")
    if len(slots) != len(briefs):
        errors.append(f"dialogue slot count {len(slots)} does not match brief count {len(briefs)}")
    slot_formats = {slot["contentId"]: slot.get("format") for slot in slots}
    for brief in briefs:
        if slot_formats.get(brief["contentId"]) != brief.get("format"):
            errors.append(f"slot/brief format mismatch for {brief['contentId']}")
    pillars = {brief.get("topicPillar") for brief in briefs}
    if len(pillars) < programming["topicPortfolio"]["weeklyMinimumDistinctPillars"]:
        errors.append("weekly topic-pillar minimum is not met")
    flagship = plan["formatContracts"]["flagship_40"]
    if flagship.get("durationMinutes") != [35, 45] or not flagship.get("measuredMediaDurationRequired"):
        errors.append("flagship runtime contract must require a measured 35-45 minute render")
    return errors


def section_names(brief: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    if brief["format"] == "flagship_40":
        if brief["contentId"].endswith("episode_024") and plan.get("flagshipStructure"):
            return [str(item["beat"]) for item in plan["flagshipStructure"]]
        return [
            "cold_open_and_promise",
            "first_lived_story",
            "host_disagreement",
            "changed_condition_one",
            "guided_participation",
            "changed_condition_two",
            "natural_speed_application",
            "opening_callback",
        ]
    if brief["format"] == "extended":
        return ["cold_open", "first_story", "complication", "changed_condition", "guided_application", "callback"]
    return ["cold_open", "first_usable_move", "changed_condition", "live_repair", "callback"]


def production_record(brief: dict[str, Any], plan: dict[str, Any], scheduled_at: str) -> dict[str, Any]:
    series, episode = parse_content_id(brief["contentId"])
    return {
        "schema": "elr-dialogue-production-card-v1",
        "contentId": brief["contentId"],
        "series": series,
        "episode": episode,
        "format": brief["format"],
        "targetLevel": LEVELS[series],
        "hosts": list(HOSTS[series]),
        "scheduledAt": scheduled_at,
        "workingTitle": brief["workingTitle"],
        "topicPillar": brief["topicPillar"],
        "centralIdea": brief["centralIdea"],
        "formatContract": plan["formatContracts"][brief["format"]],
        "sections": section_names(brief, plan),
        "stablePipeline": [
            "fill_section_files_once",
            "assemble_with_scripts_long_form_py",
            "prepare_manifest_with_existing_tool",
            "render_with_scripts_elr_py",
            "run_one_release_preflight",
            "upload_with_authenticated_provider",
        ],
        "modelUse": "creative_section_drafting_and_named_defect_revision_only",
        "status": "section_drafting",
    }


def section_template(index: int, name: str, hosts: tuple[str, str]) -> str:
    label = name.replace("_", " ").title()
    return (
        f"## {label}\n\n"
        f"[Production note: Replace this note with finished dialogue. Do not leave TODO markers.]\n\n"
        f"{hosts[0]}: TODO\n\n"
        f"{hosts[1]}: TODO\n"
    )


def scaffold_week(plan_path: Path, programming_path: Path, workspace_root: Path) -> tuple[int, int]:
    plan = load_json(plan_path)
    programming = load_json(programming_path)
    errors = validate_plan(plan, programming)
    if errors:
        raise ValueError("; ".join(errors))
    fingerprint = plan_fingerprint(plan_path, programming_path)
    receipt_path = workspace_root / ".long_form_scaffold_receipt.json"
    if receipt_path.exists() and load_json(receipt_path).get("fingerprint") == fingerprint:
        return 0, len(plan["dialogueBriefs"])
    slots = {slot["contentId"]: slot["scheduledAt"] for slot in plan["publicationSlots"]}
    created = 0
    for brief in plan["dialogueBriefs"]:
        series, episode = parse_content_id(brief["contentId"])
        episode_id = f"episode_{episode:03d}"
        production_dir = workspace_root / series / episode_id / "production"
        sections_dir = production_dir / "sections"
        record_path = production_dir / "production_card.json"
        record = production_record(brief, plan, slots[brief["contentId"]])
        write_json(record_path, record)
        sections_dir.mkdir(parents=True, exist_ok=True)
        for index, name in enumerate(record["sections"], start=1):
            section_path = sections_dir / f"{index:02d}-{name}.md"
            if not section_path.exists():
                section_path.write_text(
                    section_template(index, name, HOSTS[series]), encoding="utf-8", newline="\n"
                )
        created += 1
    write_json(
        receipt_path,
        {
            "schema": "elr-long-form-scaffold-receipt-v1",
            "fingerprint": fingerprint,
            "plan": str(plan_path),
            "programming": str(programming_path),
            "episodeCount": len(plan["dialogueBriefs"]),
        },
    )
    return created, len(plan["dialogueBriefs"])


def assemble_episode(episode_dir: Path) -> Path:
    production_dir = episode_dir / "production"
    card = load_json(production_dir / "production_card.json")
    section_paths = sorted((production_dir / "sections").glob("*.md"))
    if len(section_paths) != len(card["sections"]):
        raise ValueError("section count does not match production card")
    section_text = "\n\n".join(path.read_text(encoding="utf-8").strip() for path in section_paths)
    if "TODO" in section_text or "[Production note:" in section_text:
        raise ValueError("unfinished section markers remain")
    hosts = ", ".join(card["hosts"])
    estimated = card["formatContract"].get("targetMinutes", card["formatContract"]["durationMinutes"])
    draft = (
        f"Title: {card['workingTitle']}\n"
        f"Description: {card['centralIdea']}\n"
        f"Target Level: {card['targetLevel']}\n"
        f"Estimated Duration: {estimated[0]}-{estimated[1]} minutes\n"
        f"Hosts: {hosts}\n"
        f"Show Profile: {card['series']}\n"
        f"Episode Engine: {card['centralIdea']}\n"
        f"Learner Problem: The viewer needs this idea in comprehensible, usable English.\n\n"
        f"[Teaching Plan]\nMove from a lived story to a reusable three-question device, changed conditions, guided participation, natural-speed application, and an opening callback.\n\n"
        f"[Episode Contract]\n{card['centralIdea']}\n\n---\n\n{section_text}\n"
    )
    episode_id = episode_dir.name
    output = episode_dir / f"000_{episode_id}.draft.md"
    output.write_text(draft, encoding="utf-8", newline="\n")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic ELR long-form planning and assembly.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-plan")
    validate.add_argument("--plan", required=True, type=Path)
    validate.add_argument("--programming", type=Path, default=DEFAULT_PROGRAMMING)
    scaffold = sub.add_parser("scaffold-week")
    scaffold.add_argument("--plan", required=True, type=Path)
    scaffold.add_argument("--programming", type=Path, default=DEFAULT_PROGRAMMING)
    scaffold.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE)
    assemble = sub.add_parser("assemble")
    assemble.add_argument("--episode-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "validate-plan":
        errors = validate_plan(load_json(args.plan), load_json(args.programming))
        if errors:
            for error in errors:
                print(f"ERROR {error}")
            return 2
        print("PASS long-form weekly plan")
        return 0
    if args.command == "scaffold-week":
        created, total = scaffold_week(args.plan, args.programming, args.workspace_root)
        print(f"scaffolded={created} total={total}")
        return 0
    output = assemble_episode(args.episode_dir)
    print(f"draft={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
