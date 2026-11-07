"""Read-only filesystem evidence repository; no database or generated state."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .schema import artifact, object_value, relative_path


class EvidenceRepository:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, relative: str) -> Path:
        return self.root / relative_path(relative)

    def verify(self, reference: dict) -> Path:
        reference = artifact(reference)
        path = self.path(reference["path"])
        digest, size = hashlib.sha256(), 0
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        if size == 0 or digest.hexdigest() != reference["sha256"]:
            raise ValueError(f"Missing, empty or stale artifact: {reference['path']}")
        return path

    def json(self, reference: dict) -> dict:
        reference = artifact(reference)
        path = self.path(reference["path"])
        if path.stat().st_size > 8_000_000:
            raise ValueError("JSON evidence exceeds 8 MB")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != reference["sha256"]:
            raise ValueError(f"Stale JSON evidence: {reference['path']}")
        return object_value(json.loads(data), "JSON evidence")

    def image_dimensions(self, reference: dict) -> tuple[int, int]:
        from PIL import Image
        with Image.open(self.verify(reference)) as image:
            image.load()
            return image.size

    def read_handoff(self, path: Path) -> dict:
        return object_value(json.loads(path.read_bytes()), "handoff")
