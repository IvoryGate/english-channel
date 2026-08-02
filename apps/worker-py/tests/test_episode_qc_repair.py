from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "workspace" / "shows" / "tools"))

from check_episode import blocking_segment_ids, has_blocking_qc_issues  # noqa: E402
from prepare_episode_manifest import target_max_len  # noqa: E402


def test_target_max_len_single_word_tight_cap() -> None:
    assert target_max_len(1) == 28
    assert target_max_len(2) == 48
    assert target_max_len(12) == 128
    assert target_max_len(20) is None


def test_blocking_segment_ids_short_too_long() -> None:
    report = {
        "chapter": {"flags": ["HAS_REVIEW_SEGMENTS"]},
        "segments": [
            {"id": "p001", "flags": [], "status": "ok"},
            {"id": "p089", "flags": ["CHECK_LONG", "SHORT_TOO_LONG"], "status": "review"},
            {"id": "p081", "flags": ["CHECK_LONG"], "status": "review"},
        ],
    }
    assert blocking_segment_ids(report) == ["p089"]
    assert has_blocking_qc_issues(report) is True


def test_check_long_alone_not_blocking() -> None:
    report = {
        "chapter": {"flags": ["HAS_REVIEW_SEGMENTS"]},
        "segments": [{"id": "p081", "flags": ["CHECK_LONG"], "status": "review"}],
    }
    assert blocking_segment_ids(report) == []
    assert has_blocking_qc_issues(report) is False
