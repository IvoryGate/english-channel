from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .repo import PolicyMismatchError, RepositoryError, SqliteChannelRepository
from .schema import (
    SchemaError,
    load_channel_policy,
    load_release_policy,
    load_resource_policies,
)
from .service import ChannelIdentityService, ReleaseReservationService
from .types import CollisionRecord, ImportSummary, InventorySummary, ReleaseReservation


def _json_default(value: object) -> str:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=_json_default))


def inventory_payload(value: InventorySummary) -> dict[str, object]:
    return {
        "database": str(value.database),
        "schemaVersion": value.schema_version,
        "channels": value.channel_count,
        "productLines": value.product_line_count,
        "series": value.series_count,
        "contentItems": value.content_item_count,
        "sourceAliases": value.source_alias_count,
        "artifacts": value.artifact_count,
        "publications": value.publication_count,
        "importRuns": value.import_run_count,
        "unresolvedCollisions": value.unresolved_collision_count,
        "contentByProductLine": value.content_by_product_line,
    }


def import_payload(value: ImportSummary) -> dict[str, object]:
    return {
        "importRunId": value.import_run_id,
        "sourceSystem": value.source_system,
        "sourceLocator": value.source_locator,
        "sourceSha256": value.source_sha256,
        "total": value.total,
        "inserted": value.inserted,
        "updated": value.updated,
        "unchanged": value.unchanged,
        "collided": value.collided,
        "collisionCount": value.collision_count,
        "ok": value.collided == 0,
    }


def collision_payload(value: CollisionRecord) -> dict[str, object | None]:
    payload = asdict(value)
    return {
        "collisionId": payload["collision_id"],
        "importRunId": payload["import_run_id"],
        "sourceSystem": payload["source_system"],
        "sourceItemId": payload["source_item_id"],
        "kind": payload["kind"],
        "identityKey": payload["identity_key"],
        "existingContentId": payload["existing_content_id"],
        "incomingContentId": payload["incoming_content_id"],
        "detail": payload["detail"],
        "createdAt": payload["created_at"],
        "resolvedAt": payload["resolved_at"],
    }


