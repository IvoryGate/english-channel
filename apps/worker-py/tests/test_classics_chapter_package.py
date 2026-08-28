from pathlib import Path

from worker.classics.chapter_package import (
    CHAPTER_COPY,
    _subtitle_chunks,
    _timestamp,
    channel_description_footer,
)


REPO = Path(__file__).resolve().parents[3]


def test_subtitle_chunks_preserve_text_and_duration() -> None:
    source = "Anne Elliot listened quietly while the others decided what her future should be."
    chunks = _subtitle_chunks(source, 8.4)

    assert " ".join(text.replace("\n", " ") for text, _ in chunks) == source
    assert abs(sum(duration for _, duration in chunks) - 8.4) < 0.001
    assert all(duration > 0 for _, duration in chunks)


def test_timestamp_formats_are_stable() -> None:
    assert _timestamp(62.345, srt=True) == "00:01:02,345"
    assert _timestamp(62.345) == "00:01:02.345"


def test_first_three_youtube_titles_fit_limit() -> None:
    for chapter, copy in CHAPTER_COPY.items():
        title = f"Persuasion Chapter {chapter}: {copy['hook']} | Jane Austen Full Audiobook"
        assert len(title) <= 100


def test_classic_description_uses_channel_owned_schedule() -> None:
    footer = channel_description_footer(REPO)

    assert "Classic Listening: Mondays and Thursdays at 8:00 AM" in footer
    assert "New Shorts: every day at 12:30 PM and 6:00 PM" in footer
