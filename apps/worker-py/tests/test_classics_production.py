from pathlib import Path

from worker.classics.production import render_chapter_visuals


class _BookConfig:
    slug = "persuasion"
    visual = {"chapterThumbnails": {"4": "public/classics/persuasion/chapter-04.png"}}

    @staticmethod
    def repo_path(repo_root: Path, value: str) -> Path:
        return repo_root / value


def test_render_chapter_visuals_preserves_configured_thumbnail(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "public" / "classics" / "persuasion" / "chapter-04.png"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"reviewed-thumbnail")
    calls: list[list[str]] = []

    def fake_render(_repo_root: Path, arguments: list[str]) -> None:
        calls.append(arguments)

    monkeypatch.setattr("worker.classics.production._render", fake_render)

    result = render_chapter_visuals(tmp_path, _BookConfig(), [4])

    thumbnail = (
        tmp_path
        / "workspace"
        / "classics"
        / "persuasion"
        / "chapter_004"
        / "video"
        / "000_chapter_004.thumbnail.png"
    )
    assert thumbnail.read_bytes() == b"reviewed-thumbnail"
    assert len(calls) == 2
    assert all("PersuasionChapter4Cover" not in call for call in calls)
    assert result[0]["thumbnail"].endswith("000_chapter_004.thumbnail.png")
