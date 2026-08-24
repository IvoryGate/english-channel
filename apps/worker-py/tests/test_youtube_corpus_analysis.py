from __future__ import annotations

import sys
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKER_ROOT))

ANALYSIS_SCRIPTS = Path(__file__).resolve().parents[3] / ".cursor" / "skills" / "youtube-corpus-analysis" / "scripts"
sys.path.insert(0, str(ANALYSIS_SCRIPTS))

from analyze_transcript_structure import analyze_transcript_record, topic_hits  # noqa: E402
from worker.youtube_podcast_research.workspace import composite_trend_score  # noqa: E402


def test_topic_hits_detects_workplace_cluster() -> None:
    topics = topic_hits("Work English", "Practice meetings and email", "Let's talk about your boss and office small talk.")

    assert "workplace" in topics


def test_composite_trend_score_includes_dual_host_component() -> None:
    score = composite_trend_score(
        {"view_count": 100_000, "like_count": 5000, "comment_count": 200, "upload_date": "20260101"},
        title="Leo and Mia Podcast: Daily English Conversation",
        description="Two hosts talk about natural English dialogue.",
    )

    assert score["trend_score"] > 0
    assert score["dual_host"]["likely_dual_host"] is True


def test_analyze_transcript_record_flags_hook_and_recap() -> None:
    record = {
        "channel": {"slug": "jandmaypodcast", "name": "J and May Podcast"},
        "metadata": {
            "id": "xyz",
            "webpage_url": "https://www.youtube.com/watch?v=xyz",
            "title": "Let's Talk English",
            "view_count": 999,
        },
        "description": "Subscribe for more.",
        "transcript": (
            "Welcome to today's episode. Let's talk about coffee English. "
            + "We will practice ordering and small talk at a cafe. "
            * 20
            + "Repeat after me: Could I get a latte, please? "
            + "That sounds more natural than give me coffee. "
            * 15
            + "Before we go, remember these key phrases. Subscribe and comment below."
        ),
    }

    analyzed = analyze_transcript_record(record)

    assert analyzed["opening_beats"]["hook"] >= 1
    assert analyzed["closing_beats"]["recap"] >= 1
