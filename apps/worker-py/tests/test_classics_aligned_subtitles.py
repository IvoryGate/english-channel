from worker.classics.aligned_subtitles import split_source_cues, timed_source_cues


def test_short_source_stays_in_one_cue() -> None:
    cues = split_source_cues("A short sentence stays together.")
    assert len(cues) == 1
    assert cues[0]["sourceText"] == "A short sentence stays together."


def test_long_source_splits_to_at_most_two_lines() -> None:
    text = (
        "This deliberately long sentence contains enough words to require a split, "
        "but it should still preserve every source word in its original order."
    )
    cues = split_source_cues(text)
    assert len(cues) >= 2
    assert all(len(cue["text"].splitlines()) <= 2 for cue in cues)
    assert " ".join(cue["sourceText"] for cue in cues) == text


def test_word_timestamps_drive_split_boundary() -> None:
    words = [
        {"word": " One", "start": 0.2, "end": 0.5},
        {"word": " two", "start": 0.6, "end": 0.9},
        {"word": " three", "start": 1.0, "end": 1.4},
    ]
    cues = timed_source_cues("One two three.", "One two three.", words, offset=4.0, duration=2.0)
    assert cues[0]["start"] == 4.12
    assert cues[0]["end"] == 5.52
