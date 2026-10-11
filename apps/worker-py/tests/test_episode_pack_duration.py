from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS = REPO_ROOT / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from pack_episode import duration_contract_error  # noqa: E402


def test_duration_contract_accepts_measured_flagship() -> None:
    card = {"formatContract": {"durationMinutes": [35, 45]}}
    report = {"verification": {"durationSec": 38 * 60}}
    assert duration_contract_error(card, report) is None


def test_duration_contract_rejects_short_flagship() -> None:
    card = {"formatContract": {"durationMinutes": [35, 45]}}
    report = {"verification": {"durationSec": 34 * 60}}
    assert "outside the 35-45 minute contract" in duration_contract_error(card, report)
