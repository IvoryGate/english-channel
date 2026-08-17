from __future__ import annotations

import sys
from pathlib import Path


def worker_root() -> Path:
    return Path(__file__).resolve().parents[2]


def repo_root() -> Path:
    return worker_root().parents[1]


def ensure_worker_importable() -> None:
    root = str(worker_root())
    if root not in sys.path:
        sys.path.insert(0, root)
