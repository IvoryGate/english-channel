from worker.classics.chapter_package import CHAPTER_COPY, _subtitle_chunks, _timestamp


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
