from __future__ import annotations

import sys
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKER_ROOT))

ANALYSIS_SCRIPTS = Path(__file__).resolve().parents[3] / ".cursor" / "skills" / "youtube-corpus-analysis" / "scripts"
SCRIPTWRITING_SCRIPTS = Path(__file__).resolve().parents[3] / ".cursor" / "skills" / "dialogue-podcast-scriptwriting" / "scripts"
sys.path.insert(0, str(ANALYSIS_SCRIPTS))
sys.path.insert(0, str(SCRIPTWRITING_SCRIPTS))

from worker.youtube_podcast_research.workspace import strip_vtt_to_text, write_json, write_text  # noqa: E402
from analyze_youtube_corpus import analyze_corpus, classify_title  # noqa: E402
from validate_podcast_script import validate_script_text  # noqa: E402


def test_strip_vtt_to_text_removes_timing_and_duplicates() -> None:
    raw = """WEBVTT

00:00:00.000 --> 00:00:01.000
<c>Hello learners.</c>

00:00:01.000 --> 00:00:02.000
<c>Hello learners.</c>

00:00:02.000 --> 00:00:03.000
Let's practice.
"""

    assert strip_vtt_to_text(raw) == "Hello learners.\nLet's practice."


def test_classify_title_detects_learning_patterns() -> None:
    labels = classify_title("5 Common English Phrases To Sound Natural In Conversation")

    assert "list" in labels
    assert "conversation" in labels
    assert "vocabulary" in labels


def test_analyze_corpus_summarizes_local_fixture(tmp_path: Path) -> None:
    video_root = tmp_path / "englishwithhopeee" / "videos" / "abc123"
    write_json(
        video_root / "metadata.json",
        {
            "id": "abc123",
            "webpage_url": "https://www.youtube.com/watch?v=abc123",
            "title": "Stop Saying I'm Fine In English Conversation",
            "view_count": 12345,
        },
    )
    write_text(video_root / "description.txt", "Practice natural answers. Comment your sentence below.")
    write_text(video_root / "transcript.txt", "Host one explains a phrase. Host two practices the phrase.")

    analysis = analyze_corpus(tmp_path)

    assert analysis["video_count"] == 1
    assert analysis["transcript_count"] == 1
    assert analysis["channels"]["englishwithhopeee"]["video_count"] == 1
    assert analysis["channels"]["englishwithhopeee"]["description_ctas"]["comment"] == 1


def test_validate_script_text_requires_two_hosts_and_cta() -> None:
    script = """Title: Natural Coffee English
Description: Practice ordering coffee naturally.
Mia: Today we practice ordering coffee.
Leo: Repeat this line with us.
Mia: Could I get a latte, please?
Leo: Great. Comment your own coffee order below.
"""

    result = validate_script_text(script, min_words=5, max_words=200)

    assert result["ok"] is True
    assert result["host_turns"] == {"Mia": 2, "Leo": 2}


def test_validate_series_b_profile_spoken_word_count() -> None:
    body = " ".join(["practice english alone every day"] * 320)
    script = f"""Title: Practice Alone
Description: A simple plan for solo practice. Try it today and comment below.
[Episode Contract]
Riley: By the end you will have a simple plan.
Sam: {body}
Riley: Subscribe if this helped.
"""

    result = validate_script_text(script, min_words=1400, max_words=1900, profile="series_b")

    assert result["profile"] == "series_b"
    assert result["word_count"] >= 1400


def test_validate_series_b_requires_episode_contract_marker() -> None:
    script = """Title: Practice Alone
Description: Try today.
Sam: Hello.
Riley: Hi.
Sam: Help me practice and subscribe.
Riley: Sure.
"""

    result = validate_script_text(script, min_words=5, max_words=200, profile="series_b")

    assert result["ok"] is False
    assert any(issue["code"] == "SERIES_B_STRUCTURE" for issue in result["issues"])


def test_is_rate_limit_error_detects_youtube_message() -> None:
    from worker.youtube_podcast_research.rate_limit import guard_rate_limit, is_rate_limit_error

    assert is_rate_limit_error("Video unavailable. rate-limited by YouTube for up to an hour")
    try:
        guard_rate_limit(Exception("HTTP Error 429: Too Many Requests"))
    except Exception as exc:
        assert exc.__class__.__name__ == "YouTubeRateLimitError"
    else:
        raise AssertionError("expected YouTubeRateLimitError")


def test_dual_host_signals_detects_podcast_shape() -> None:
    from worker.youtube_podcast_research.workspace import dual_host_signals

    signals = dual_host_signals(
        "English Podcast: Leo and Mia Talk About Work English",
        "Join us for a conversation between two hosts about office phrases.",
    )

    assert signals["likely_dual_host"] is True
