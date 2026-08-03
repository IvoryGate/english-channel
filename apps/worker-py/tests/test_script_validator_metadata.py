from __future__ import annotations

import sys
from pathlib import Path


VALIDATOR = Path(__file__).resolve().parents[3] / ".cursor" / "skills" / "dialogue-podcast-scriptwriting" / "scripts"
sys.path.insert(0, str(VALIDATOR))

from validate_podcast_script import validate_script_text  # noqa: E402


def test_character_profiles_are_not_counted_as_spoken_turns() -> None:
    draft = """Title: Test
Description: Test
characterProfiles:
  Ethan: "curious learner profile words"
  Nora: "warm coach profile words"

---

[Teaching Plan]
[Structure Map]
[Early Contract]
[Host Intro]
[Micro-Pocket]
[Recycle]
[Word Tour]
[Delivery: natural]
Ethan: Spoken words only.
[Delivery: natural]
Nora: These words count.
"""
    result = validate_script_text(draft, min_words=1, max_words=100, profile="series_a")
    assert result["word_count"] == 6
    assert result["host_turns"] == {"Ethan": 1, "Nora": 1}
