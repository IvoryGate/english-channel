from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .repo import EvidenceRepository
from .service import HandoffService


def run_check(root: Path, input_path: Path, required: str, final_audio_check: Callable | None = None) -> int:
    repository = EvidenceRepository(root)
    try:
        payload = repository.read_handoff(input_path)
        report = HandoffService(repository, final_audio_check).validate(payload)
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc), "publicReleaseAllowed": False}))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["stages"].get(required) is True else 2
