from __future__ import annotations

import argparse
import json
from pathlib import Path

from .repo import JsonPublicationRepository, LocalEpisodeRepository
from .schema import load_policy, parse_release_slots, read_json
from .service import PublicationPreflightService, validate_release_plan
from .types import PreflightResult


def candidate_json(result: PreflightResult) -> dict[str, object]:
    candidate = result.candidate
    return {
        "ok": result.ok,
        "errors": list(result.errors),
        "warnings": list(result.warnings),
        "existingVideoId": result.existing_video_id,
        "candidate": {
            "showId": candidate.show_id,
            "episodeId": candidate.episode_id,
            "title": candidate.title,
            "levelBand": candidate.level_band,
            "playlistId": candidate.playlist_id,
            "durationSec": candidate.duration_sec,
            "artifacts": {
                item.kind: {
                    "path": str(item.path),
                    "sizeBytes": item.size_bytes,
                    "sha256": item.sha256,
                }
                for item in candidate.artifacts
            },
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ELR channel publication safety controller")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--show", required=True)
    preflight.add_argument("--episode", required=True)
    plan = subparsers.add_parser("validate-plan")
    plan.add_argument("--plan", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policies, channel_spacing, series_spacing = load_policy(args.policy)
    if args.command == "validate-plan":
        slots = parse_release_slots(read_json(args.plan))
        errors = list(
            validate_release_plan(
                slots,
                min_channel_spacing_hours=channel_spacing,
                min_same_series_spacing_hours=series_spacing,
            )
        )
        service = PublicationPreflightService(
            LocalEpisodeRepository(args.repo_root),
            JsonPublicationRepository(args.ledger),
            policies,
        )
        candidates = []
        for slot in slots:
            result = service.preflight(slot.show_id, slot.episode_id)
            candidates.append(candidate_json(result))
            errors.extend(result.errors)
        print(json.dumps({"ok": not errors, "errors": errors, "candidates": candidates}, indent=2))
        return 0 if not errors else 1
    service = PublicationPreflightService(
        LocalEpisodeRepository(args.repo_root),
        JsonPublicationRepository(args.ledger),
        policies,
    )
    result = service.preflight(args.show, args.episode)
    print(json.dumps(candidate_json(result), indent=2))
    return 0 if result.ok else 1
