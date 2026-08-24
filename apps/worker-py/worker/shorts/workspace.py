from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .contracts import build_manifest


def canonical_short_workspace(repo_root: Path, short_id: str) -> Path:
    return (repo_root.resolve() / "workspace" / "shorts" / short_id).resolve()


def manifest_path(repo_root: Path, short_id: str) -> Path:
    return canonical_short_workspace(repo_root, short_id) / "manifest.json"


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def ensure_workspace(repo_root: Path, short_id: str) -> Path:
    root = canonical_short_workspace(repo_root, short_id)
    for name in ("audio", "video", "reports", "package"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def bootstrap_entry(
    repo_root: Path,
    product: dict[str, Any],
    portfolio: dict[str, Any],
    entry: dict[str, Any],
    *,
    force: bool = False,
) -> Path:
    root = ensure_workspace(repo_root, str(entry["shortId"]))
    path = root / "manifest.json"
    generated = build_manifest(entry, product, str(portfolio["cycleId"]))
    if path.exists() and not force:
        current = read_json(path)
        if current.get("contentKey") != generated["contentKey"]:
            raise ValueError(
                f"{entry['shortId']} already exists with different content. "
                "Use a new shortId instead of overwriting published identity."
            )
        return path
    if path.exists() and force:
        current = read_json(path)
        generated["publication"] = current.get("publication", generated["publication"])
    atomic_write_json(path, generated)
    return path


def bootstrap_portfolio(
    repo_root: Path,
    product: dict[str, Any],
    portfolio: dict[str, Any],
    *,
    force: bool = False,
) -> list[Path]:
    return [
        bootstrap_entry(repo_root, product, portfolio, entry, force=force)
        for entry in portfolio["entries"]
    ]


def find_manifest(repo_root: Path, short_id: str) -> tuple[Path, dict[str, Any]]:
    path = manifest_path(repo_root, short_id)
    if not path.is_file():
        raise FileNotFoundError(f"Short workspace not bootstrapped: {short_id}. Run shorts.py bootstrap.")
    return path, read_json(path)


def operation_root(repo_root: Path) -> Path:
    path = (repo_root.resolve() / "workspace" / "shorts" / "ops").resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path
