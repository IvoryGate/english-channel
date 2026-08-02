from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / ".." / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS.resolve()))

from prepare_episode_youtube_packaging import (  # noqa: E402
    _ViewerChapterLabelBuilder,
    _parse_teaching_plan_threads,
    auto_derive_markers_from_draft,
)


def test_parse_teaching_plan_threads_series_a_style() -> None:
    draft = """
[Teaching Plan]
- Thread 1, real conversations start mid-stream, you rarely get a clean hello.
- Thread 2, why learners wait at the starting line, textbooks begin at line one.
"""
    threads = _parse_teaching_plan_threads(draft)
    assert threads == [
        "real conversations start mid-stream",
        "why learners wait at the starting line",
    ]


def test_viewer_labels_never_use_internal_headers() -> None:
    draft = """
[Teaching Plan]
- Thread 1, real conversations start mid-stream, you rarely get a clean hello.
- Thread 2, why learners wait at the starting line, textbooks begin at line one.
- Thread 3, follow-up bridges to join in, short reactions when talk is moving.
- Thread 4, permission to join imperfectly, get the gist before perfect sentences.

[Micro-Pocket]
After the second teaching beat, mid-stream and join in replayed slowly.

[Recycle]
Ethan worries he must catch every word before he can jump in.

[Word Tour]
Nine phrases replayed at the end.

Key Phrases: mid-stream, join in, follow-up bridge, catch up, jump in

---

## Intro Hook — 起
Nora: Hello.

## Teaching Dialogue — 承
Nora: First idea.

## Micro-Pocket
Nora: Slow replay.

## Teaching Dialogue — 承 (continued)
Nora: Third idea.

## Recycle — conflict
Ethan: Pushback.

## Word Tour — 转
Nora: Tour.

## Recap And CTA — 合
Nora: Bye.
"""
    manifest = {
        "showId": "series_a",
        "description": "Join talk already in progress.",
        "turns": [{"id": f"p{i:03d}", "order": i} for i in range(1, 8)],
    }
    youtube = {"hookText": "When Everyone Is Already Talking"}
    builder = _ViewerChapterLabelBuilder(draft_text=draft, youtube=youtube, manifest=manifest)
    labels = [
        builder.label_for("## Intro Hook — 起"),
        builder.label_for("## Teaching Dialogue — 承"),
        builder.label_for("## Micro-Pocket"),
        builder.label_for("## Teaching Dialogue — 承 (continued)"),
        builder.label_for("## Recycle — conflict"),
        builder.label_for("## Word Tour — 转"),
        builder.label_for("## Recap And CTA — 合"),
    ]
    assert labels[0] == "When Everyone Is Already Talking"
    assert labels[1] == "real conversations start mid-stream"
    assert labels[2].startswith("Slow replay:")
    assert "mid-stream" in labels[2]
    assert labels[3] == "follow-up bridges to join in"
    assert "catch every word" in labels[4]
    assert "mid-stream" in labels[5]
    assert labels[6] == "Recap & your practice"
    assert "Teaching Dialogue" not in " ".join(labels)
    assert "Intro Hook" not in " ".join(labels)


def test_auto_derive_markers_maps_turn_ids(tmp_path: Path) -> None:
    draft_path = tmp_path / "000_episode_001.draft.md"
    draft_path.write_text(
        """
[Teaching Plan]
- Thread 1, quiet confidence sounds different from loud voice.

---

## Intro Hook — 起
Riley: Hi.

## Teaching Dialogue — 承
Riley: Part one.
""",
        encoding="utf-8",
    )
    manifest = {
        "showId": "series_b",
        "turns": [{"id": "p001", "order": 1}, {"id": "p002", "order": 2}],
    }
    markers = auto_derive_markers_from_draft(
        draft_path,
        manifest,
        youtube={"hookText": "One small sentence"},
    )
    assert markers == [
        {"turnId": "p001", "label": "One small sentence"},
        {"turnId": "p002", "label": "quiet confidence sounds different from loud voice"},
    ]
