from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "worker-py"))

from worker.shorts.analytics import ingest_snapshot  # noqa: E402
from worker.shorts.audio import render_audio, render_audio_batch  # noqa: E402
from worker.shorts.contracts import ContractError, load_and_validate  # noqa: E402
from worker.shorts.ledger import load_ledger, record_publication  # noqa: E402
from worker.shorts.packaging import package_short  # noqa: E402
from worker.shorts.qc import check_manifest  # noqa: E402
from worker.shorts.render import render_short, render_thumbnail  # noqa: E402
from worker.shorts.review import build_review, write_review  # noqa: E402
from worker.shorts.workspace import (  # noqa: E402
    bootstrap_portfolio,
    canonical_short_workspace,
    find_manifest,
)
from worker.shorts.youtube import authorize, sync_analytics, upload_private  # noqa: E402


DEFAULT_PRODUCT = REPO / "configs" / "shorts" / "product.json"
DEFAULT_PORTFOLIO = REPO / "configs" / "shorts" / "pilot-2026-08.json"


def add_contract_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--product", type=Path, default=DEFAULT_PRODUCT)
    parser.add_argument("--portfolio", type=Path, default=DEFAULT_PORTFOLIO)


def load_contracts(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_and_validate(args.product.resolve(), args.portfolio.resolve())


def command_plan(args: argparse.Namespace) -> int:
    product, portfolio = load_contracts(args)
    counts: dict[str, int] = {}
    for entry in portfolio["entries"]:
        counts[str(entry["format"])] = counts.get(str(entry["format"]), 0) + 1
    print(f"cycle={portfolio['cycleId']} entries={len(portfolio['entries'])}")
    print("formats=" + json.dumps(counts, sort_keys=True))
    for entry in portfolio["entries"]:
        assignments = ", ".join(
            f"{key}={value}" for key, value in sorted(entry["experimentAssignments"].items())
        )
        print(
            f"{entry['shortId']} | {entry['format']} | {entry['durationSec']}s | "
            f"{assignments} | {entry['title']}"
        )
    return 0


def command_bootstrap(args: argparse.Namespace) -> int:
    product, portfolio = load_contracts(args)
    paths = bootstrap_portfolio(REPO, product, portfolio, force=args.force)
    print(f"bootstrapped={len(paths)}")
    for path in paths:
        print(path)
    return 0


def command_preflight(args: argparse.Namespace) -> int:
    product, _portfolio = load_contracts(args)
    _path, manifest = find_manifest(REPO, args.short)
    report = check_manifest(manifest, product)
    workspace = canonical_short_workspace(REPO, args.short)
    if args.production:
        audio_path = args.audio or workspace / "audio" / "master.wav"
        if not audio_path.is_file():
            report["errors"].append("PRODUCTION_AUDIO_MISSING")
            report["status"] = "fail"
    report_path = workspace / "reports" / "preflight.json"
    from worker.shorts.workspace import atomic_write_json

    atomic_write_json(report_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


def command_render(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    _path, manifest = find_manifest(REPO, args.short)
    workspace = canonical_short_workspace(REPO, args.short)
    audio_path: Path | None = None
    if not args.preview:
        audio_path = (args.audio or workspace / "audio" / "master.wav").resolve()
        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Production audio missing: {audio_path}. Supply --audio or use --preview for a silent visual proof."
            )
    output = render_short(REPO, manifest, audio_path=audio_path)
    print(output)
    return 0


def command_render_audio(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    manifest_path, manifest = find_manifest(REPO, args.short)
    output = render_audio(REPO, manifest_path, manifest, force=args.force)
    print(output)
    return 0


def command_render_audio_batch(args: argparse.Namespace) -> int:
    short_ids = args.short
    if args.all:
        _product, portfolio = load_contracts(args)
        short_ids = [str(entry["shortId"]) for entry in portfolio["entries"]]
    items = []
    for short_id in short_ids:
        manifest_path, manifest = find_manifest(REPO, short_id)
        items.append((manifest_path, manifest))
    outputs = render_audio_batch(REPO, items, force=args.force)
    for output in outputs:
        print(output)
    return 0


def command_render_thumbnail(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    _path, manifest = find_manifest(REPO, args.short)
    output = render_thumbnail(REPO, manifest)
    print(output)
    return 0


def command_package(args: argparse.Namespace) -> int:
    product, _portfolio = load_contracts(args)
    _path, manifest = find_manifest(REPO, args.short)
    report_path, report = package_short(REPO, product, manifest, require_audio=not args.preview)
    print(json.dumps({"path": str(report_path), "status": report["status"]}, indent=2))
    return 0 if report["status"] == "pass" else 1


def command_record(args: argparse.Namespace) -> int:
    product, _portfolio = load_contracts(args)
    _path, manifest = find_manifest(REPO, args.short)
    allow_public = (
        args.allow_public
        and os.environ.get("ELR_SHORTS_PUBLICATION_ENABLED") == "1"
        and bool(product["publishing"].get("publicPublishingEnabled"))
    )
    entry = record_publication(
        REPO,
        short_id=args.short,
        content_key=str(manifest["contentKey"]),
        status=args.status,
        youtube_id=args.youtube_id,
        scheduled_at=args.scheduled_at,
        published_at=args.published_at,
        allow_public=allow_public,
    )
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def command_ingest(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    path = ingest_snapshot(REPO, args.input.resolve())
    print(path)
    return 0


def command_review(args: argparse.Namespace) -> int:
    product, portfolio = load_contracts(args)
    review = build_review(REPO, product, portfolio, cutoff=args.cutoff)
    json_path, markdown_path = write_review(REPO, review)
    print(json.dumps({"json": str(json_path), "markdown": str(markdown_path)}, indent=2))
    return 0


def command_status(args: argparse.Namespace) -> int:
    product, portfolio = load_contracts(args)
    ledger = load_ledger(REPO)
    ledger_by_id = {str(item["shortId"]): item for item in ledger["entries"]}
    rows = []
    for entry in portfolio["entries"]:
        short_id = str(entry["shortId"])
        workspace = canonical_short_workspace(REPO, short_id)
        ledger_entry = ledger_by_id.get(short_id, {})
        rows.append(
            {
                "shortId": short_id,
                "format": entry["format"],
                "manifest": (workspace / "manifest.json").is_file(),
                "audio": (workspace / "audio" / "master.wav").is_file(),
                "video": (workspace / "video" / f"{short_id}.mp4").is_file(),
                "package": (workspace / "package" / "upload.json").is_file(),
                "publication": ledger_entry.get("status", "planned"),
            }
        )
    if args.json:
        print(json.dumps({"cycleId": portfolio["cycleId"], "rows": rows}, indent=2))
    else:
        print(f"cycle={portfolio['cycleId']} publicEnabled={product['publishing']['publicPublishingEnabled']}")
        for row in rows:
            print(
                f"{row['shortId']} manifest={row['manifest']} audio={row['audio']} "
                f"video={row['video']} package={row['package']} publication={row['publication']}"
            )
    return 0


def command_youtube_auth(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    print(authorize(REPO))
    return 0


def command_upload_private(args: argparse.Namespace) -> int:
    product, _portfolio = load_contracts(args)
    _manifest_path, manifest = find_manifest(REPO, args.short)
    package_path = canonical_short_workspace(REPO, args.short) / "package" / "upload.json"
    entry = upload_private(REPO, product, manifest, package_path)
    print(json.dumps(entry, ensure_ascii=False, indent=2))
    return 0


def command_sync_analytics(args: argparse.Namespace) -> int:
    _product, _portfolio = load_contracts(args)
    print(sync_analytics(REPO, start_date=args.start, end_date=args.end))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="English Listening Room autonomous Shorts controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Validate and display the controlled pilot portfolio")
    add_contract_args(plan)
    plan.set_defaults(func=command_plan)

    bootstrap = subparsers.add_parser("bootstrap", help="Create canonical workspaces and manifests")
    add_contract_args(bootstrap)
    bootstrap.add_argument("--force", action="store_true")
    bootstrap.set_defaults(func=command_bootstrap)

    preflight = subparsers.add_parser("preflight", help="Run content and production readiness checks")
    add_contract_args(preflight)
    preflight.add_argument("--short", required=True)
    preflight.add_argument("--production", action="store_true")
    preflight.add_argument("--audio", type=Path)
    preflight.set_defaults(func=command_preflight)

    render = subparsers.add_parser("render", help="Render a data-driven 9:16 Short")
    add_contract_args(render)
    render.add_argument("--short", required=True)
    render.add_argument("--audio", type=Path)
    render.add_argument("--preview", action="store_true")
    render.set_defaults(func=command_render)

    render_audio_parser = subparsers.add_parser("render-audio", help="Render and master Short audio with VoxCPM2")
    add_contract_args(render_audio_parser)
    render_audio_parser.add_argument("--short", required=True)
    render_audio_parser.add_argument("--force", action="store_true")
    render_audio_parser.set_defaults(func=command_render_audio)

    render_audio_batch_parser = subparsers.add_parser(
        "render-audio-batch",
        help="Render several Shorts in GPU-safe chunks while reusing each model load",
    )
    add_contract_args(render_audio_batch_parser)
    batch_selection = render_audio_batch_parser.add_mutually_exclusive_group(required=True)
    batch_selection.add_argument("--short", nargs="+")
    batch_selection.add_argument("--all", action="store_true")
    render_audio_batch_parser.add_argument("--force", action="store_true")
    render_audio_batch_parser.set_defaults(func=command_render_audio_batch)

    render_thumbnail_parser = subparsers.add_parser(
        "render-thumbnail", help="Render a dedicated 9:16 Shorts discovery cover"
    )
    add_contract_args(render_thumbnail_parser)
    render_thumbnail_parser.add_argument("--short", required=True)
    render_thumbnail_parser.set_defaults(func=command_render_thumbnail)

    package = subparsers.add_parser("package", help="Probe and create a private upload package")
    add_contract_args(package)
    package.add_argument("--short", required=True)
    package.add_argument("--preview", action="store_true")
    package.set_defaults(func=command_package)

    record = subparsers.add_parser("record-publication", help="Update the duplicate-safe publication ledger")
    add_contract_args(record)
    record.add_argument("--short", required=True)
    record.add_argument(
        "--status",
        required=True,
        choices=("planned", "packaged", "uploaded_private", "scheduled", "published", "failed"),
    )
    record.add_argument("--youtube-id")
    record.add_argument("--scheduled-at")
    record.add_argument("--published-at")
    record.add_argument("--allow-public", action="store_true")
    record.set_defaults(func=command_record)

    ingest = subparsers.add_parser("ingest-analytics", help="Import a CSV or JSON analytics snapshot")
    add_contract_args(ingest)
    ingest.add_argument("--input", required=True, type=Path)
    ingest.set_defaults(func=command_ingest)

    review = subparsers.add_parser("review", help="Evaluate experiments and write the next decision artifact")
    add_contract_args(review)
    review.add_argument("--cutoff", help="YYYY-MM-DD; defaults to today")
    review.set_defaults(func=command_review)

    status = subparsers.add_parser("status", help="Show workspace, package, and publication state")
    add_contract_args(status)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    youtube_auth = subparsers.add_parser("youtube-auth", help="Create the local OAuth token in an interactive browser")
    add_contract_args(youtube_auth)
    youtube_auth.set_defaults(func=command_youtube_auth)

    upload_private_parser = subparsers.add_parser(
        "upload-private", help="Idempotently upload a QC-passed package as private"
    )
    add_contract_args(upload_private_parser)
    upload_private_parser.add_argument("--short", required=True)
    upload_private_parser.set_defaults(func=command_upload_private)

    sync = subparsers.add_parser("sync-analytics", help="Sync aggregate Shorts metrics from YouTube Analytics")
    add_contract_args(sync)
    sync.add_argument("--start", help="YYYY-MM-DD; defaults to a 28-day window")
    sync.add_argument("--end", help="YYYY-MM-DD; defaults to yesterday")
    sync.set_defaults(func=command_sync_analytics)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (ContractError, FileNotFoundError, PermissionError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
