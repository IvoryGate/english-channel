from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "long_form.py"
SPEC = importlib.util.spec_from_file_location("long_form", SCRIPT_PATH)
assert SPEC and SPEC.loader
long_form = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(long_form)


def test_current_plan_matches_programming_and_scaffolds_once(tmp_path: Path) -> None:
    plan_path = REPO_ROOT / "configs" / "channel" / "weekly-plan-2026-09-07.json"
    programming_path = REPO_ROOT / "configs" / "channel" / "programming.json"

    errors = long_form.validate_plan(
        long_form.load_json(plan_path),
        long_form.load_json(programming_path),
    )
    assert errors == []

    created, total = long_form.scaffold_week(plan_path, programming_path, tmp_path)
    assert (created, total) == (8, 8)
    assert (tmp_path / "series_b" / "episode_024" / "production" / "production_card.json").exists()
    assert (tmp_path / "series_c" / "episode_025" / "production" / "production_card.json").exists()

    created_again, total_again = long_form.scaffold_week(plan_path, programming_path, tmp_path)
    assert (created_again, total_again) == (0, 8)


def test_assemble_refuses_unfinished_sections_then_writes_finished_draft(tmp_path: Path) -> None:
    plan_path = REPO_ROOT / "configs" / "channel" / "weekly-plan-2026-09-07.json"
    programming_path = REPO_ROOT / "configs" / "channel" / "programming.json"
    long_form.scaffold_week(plan_path, programming_path, tmp_path)
    episode_dir = tmp_path / "series_b" / "episode_023"

    try:
        long_form.assemble_episode(episode_dir)
    except ValueError as exc:
        assert "unfinished section markers" in str(exc)
    else:
        raise AssertionError("unfinished sections must not assemble")

    card = json.loads(
        (episode_dir / "production" / "production_card.json").read_text(encoding="utf-8")
    )
    for index, section_path in enumerate(sorted((episode_dir / "production" / "sections").glob("*.md"))):
        section_path.write_text(
            f"## {card['sections'][index]}\n\nRiley: A finished line.\n\nSam: A real response.\n",
            encoding="utf-8",
            newline="\n",
        )

    output = long_form.assemble_episode(episode_dir)
    text = output.read_text(encoding="utf-8")
    assert "Title: A Bad Morning Is Not a Bad Life" in text
    assert "[Teaching Plan]" in text
    assert "[Episode Contract]" in text
    assert "TODO" not in text
