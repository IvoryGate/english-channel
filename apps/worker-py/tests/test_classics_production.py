import json
from pathlib import Path

from worker.classics.chapter_package import CHAPTER_COPY
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


class _FallbackBookConfig:
    slug = "persuasion"
    visual: dict[str, object] = {}


def test_render_chapter_visuals_renders_fallback_thumbnail(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[list[str]] = []

    def fake_render(_repo_root: Path, arguments: list[str]) -> None:
        calls.append(arguments)

    monkeypatch.setattr("worker.classics.production._render", fake_render)

    result = render_chapter_visuals(tmp_path, _FallbackBookConfig(), [5])

    assert len(calls) == 3
    assert any("PersuasionChapter5Cover" in call for call in calls)
    assert result[0]["thumbnail"].endswith("000_chapter_005.thumbnail.png")


def test_all_persuasion_compositions_and_next_week_assets_are_registered() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    root = (repo_root / "src" / "classics" / "root.tsx").read_text(encoding="utf-8")
    card = (repo_root / "src" / "classics" / "classic-listening-card.tsx").read_text(encoding="utf-8")
    cover = (repo_root / "src" / "classics" / "persuasion-chapter-cover.tsx").read_text(encoding="utf-8")

    assert "Array.from({length: 24}" in root
    assert "chapter: number" in card
    assert "chapter-07-cover-bg-v1-imagegen.png" in cover
    assert "chapter-08-cover-bg-v1-imagegen.png" in cover
    assert "chapter-09-cover-bg-v1-imagegen.png" in cover
    config = json.loads((repo_root / "configs" / "classics" / "persuasion.json").read_text(encoding="utf-8"))
    assert config["visual"]["chapterBackgrounds"]["7"].endswith("chapter-07-cover-bg-v1-imagegen.png")
    assert config["visual"]["chapterBackgrounds"]["8"].endswith("chapter-08-cover-bg-v1-imagegen.png")
    assert config["visual"]["chapterBackgrounds"]["9"].endswith("chapter-09-cover-bg-v1-imagegen.png")
    assert CHAPTER_COPY[7]["hook"] == "He Sees Her Again"
    assert CHAPTER_COPY[8]["hook"] == "Worse Than Strangers"
    assert CHAPTER_COPY[9]["hook"] == "One Small Kindness"
