from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .repo import BookCatalogRepository, OperationLedgerRepository
from .schema import load_json_object, parse_series_policy
from .service import ClassicOperationsService
from .types import LifecycleState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the Classic Listening lifecycle ledger.")
    parser.add_argument("--repo-root", type=Path, required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("policy", help="Print the active series policy.")
    status = subparsers.add_parser("status", help="Print lifecycle status and event history.")
    status.add_argument("--book", required=True)
    status.add_argument("--chapter", type=int, required=True)

    transition = subparsers.add_parser("transition", help="Append one guarded lifecycle transition.")
    transition.add_argument("--book", required=True)
    transition.add_argument("--chapter", type=int, required=True)
    transition.add_argument("--to", choices=[state.value for state in LifecycleState], required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--reason", required=True)
    transition.add_argument("--idempotency-key", required=True)
    transition.add_argument("--evidence", type=Path)
    return parser


def _service(repo_root: Path) -> ClassicOperationsService:
    policy = parse_series_policy(load_json_object(repo_root / "configs" / "classics" / "series.json"))
    catalog = BookCatalogRepository(repo_root / "configs" / "classics" / "books")
    ledger = OperationLedgerRepository(repo_root / "workspace" / "classics" / "operations")
    return ClassicOperationsService(policy, catalog, ledger)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    service = _service(repo_root)
    if args.command == "policy":
        print(json.dumps(service.policy.__dict__, default=lambda value: value.value, indent=2))
        return 0
    if args.command == "status":
        events = service.ledger.read(args.book, args.chapter)
        print(
            json.dumps(
                {
                    "bookSlug": args.book,
                    "chapter": args.chapter,
                    "state": events[-1].to_state.value if events else None,
                    "eventCount": len(events),
                },
                indent=2,
            )
        )
        return 0
    evidence = load_json_object(args.evidence) if args.evidence else {}
    event = service.transition(
        args.book,
        args.chapter,
        LifecycleState(args.to),
        actor=args.actor,
        reason=args.reason,
        idempotency_key=args.idempotency_key,
        evidence=evidence,
    )
    print(json.dumps({"eventId": event.event_id, "sequence": event.sequence, "state": event.to_state.value}, indent=2))
    return 0
