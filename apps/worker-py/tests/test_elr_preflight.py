from __future__ import annotations

import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "scripts"
TOOLS = REPO / "workspace" / "shows" / "tools"
for import_path in (SCRIPTS, TOOLS):
    sys.path.insert(0, str(import_path))

from elr_production import build_context, preflight_episode  # noqa: E402
from episode_artifacts import artifact_paths  # noqa: E402


def _write(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_preflight_rejects_missing_canonical_workspace(tmp_path: Path) -> None:
    context = build_context(tmp_path, "series_a", 17, tmp_path / "youtube")
    report = preflight_episode(context, runtime_checks=False)
    assert report.ok is False
    assert report.checks[0].name == "workspace"
    assert report.checks[0].status == "error"


def test_preflight_scaffolds_youtube_metadata_and_detects_missing_assets(tmp_path: Path, monkeypatch) -> None:
    context = build_context(tmp_path, "series_b", 17, tmp_path / "youtube")
    paths = artifact_paths(context.workspace, context.episode_id)
    title = "Learn One Positive English Line — Not a Speech, Just One | Easy English Podcast A2-B1"
    draft = f"""Title: {title}
Description: A practical lesson.
Show Profile: series_b

[Part 1]
Riley: This is a short test line.
Sam: This is another short test line.
"""
    _write(paths["draft"], draft)
    manifest = {
        "episodeId": context.episode_id,
        "showId": "series_b",
        "title": title,
        "description": "A practical lesson.",
        "hosts": {},
        "turns": [
            {"text": "This is a short test line.", "wordCount": 6},
            {"text": "This is another short test line.", "wordCount": 6},
        ],
    }
    _write(paths["manifest"], json.dumps(manifest))

    report = preflight_episode(context, runtime_checks=False, scaffold_metadata=True)

    assert paths["youtube"].is_file()
    saved = json.loads(paths["youtube"].read_text(encoding="utf-8"))
    assert saved["title"] == title
    by_name = {check.name: check for check in report.checks}
    assert by_name["manifest-coverage"].status == "pass"
    assert by_name["cover-16x9"].status == "error"
    assert report.ok is False

    monkeypatch.setattr(
        "elr_production.validate_script_text",
        lambda *_args, **_kwargs: {"ok": True, "word_count": 12, "issues": []},
    )
    audio_report = preflight_episode(
        context,
        runtime_checks=False,
        scaffold_metadata=True,
        require_visuals=False,
    )
    audio_by_name = {check.name: check for check in audio_report.checks}
    assert "cover-16x9" not in audio_by_name
    assert "background-16x9" not in audio_by_name
    assert "workspace-disk" not in audio_by_name
    assert "export-disk" not in audio_by_name
    assert audio_by_name["visual-assets"].status == "warn"
    assert audio_report.ok is True


def test_preflight_uses_flagship_spoken_word_contract(tmp_path: Path, monkeypatch) -> None:
    context = build_context(tmp_path, "series_b", 24, tmp_path / "youtube")
    paths = artifact_paths(context.workspace, context.episode_id)
    draft = """Title: A Flagship Test
Description: A practical long-form conversation.

[Teaching Plan]
Practice one idea in changed conditions.

[Episode Contract]
Use the idea today.

Riley: This is a complete test line for the flagship contract.
Sam: Comment with the next step you will practice today.
"""
    _write(paths["draft"], draft)
    _write(
        paths["manifest"],
        json.dumps(
            {
                "episodeId": context.episode_id,
                "showId": "series_b",
                "title": "A Flagship Test",
                "description": "A practical long-form conversation.",
                "hosts": {},
                "turns": [
                    {"text": "This is a complete test line for the flagship contract.", "wordCount": 10},
                    {"text": "Comment with the next step you will practice today.", "wordCount": 9},
                ],
            }
        ),
    )
    _write(
        context.workspace / "production" / "production_card.json",
        json.dumps(
            {
                "format": "flagship_40",
                "formatContract": {"spokenWordTarget": [10, 30]},
            }
        ),
    )
    monkeypatch.setattr(
        "elr_production.validate_script_text",
        lambda _text, *, min_words, max_words, profile: {
            "ok": (min_words, max_words, profile) == (10, 30, "series_b"),
            "word_count": 19,
            "issues": [],
        },
    )

    report = preflight_episode(
        context,
        runtime_checks=False,
        scaffold_metadata=True,
        require_visuals=False,
    )

    assert {check.name: check for check in report.checks}["script-quality"].status == "pass"
