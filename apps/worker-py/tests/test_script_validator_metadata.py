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


def test_empty_confirmation_is_an_editorial_warning_not_a_legacy_failure() -> None:
    draft = """Title: Test
Description: Test

[Teaching Plan]
[Episode Contract]
Riley: I missed the last part, so I need a recovery line.
Sam: Exactly.
Riley: Could you say that last part again? Practice it now.
Sam: I can use that instead of pretending I understood.
"""
    result = validate_script_text(draft, min_words=1, max_words=100, profile="series_b")
    assert result["ok"] is True
    assert result["warnings"] == [
        {
            "code": "AI_STYLE_EMPTY_CONFIRMATION",
            "message": "Replace 1 empty affirmation turn(s) with disagreement, consequence, memory, or forward motion.",
        }
    ]
