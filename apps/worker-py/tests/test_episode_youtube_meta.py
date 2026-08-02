from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / ".." / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS.resolve()))

from episode_youtube_meta import (  # noqa: E402
    derive_hook_text,
    hook_text_matches_title,
    sync_youtube_json,
)


def test_derive_hook_series_a_three_part_title() -> None:
    title = (
        "English Podcast For Daily Life Conversation | "
        "When Someone Asks About Your Dream Job | Learn English"
    )
    assert derive_hook_text(title, "series_a") == "When Someone Asks About Your Dream Job"


def test_derive_hook_series_b_em_dash_clause() -> None:
    title = (
        "Learn One Positive English Line — Not a Speech, Just One | "
        "Easy English Podcast A2-B1"
    )
    assert derive_hook_text(title, "series_b") == "Not a Speech, Just One"


def test_derive_hook_series_b_ep005_style() -> None:
    title = (
        "Talk About Confidence in English — Small Sentences, Not Big Speeches | "
        "Easy English Podcast A2-B1"
    )
    assert derive_hook_text(title, "series_b") == "Small Sentences, Not Big Speeches"


def test_derive_hook_series_c_keeps_full_first_segment() -> None:
    title = (
        "You Passed B2 — So Why Does English Still Feel Thin? | "
        "Polished English Podcast B2-C1"
    )
    assert (
        derive_hook_text(title, "series_c")
        == "You Passed B2 — So Why Does English Still Feel Thin?"
    )


def test_shorthand_hook_fails_consistency_check() -> None:
    title = (
        "Learn One Positive English Line — Not a Speech, Just One | "
        "Easy English Podcast A2-B1"
    )
    assert not hook_text_matches_title("One Line. Not a Speech.", title)
    assert hook_text_matches_title("Not a Speech, Just One", title)


def test_sync_youtube_json_overwrites_stale_hook(tmp_path: Path) -> None:
    episode_id = "episode_099"
    draft = tmp_path / f"000_{episode_id}.draft.md"
    draft.write_text(
        "Title: Learn One Positive English Line — Not a Speech, Just One | Easy English Podcast A2-B1\n\n---\n",
        encoding="utf-8",
    )
    youtube_path = tmp_path / f"000_{episode_id}.youtube.json"
    youtube_path.write_text(
        json.dumps(
            {
                "showId": "series_b",
                "hookText": "One Line. Not a Speech.",
                "title": "wrong title",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = sync_youtube_json(
        tmp_path,
        episode_id,
        manifest={"showId": "series_b", "title": extract_title(draft)},
        write=True,
    )
    assert report["changed"] is True
    assert report["hookText"] == "Not a Speech, Just One"
    saved = json.loads(youtube_path.read_text(encoding="utf-8"))
    assert saved["hookText"] == "Not a Speech, Just One"
    assert hook_text_matches_title(saved["hookText"], saved["title"])


def extract_title(draft_path: Path) -> str:
    from episode_youtube_meta import extract_draft_title

    return extract_draft_title(draft_path)
