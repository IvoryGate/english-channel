from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .providers.youtube import YouTubeApiProvider, authorize
from .repo import YouTubeReleaseJournal
from .schema import SchemaError, load_youtube_release_manifest
from .service import YouTubeReleaseService


def _print(value: Any) -> None:
    print(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=lambda item: str(item) if isinstance(item, Path) else item,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="API-first YouTube upload, asset, scheduling, and reconciliation controller."
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--journal", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("auth", help="Run the one-time OAuth desktop grant.")
    subparsers.add_parser("preflight", help="Validate every release item without remote writes.")
    status = subparsers.add_parser("status", help="Read the local crash-recovery journal.")
    status.add_argument("--content-id")
    adopt = subparsers.add_parser("adopt", help="Bind an existing private Studio upload to an item.")
    adopt.add_argument("--content-id", required=True)
    adopt.add_argument("--youtube-id", required=True)
    adopt.add_argument("--assets-already-set", action="store_true")
    sync = subparsers.add_parser("sync", help="Idempotently upload and/or schedule ready items.")
    sync.add_argument("--content-id")
    sync.add_argument("--apply-upload", action="store_true")
    sync.add_argument("--apply-schedule", action="store_true")
    return parser


def _manifest_header(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    channel_id = payload.get("youtubeChannelId")
    if not isinstance(channel_id, str) or not channel_id.strip():
        raise SchemaError("YouTube release manifest requires youtubeChannelId")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    journal_path = (
        args.journal.resolve()
        if args.journal
        else repo_root / "workspace" / "channel" / "youtube" / "release-journal.json"
    )
    journal = YouTubeReleaseJournal(journal_path)
    if args.command == "auth":
        _print({"token": str(authorize(repo_root)), "remoteMutation": False})
        return 0
    if args.command == "status":
        payload = journal.load()
        if args.content_id:
            payload = {
                "schema": payload["schema"],
                "entries": {args.content_id: payload["entries"].get(args.content_id)},
            }
        _print(payload)
        return 0
    if not args.manifest:
        raise SchemaError(f"{args.command} requires --manifest")
    manifest_path = args.manifest.resolve()
    header = _manifest_header(manifest_path)
    specs = load_youtube_release_manifest(manifest_path, repo_root)
    selected = tuple(
        item for item in specs
        if not getattr(args, "content_id", None) or item.content_id == args.content_id
    )
    if not selected:
        raise SchemaError(f"Content ID is not present in manifest: {getattr(args, 'content_id', '')}")
    if args.command == "preflight":
        service = YouTubeReleaseService(
            provider=None,
            journal=journal,
            expected_channel_id=str(header["youtubeChannelId"]),
        )
        rows = []
        failures = 0
        for spec in selected:
            try:
                fingerprint = service.preflight(spec)
                rows.append({"contentId": spec.content_id, "status": "pass", "sha256": fingerprint})
            except (OSError, ValueError) as exc:
                failures += 1
                rows.append({"contentId": spec.content_id, "status": "fail", "error": str(exc)})
        _print({"manifest": str(manifest_path), "rows": rows, "remoteMutation": False})
        return 1 if failures else 0
    provider = YouTubeApiProvider(repo_root)
    service = YouTubeReleaseService(
        provider,
        journal,
        expected_channel_id=str(header["youtubeChannelId"]),
    )
    if args.command == "adopt":
        result = service.adopt(selected[0], args.youtube_id)
        if args.assets_already_set:
            journal.record(
                selected[0].content_id,
                thumbnailSet=selected[0].thumbnail_path is not None,
                captionsSet=selected[0].captions_path is not None,
                updatedAt=service.now(),
            )
        _print(asdict(result))
        return 0
    rows = []
    failures = 0
    for spec in selected:
        try:
            rows.append(
                asdict(
                    service.sync(
                        spec,
                        apply_upload=args.apply_upload,
                        apply_schedule=args.apply_schedule,
                    )
                )
            )
        except (OSError, RuntimeError, ValueError) as exc:
            failures += 1
            rows.append({"content_id": spec.content_id, "state": "failed", "detail": str(exc)})
    _print(
        {
            "manifest": str(manifest_path),
            "applyUpload": args.apply_upload,
            "applySchedule": args.apply_schedule,
            "rows": rows,
        }
    )
    return 1 if failures else 0
