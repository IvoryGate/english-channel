from pathlib import Path

import pytest

from worker.classics.chapter_package import (
    CHAPTER_COPY,
    ChapterPackageError,
    _normalized_concat_command,
    _shift_srt_timeline,
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


def test_youtube_captions_shift_body_timeline_by_intro_duration() -> None:
    source = "1\n00:00:00,000 --> 00:00:01,250\nMr Shepherd spoke.\n"

    shifted = _shift_srt_timeline(source, 10.048)

    assert "00:00:10,048 --> 00:00:11,298" in shifted
    assert "Mr Shepherd spoke." in shifted


def test_youtube_caption_offset_cannot_be_negative() -> None:
    with pytest.raises(ChapterPackageError, match="cannot be negative"):
        _shift_srt_timeline(
            "1\n00:00:00,000 --> 00:00:01,000\nText.\n", -0.001
        )


def test_final_composition_normalizes_timestamps_and_reencodes() -> None:
    command = _normalized_concat_command(
        [Path("intro.mp4"), Path("body.mp4"), Path("outro.mp4")],
        Path("final.mp4"),
    )
    rendered = " ".join(command)

    assert rendered.count("settb=AVTB") == 3
    assert rendered.count(",setpts=PTS-STARTPTS") == 3
    assert rendered.count("asetpts=PTS-STARTPTS") == 3
    assert "concat=n=3:v=1:a=1" in rendered
    assert "libx264" in command
    assert "aac" in command
    assert "-f concat" not in rendered
    assert "-c copy" not in rendered


def test_reviewed_youtube_titles_fit_limit() -> None:
    for chapter, copy in CHAPTER_COPY.items():
        title = f"Persuasion Chapter {chapter}: {copy['hook']} | Jane Austen Full Audiobook"
        assert len(title) <= 100


def test_youtube_package_does_not_duplicate_canonical_video(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from worker.classics import chapter_package as package
    from worker.classics.paths import ClassicPaths

    config = SimpleNamespace(slug="persuasion", title="Persuasion", author="Jane Austen")
    paths = ClassicPaths(tmp_path, config.slug)
    captions = paths.subtitles_dir(12) / "youtube.srt"
    for path in (paths.final_video(12), paths.thumbnail(12), paths.source_text(12),
                 paths.subtitle_srt(12), captions):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"canonical fixture")
    monkeypatch.setattr(package, "_probe", lambda *args: {"format": {"duration": "600"}})
    monkeypatch.setattr(package, "_validate_composed_video", lambda *args: {"status": "pass"})
    monkeypatch.setattr(package, "_write_youtube_captions", lambda *args: captions)
    monkeypatch.setattr(package, "channel_description_footer", lambda *args: "Channel schedule")
    result = package.write_youtube_package(tmp_path, config, 12)
    export = result["exportDirectory"]
    assert not list(export.glob("*.mp4"))
    assert paths.final_video(12).read_bytes() == b"canonical fixture"
    assert result["youtube"]["video"] == paths.final_video(12).relative_to(tmp_path).as_posix()
    assert result["youtube"]["video"] in (export / "upload-checklist.md").read_text(encoding="utf-8")


def test_chapter_four_copy_matches_the_thumbnail_promise() -> None:
    assert CHAPTER_COPY[4]["hook"] == "The Broken Engagement"
    assert "Frederick Wentworth" in CHAPTER_COPY[4]["summary"]
    assert CHAPTER_COPY[5]["hook"] == "Left Behind, Still Needed"
    assert "Uppercross" in CHAPTER_COPY[5]["summary"]
    assert CHAPTER_COPY[10]["hook"] == "He Could Not See Her Suffer"
    assert "Winthrop" in CHAPTER_COPY[10]["summary"]
    assert CHAPTER_COPY[11]["hook"] == "A New World at Lyme"
    assert "Captain Benwick" in CHAPTER_COPY[11]["summary"]
    assert CHAPTER_COPY[13]["hook"] == "He Asked About Her"
    assert "Crofts" in CHAPTER_COPY[13]["summary"]
    assert "enquired after her" in CHAPTER_COPY[13]["summary"]


def test_classic_description_uses_channel_owned_schedule() -> None:
    footer = channel_description_footer(REPO)

    assert "Classic Listening: Mondays and Saturdays at 8:00 AM" in footer
    assert "New Shorts: every day at 9:30 AM, 1:00 PM, 5:00 PM, and 10:00 PM" in footer
