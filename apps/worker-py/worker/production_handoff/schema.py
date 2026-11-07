"""Pure JSON contracts; validation never reads files or grants authority."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any


def object_value(value: Any, name: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be nonempty text")
    return value


def relative_path(value: Any) -> str:
    value = text(value, "path")
    if (PureWindowsPath(value).drive or PureWindowsPath(value).root
            or PurePosixPath(value).is_absolute() or ".." in PureWindowsPath(value).parts):
        raise ValueError("Evidence paths must be project-relative without parent traversal")
    return value


def artifact(value: Any) -> dict:
    result = object_value(value, "artifact reference")
    relative_path(result.get("path"))
    if not re.fullmatch(r"[a-f0-9]{64}", str(result.get("sha256", ""))):
        raise ValueError("Artifact reference requires a lowercase SHA-256")
    return result


def identity_sha256(identity: dict) -> str:
    return hashlib.sha256(json.dumps(identity, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def accepted_review(value: Any, checks: tuple[str, ...]) -> dict:
    review = object_value(value, "review")
    if review.get("status") != "accepted":
        raise ValueError("Review is not accepted; unknown/pending does not pass")
    reviewer = object_value(review.get("reviewer"), "reviewer")
    text(reviewer.get("id"), "reviewer.id")
    if reviewer.get("kind") not in {"agent", "human"}:
        raise ValueError("Reviewer kind must declare agent or human")
    text(review.get("reviewedAt"), "reviewedAt")
    recorded = object_value(review.get("checks"), "review checks")
    if any(recorded.get(name) is not True for name in checks):
        raise ValueError("Required review checks must be explicitly true: " + ", ".join(checks))
    return review


def handoff(value: Any) -> dict:
    value = object_value(value, "handoff")
    if value.get("schema") != "elr-production-handoff-v1":
        raise ValueError("Unsupported production handoff schema")
    text(value.get("contentId"), "contentId")
    text(value.get("episodeId"), "episodeId")
    relative_path(value.get("workspace"))
    return value
