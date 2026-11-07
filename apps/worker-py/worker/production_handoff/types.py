from __future__ import annotations

from dataclasses import dataclass


STAGES = ("ready_to_prepare", "local_production", "package_verified", "public_release")


@dataclass(frozen=True)
class Check:
    stage: str
    name: str
    passed: bool
    detail: str
