from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / ".." / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS.resolve()))

from prepare_episode_youtube_packaging import (  # noqa: E402
    _ViewerChapterLabelBuilder,
    _parse_teaching_plan_threads,
    _programming_footer,
    assemble_description,
    auto_derive_markers_from_draft,
    resolve_video_intro_offset,
)


def test_programming_footer_is_added_to_description(tmp_path: Path) -> None:
    config = tmp_path / "configs" / "channel" / "programming.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        '{"schema":"youtube-channel-programming-v1","descriptionFooter":["First Steps: Tuesdays"]}',
        encoding="utf-8",
    )

    lines = _programming_footer(tmp_path)
    description = assemble_description(
        youtube={"description": "Practice one useful line."},
        markers=[],
        show_name="First Steps",
        level_band="A2-B1",
        schedule_lines=lines,
    )

    assert lines == ["First Steps: Tuesdays"]
    assert "📅 New episodes on a fixed schedule:" in description
    assert "First Steps: Tuesdays" in description


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


def test_branding_intro_offset_uses_composed_intro_duration(tmp_path: Path, monkeypatch) -> None:
    intro = tmp_path / "english-listening-room-intro.mp4"
    intro.touch()
    report = tmp_path / "000_episode_015.video_report.json"
    report.write_text(
        '{"branding":{"enabled":true,"introMp4":"' + str(intro).replace("\\", "\\\\") + '"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "prepare_episode_youtube_packaging._probe_media_duration",
        lambda path: 8.375,
    )

    offset, source = resolve_video_intro_offset({"videoReport": report})

    assert offset == 8.375
    assert source == "branding-intro-media"
