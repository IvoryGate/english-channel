from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import BookConfig
from .io import read_json, sha256_file
from .paths import ClassicPaths
from .segment import normalize_coverage_text


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class PreflightReport:
    book_slug: str
    chapter: int
    checks: list[CheckResult]

    @property
    def ok(self) -> bool:
        return not any(check.status == "error" for check in self.checks)


def _file_hash_check(name: str, path: Path, expected: str) -> CheckResult:
    if not path.is_file():
        return CheckResult(name, "error", f"missing: {path}")
    actual = sha256_file(path)
    if actual != expected.lower():
        return CheckResult(name, "error", f"SHA-256 mismatch: expected {expected.lower()}, got {actual}")
    return CheckResult(name, "pass", f"{path} ({actual})")


def preflight_chapter(repo_root: Path, config: BookConfig, chapter: int) -> PreflightReport:
    checks: list[CheckResult] = []
    paths = ClassicPaths(repo_root, config.slug)
    if chapter < 1 or chapter > config.chapter_count:
        return PreflightReport(config.slug, chapter, [CheckResult("chapter", "error", "out of configured range")])
    source_epub = config.repo_path(repo_root, str(config.source["path"]))
    checks.append(_file_hash_check("source-epub", source_epub, str(config.source["sha256"])))
    checks.append(
        _file_hash_check(
            "voice-reference",
            config.repo_path(repo_root, str(config.voice["referencePath"])),
            str(config.voice["referenceSha256"]),
        )
    )
    if not paths.inventory.is_file():
        checks.append(CheckResult("inventory", "error", f"missing: {paths.inventory}"))
        return PreflightReport(config.slug, chapter, checks)
    inventory = read_json(paths.inventory)
    if int(inventory.get("chapterCount", 0)) != config.chapter_count:
        checks.append(CheckResult("inventory", "error", "chapter count does not match config"))
    else:
        checks.append(CheckResult("inventory", "pass", f"{config.chapter_count} chapters"))
    source_path = paths.source_text(chapter)
    manifest_path = paths.segments(chapter)
    if not source_path.is_file():
        checks.append(CheckResult("chapter-source", "error", f"missing: {source_path}"))
    else:
        checks.append(CheckResult("chapter-source", "pass", str(source_path)))
    if not manifest_path.is_file():
        checks.append(CheckResult("segment-manifest", "error", f"missing: {manifest_path}"))
    else:
        manifest: dict[str, Any] = read_json(manifest_path)
        segments = manifest.get("segments")
        if not isinstance(segments, list) or not segments:
            checks.append(CheckResult("segment-manifest", "error", "segments are missing"))
        elif any(item.get("voiceProfile") != config.voice["profileId"] for item in segments if isinstance(item, dict)):
            checks.append(CheckResult("single-voice", "error", "one or more segments route to another voice"))
        elif source_path.is_file() and normalize_coverage_text(source_path.read_text(encoding="utf-8")) != normalize_coverage_text(
            " ".join(str(item.get("displayText", "")) for item in segments)
        ):
            checks.append(CheckResult("source-coverage", "error", "segment display text does not cover chapter source"))
        else:
            checks.append(CheckResult("segment-manifest", "pass", f"{len(segments)} single-voice segments"))
            checks.append(CheckResult("source-coverage", "pass", "100% normalized ordered coverage"))
    model_path = config.runtime_path(repo_root, str(config.render["modelId"]))
    checks.append(CheckResult("model", "pass" if model_path.exists() else "error", str(model_path)))
    return PreflightReport(config.slug, chapter, checks)