def reservation_payload(value: ReleaseReservation) -> dict[str, object | None]:
    return {
        "reservationId": value.reservation_id,
        "contentId": value.content_id,
        "programId": value.program_id,
        "scheduledAt": value.scheduled_at,
        "timezone": value.timezone,
        "idempotencyKey": value.idempotency_key,
        "intentHash": value.intent_hash,
        "createdAt": value.created_at,
        "cancelledAt": value.cancelled_at,
        "cancellationReason": value.cancellation_reason,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified local YouTube channel identity controller (no remote mutations)."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--release-policy", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Apply SQLite migrations and seed tracked channel policy.")
    subparsers.add_parser("status", help="Show local database and collision status.")
    subparsers.add_parser("inventory", help="Show canonical identity inventory counts.")
    collisions = subparsers.add_parser("collisions", help="List identity collisions for review.")
    collisions.add_argument("--all", action="store_true", help="Include resolved collisions.")
    dialogue = subparsers.add_parser("import-dialogue", help="Import a Dialogue publication JSON ledger.")
    dialogue.add_argument("--source", type=Path, required=True)
    shorts = subparsers.add_parser("import-shorts", help="Import a Shorts publication JSON ledger.")
    shorts.add_argument("--source", type=Path, required=True)
    classics = subparsers.add_parser("import-classics", help="Import Classic Listening event ledgers.")
    classics.add_argument("--source", type=Path, required=True, help="Operations directory containing events.jsonl files.")
    remote = subparsers.add_parser("import-youtube-rss", help="Import an immutable public YouTube RSS capture.")
    remote.add_argument("--source", type=Path, required=True)
    remote.add_argument("--scope", required=True)
    reconcile = subparsers.add_parser("reconcile", help="Compare canonical publications with a remote capture.")
    reconcile.add_argument("--capture-id")
    resources = subparsers.add_parser("resources", help="Inspect shared local resource leases.")
    resources.add_argument("action", choices=("status",))
    resources.add_argument("--all", action="store_true", help="Include released lease history.")
    release = subparsers.add_parser("release", help="Manage local channel release reservations.")
    release_actions = release.add_subparsers(dest="release_action", required=True)
    release_status = release_actions.add_parser("status", help="List release reservations.")
    release_status.add_argument("--all", action="store_true", help="Include cancelled history.")
    reserve = release_actions.add_parser("reserve", help="Reserve one local channel release slot.")
    reserve.add_argument("--content-id", required=True)
    reserve.add_argument("--program", required=True)
    reserve.add_argument("--scheduled-at", required=True)
    reserve.add_argument("--idempotency-key", required=True)
    cancel = release_actions.add_parser("cancel", help="Cancel a reservation without deleting it.")
    cancel.add_argument("--reservation-id", required=True)
    cancel.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    policy_path = (args.policy or repo_root / "configs" / "channel" / "control-plane.json").resolve()
    database_path = (args.database or repo_root / "workspace" / "channel" / "channel.sqlite").resolve()
    try:
        policy = load_channel_policy(policy_path)
        repository = SqliteChannelRepository(database_path)
        service = ChannelIdentityService(policy, repository)
        if args.command == "release":
            service.initialize()
            release_path = (
                args.release_policy
                or repo_root / "configs" / "channel" / "release-policy.json"
            ).resolve()
            release_service = ReleaseReservationService(
                policy, load_release_policy(release_path), repository
            )
            if args.release_action == "status":
                reservations = release_service.list(active_only=not args.all)
                _print(
                    {
                        "database": str(database_path),
                        "activeOnly": not args.all,
                        "reservations": [reservation_payload(item) for item in reservations],
                        "publicSchedulingAuthority": False,
                        "remoteMutationAuthority": False,
                    }
                )
                return 0
            if args.release_action == "reserve":
                reservation, inserted = release_service.reserve(
                    content_id=args.content_id,
                    program_id=args.program,
                    scheduled_at=args.scheduled_at,
                    idempotency_key=args.idempotency_key,
                )
                _print(
                    {
                        "inserted": inserted,
                        "reservation": reservation_payload(reservation),
                        "publicSchedulingAuthority": False,
                        "remoteMutationAuthority": False,
                    }
                )
                return 0
            reservation = release_service.cancel(
                args.reservation_id, reason=args.reason
            )
            _print(
                {
                    "reservation": reservation_payload(reservation),
                    "publicSchedulingAuthority": False,
                    "remoteMutationAuthority": False,
                }
            )
            return 0
        if args.command == "resources":
            service.initialize()
            load_resource_policies(repo_root / "configs" / "channel" / "resources.json")
            leases = repository.list_leases(active_only=not args.all)
            _print(
                {
                    "database": str(database_path),
                    "activeOnly": not args.all,
                    "leases": [asdict(item) for item in leases],
                    "remoteMutationAuthority": False,
                }
            )
            return 0
        if args.command == "import-youtube-rss":
            capture_id, inserted, item_count = service.import_youtube_rss(
                args.source, scope=args.scope
            )
            _print(
                {
                    "captureId": capture_id,
                    "inserted": inserted,
                    "itemCount": item_count,
                    "remoteMutationAuthority": False,
                }
            )
            return 0
        if args.command == "reconcile":
            report = service.reconcile(args.capture_id)
            _print(
                {
                    "captureId": report.capture_id,
                    "channelId": report.channel_id,
                    "scope": report.scope,
                    "remoteCount": report.remote_count,
                    "localPublicationCount": report.local_publication_count,
                    "matchedRemoteIds": list(report.matched_remote_ids),
                    "remoteOnlyIds": list(report.remote_only_ids),
                    "localOutsideCaptureIds": list(report.local_outside_capture_ids),
                    "titleDisagreements": list(report.title_disagreements),
                    "completeRemoteInventory": False,
                    "remoteMutationAuthority": False,
                }
            )
            return 1 if report.remote_only_ids or report.title_disagreements else 0
        if args.command == "init":
            _print(inventory_payload(service.initialize()))
            return 0
        if args.command in {"status", "inventory"}:
            inventory = service.inventory()
            payload = inventory_payload(inventory)
            if args.command == "status":
                payload = {
                    "initialized": inventory.schema_version > 0,
                    "remoteMutationAuthority": False,
                    **payload,
                }
            _print(payload)
            return 0
        if args.command == "collisions":
            collisions = repository.collisions(unresolved_only=not args.all)
            _print({"count": len(collisions), "collisions": [collision_payload(item) for item in collisions]})
            return 1 if any(item.resolved_at is None for item in collisions) else 0
        if args.command == "import-dialogue":
            summary = service.import_dialogue(args.source)
        elif args.command == "import-shorts":
            summary = service.import_shorts(args.source)
        else:
            summary = service.import_classics(args.source)
        _print(import_payload(summary))
        return 0 if summary.collided == 0 else 1
    except (FileNotFoundError, json.JSONDecodeError, PolicyMismatchError, RepositoryError, SchemaError, ValueError) as exc:
        _print({"ok": False, "error": str(exc)})
        return 2
