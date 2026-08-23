from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest

from worker.classics.config import ConfigError, load_book_config, parse_book_config, require_approved_voice
from worker.classics.epub_ingest import IngestError, ingest_book
from worker.classics.io import sha256_file
from worker.classics.paths import ClassicPaths
from worker.classics.preflight import preflight_chapter
from worker.classics.run_state import RunStateStore
from worker.classics.segment import normalize_coverage_text


def _write_epub(path: Path) -> None:
    container = """<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""
    opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <manifest>
    <item id="title" href="title.xhtml" media-type="application/xhtml+xml"/>
    <item id="one" href="one.xhtml" media-type="application/xhtml+xml"/>
    <item id="two" href="two.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="title"/><itemref idref="one"/><itemref idref="two"/></spine>
</package>"""
    title = '<html xmlns="http://www.w3.org/1999/xhtml"><body><h1>Fixture</h1></body></html>'
    one = """<html xmlns="http://www.w3.org/1999/xhtml"><body>
<h2>CHAPTER I.</h2><p>First sentence.</p><p>“A quoted sentence,” she said.</p>
</body></html>"""
    two = """<html xmlns="http://www.w3.org/1999/xhtml"><body>
<h2>CHAPTER II.</h2><p>The actual ending.</p>
<p>*** END OF THE PROJECT GUTENBERG EBOOK FIXTURE ***</p>
<h2>THE FULL PROJECT GUTENBERG LICENSE</h2><p>This must not be narrated.</p>
</body></html>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=ZIP_STORED)
        archive.writestr("META-INF/container.xml", container, compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/content.opf", opf, compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/title.xhtml", title, compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/one.xhtml", one, compress_type=ZIP_DEFLATED)
        archive.writestr("OEBPS/two.xhtml", two, compress_type=ZIP_DEFLATED)


def _payload(source_path: str, source_hash: str) -> dict[str, object]:
    return {
        "schema": "classic-listening-book-v1",
        "book": {"slug": "fixture", "title": "Fixture", "author": "Author", "language": "en", "chapterCount": 2},
        "source": {
            "path": source_path,
            "sha256": source_hash,
            "chapterHeadingPattern": r"^CHAPTER\s+([IVXLCDM]+)\.?$",
            "boilerplateStopMarkers": ["*** END OF THE PROJECT GUTENBERG EBOOK FIXTURE ***", "THE FULL PROJECT GUTENBERG LICENSE"],
        },
        "release": {
            "seriesPolicyRef": "configs/classics/series.json",
            "programId": "classic-listening-baseline",
        },
        "voice": {
            "mode": "single",
            "profileId": "classic-listening-riley-narrator",
            "acceptanceStatus": "approved",
            "referencePath": "assets/riley.wav",
            "referenceSha256": "1" * 64,
            "globalControl": "same narrator",
            "narrationCue": "narration",
            "dialogueCue": "dialogue",
            "cfgValue": 2.35,
            "inferenceTimesteps": 10,
        },
        "render": {"interSegmentSilenceSec": 0.34, "shortSegmentWordThreshold": 12},
        "mastering": {},
        "branding": {},
        "visual": {},
        "export": {},
    }


def test_loads_persuasion_config() -> None:
    repo = Path(__file__).resolve().parents[3]
    config = load_book_config(repo, "persuasion")
    assert config.chapter_count == 24
    assert config.voice["profileId"] == "classic-listening-riley-narrator"
    assert config.voice["mode"] == "single"
    assert config.voice["acceptanceStatus"] == "blocked_electronic_texture"
    assert config.release["programId"] == "classic-listening-baseline"
    assert config.branding["primaryAudience"] == "women aged 55 and over"
    assert config.branding["introVoicePath"].endswith("classic-listening-intro-voice-v4.wav")
    assert config.branding["outroVoicePath"].endswith("classic-listening-outro-voice-v5b.wav")
    assert config.branding["introSpokenText"].startswith("Welcome to Classic Listening")

    with pytest.raises(ConfigError, match="blocked_electronic_texture"):
        require_approved_voice(config)


def test_classics_branding_uses_voice_and_contains_no_emoji() -> None:
    repo = Path(__file__).resolve().parents[3]
    source = (repo / "src" / "classics" / "classic-listening-card.tsx").read_text(encoding="utf-8")
    root = (repo / "src" / "classics" / "root.tsx").read_text(encoding="utf-8")
    assert "branding/chapter-" in root
    assert "voiceFile" in source
    assert "OpenBook" not in source
    assert "BEGIN CHAPTER ${chapterWord(chapter)}" in source
    assert "SUBSCRIBE AND CONTINUE" in source
    assert "✦" not in source


def test_rejects_unsafe_slug() -> None:
    with pytest.raises(ConfigError):
        ClassicPaths(Path("."), "../escape")


def test_runtime_path_allows_project_junction_without_parent_traversal(tmp_path: Path) -> None:
    config = parse_book_config(_payload("fixture.epub", "0" * 64), tmp_path / "fixture.json")

    assert config.runtime_path(tmp_path, "pretrained_models/VoxCPM2") == (
        tmp_path.resolve() / "pretrained_models" / "VoxCPM2"
    )
    with pytest.raises(ConfigError):
        config.runtime_path(tmp_path, "../shared-model")


def test_preflight_reports_blocked_voice_before_gpu_work(tmp_path: Path) -> None:
    payload = _payload("fixture.epub", "0" * 64)
    payload["voice"]["acceptanceStatus"] = "blocked_electronic_texture"  # type: ignore[index]
    config = parse_book_config(payload, tmp_path / "fixture.json")

    report = preflight_chapter(tmp_path, config, 1)

    voice_check = next(check for check in report.checks if check.name == "voice-acceptance")
    assert voice_check.status == "error"
    assert voice_check.detail == "blocked_electronic_texture"


def test_ingests_spine_chapters_and_strips_license(tmp_path: Path) -> None:
    epub = tmp_path / "fixture.epub"
    _write_epub(epub)
    payload = _payload("fixture.epub", sha256_file(epub))
    config = parse_book_config(payload, tmp_path / "fixture.json")
    inventory = ingest_book(tmp_path, config)
    paths = ClassicPaths(tmp_path, "fixture")
    assert inventory["chapterCount"] == 2
    assert inventory["source"]["spineItemCount"] == 3
    assert paths.source_text(1).read_text(encoding="utf-8") == "First sentence.\n\n“A quoted sentence,” she said.\n"
    chapter_two = paths.source_text(2).read_text(encoding="utf-8")
    assert chapter_two == "The actual ending.\n"
    assert "LICENSE" not in chapter_two
    assert "must not be narrated" not in chapter_two

    manifest = json.loads(paths.segments(1).read_text(encoding="utf-8"))
    assert {segment["voiceProfile"] for segment in manifest["segments"]} == {"classic-listening-riley-narrator"}
    assert {segment["filename"] for segment in manifest["segments"]} == {"001_narrator.wav", "002_narrator.wav"}
    assert normalize_coverage_text(" ".join(segment["displayText"] for segment in manifest["segments"])) == normalize_coverage_text(
        paths.source_text(1).read_text(encoding="utf-8")
    )


def test_ingest_rejects_source_hash_change(tmp_path: Path) -> None:
    epub = tmp_path / "fixture.epub"
    _write_epub(epub)
    config = parse_book_config(_payload("fixture.epub", "0" * 64), tmp_path / "fixture.json")
    with pytest.raises(IngestError, match="SHA-256 mismatch"):
        ingest_book(tmp_path, config)


def test_run_state_is_persisted_atomically(tmp_path: Path) -> None:
    store = RunStateStore(tmp_path / "state.json")
    store.write({"status": "RUNNING", "phase": "INGEST"})
    updated = store.update(status="READY", phase="INGESTED")
    assert updated["status"] == "READY"
    assert store.read()["phase"] == "INGESTED"
    assert not list(tmp_path.glob("*.tmp"))
