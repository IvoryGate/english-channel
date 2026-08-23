from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .workspace import atomic_write_json, operation_root, read_json


LEDGER_SCHEMA = "elr-shorts-publication-ledger-v1"
STATUSES = ("planned", "packaged", "uploaded_private", "scheduled", "published", "failed")
STATUS_RANK = {status: index for index, status in enumerate(STATUSES[:-1])}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ledger_path(repo_root: Path) -> Path:
    return operation_root(repo_root) / "publication_ledger.json"


def load_ledger(repo_root: Path) -> dict[str, Any]:
    path = ledger_path(repo_root)
    if not path.exists():
        return {"schema": LEDGER_SCHEMA, "updatedAt": None, "entries": []}
    data = read_json(path)
    if data.get("schema") != LEDGER_SCHEMA or not isinstance(data.get("entries"), list):
        raise ValueError(f"Invalid publication ledger: {path}")
    return data


def record_publication(
    repo_root: Path,
    *,
    short_id: str,
    content_key: str,
    status: str,
    youtube_id: str | None = None,
    scheduled_at: str | None = None,
    published_at: str | None = None,
    allow_public: bool = False,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError(f"Unknown publication status: {status}")
    if status in {"uploaded_private", "scheduled", "published"} and not youtube_id:
        raise ValueError(f"youtube_id is required for {status}")
    if status == "published" and not allow_public:
        raise PermissionError("Recording public publication requires --allow-public")
    ledger = load_ledger(repo_root)
    entries = list(ledger["entries"])
    for item in entries:
        if youtube_id and item.get("youtubeId") == youtube_id and item.get("shortId") != short_id:
            raise ValueError(f"YouTube ID {youtube_id} is already assigned to {item.get('shortId')}")
        if item.get("contentKey") == content_key and item.get("shortId") != short_id:
            raise ValueError(f"Content key already belongs to {item.get('shortId')}")
    existing = next((item for item in entries if item.get("shortId") == short_id), None)
    now = utc_now()
    if existing is None:
        existing = {
            "shortId": short_id,
            "contentKey": content_key,
            "status": "planned",
            "youtubeId": None,
            "scheduledAt": None,
            "publishedAt": None,
            "history": [],
            "createdAt": now,
        }
        entries.append(existing)
    if existing.get("contentKey") != content_key:
        raise ValueError(f"{short_id} content key changed after publication identity was created")
    previous_status = str(existing.get("status", "planned"))
    if status != "failed" and previous_status != "failed":
        if STATUS_RANK[status] < STATUS_RANK.get(previous_status, 0):
            raise ValueError(f"Publication status cannot move backward: {previous_status} -> {status}")
    if youtube_id and existing.get("youtubeId") not in (None, youtube_id):
        raise ValueError(f"{short_id} already has YouTube ID {existing.get('youtubeId')}")
    existing.update(
        {
            "status": status,
            "youtubeId": youtube_id or existing.get("youtubeId"),
            "scheduledAt": scheduled_at or existing.get("scheduledAt"),
            "publishedAt": published_at or existing.get("publishedAt"),
            "updatedAt": now,
        }
    )
    existing["history"].append({"status": status, "at": now})
    ledger["entries"] = sorted(entries, key=lambda item: str(item["shortId"]))
    ledger["updatedAt"] = now
    atomic_write_json(ledger_path(repo_root), ledger)
    return existing
