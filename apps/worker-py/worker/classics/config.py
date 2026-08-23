from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "classic-listening-book-v1"
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ConfigError(ValueError):
    pass


def _object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be an object")
    return value


def _string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class BookConfig:
    path: Path
    payload: dict[str, Any]
    book: dict[str, Any]
    source: dict[str, Any]
    release: dict[str, Any]
    voice: dict[str, Any]
    render: dict[str, Any]
    mastering: dict[str, Any]
    branding: dict[str, Any]
    visual: dict[str, Any]
    export: dict[str, Any]

    @property
    def slug(self) -> str:
        return str(self.book["slug"])

    @property
    def title(self) -> str:
        return str(self.book["title"])

    @property
    def author(self) -> str:
        return str(self.book["author"])

    @property
    def language(self) -> str:
        return str(self.book["language"])

    @property
    def chapter_count(self) -> int:
        return int(self.book["chapterCount"])

    def repo_path(self, repo_root: Path, value: str) -> Path:
        root = repo_root.resolve()
        candidate = (root / value).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ConfigError(f"Configured path escapes repository: {value}") from exc
        return candidate

    def runtime_path(self, repo_root: Path, value: str) -> Path:
        """Resolve a project-local runtime path without following directory junctions."""
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ConfigError(f"Runtime path must be project-relative: {value}")
        return repo_root.resolve() / relative


def parse_book_config(payload: dict[str, Any], path: Path) -> BookConfig:
    if payload.get("schema") != SCHEMA:
        raise ConfigError(f"Unsupported schema: {payload.get('schema')!r}")
    book = _object(payload, "book")
    source = _object(payload, "source")
    release = _object(payload, "release")
    voice = _object(payload, "voice")
    render = _object(payload, "render")
    mastering = _object(payload, "mastering")
    branding = _object(payload, "branding")
    visual = _object(payload, "visual")
    export = _object(payload, "export")

    slug = _string(book, "slug")
    if not SLUG_PATTERN.fullmatch(slug):
        raise ConfigError(f"Invalid book slug: {slug!r}")
    for key in ("title", "author", "language"):
        _string(book, key)
    chapter_count = book.get("chapterCount")
    if not isinstance(chapter_count, int) or chapter_count < 1:
        raise ConfigError("book.chapterCount must be a positive integer")
    for key in ("path", "sha256", "chapterHeadingPattern"):
        _string(source, key)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(source["sha256"])):
        raise ConfigError("source.sha256 must be a 64-character hexadecimal digest")
    if voice.get("mode") != "single":
        raise ConfigError("The pilot supports voice.mode=single only")
    for key in ("profileId", "referencePath", "referenceSha256", "globalControl", "acceptanceStatus"):
        _string(voice, key)
    if voice["acceptanceStatus"] not in {"approved", "blocked_electronic_texture", "review_required"}:
        raise ConfigError("voice.acceptanceStatus is invalid")
    for key in ("seriesPolicyRef", "programId"):
        _string(release, key)
    if not re.fullmatch(r"[0-9a-fA-F]{64}", str(voice["referenceSha256"])):
        raise ConfigError("voice.referenceSha256 must be a 64-character hexadecimal digest")
    try:
        re.compile(str(source["chapterHeadingPattern"]), flags=re.IGNORECASE)
    except re.error as exc:
        raise ConfigError(f"Invalid chapter heading pattern: {exc}") from exc
    markers = source.get("boilerplateStopMarkers")
    if not isinstance(markers, list) or not all(isinstance(item, str) and item for item in markers):
        raise ConfigError("source.boilerplateStopMarkers must be a non-empty string list")

    return BookConfig(
        path=path,
        payload=payload,
        book=book,
        source=source,
        release=release,
        voice=voice,
        render=render,
        mastering=mastering,
        branding=branding,
        visual=visual,
        export=export,
    )


def require_approved_voice(config: BookConfig) -> None:
    status = str(config.voice["acceptanceStatus"])
    if status != "approved":
        raise ConfigError(f"Voice provider is not approved: {status}")


def load_book_config(repo_root: Path, slug: str) -> BookConfig:
    if not SLUG_PATTERN.fullmatch(slug):
        raise ConfigError(f"Invalid book slug: {slug!r}")
    path = repo_root / "configs" / "classics" / f"{slug}.json"
    if not path.is_file():
        raise ConfigError(f"Book config not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ConfigError(f"Book config must contain a JSON object: {path}")
    config = parse_book_config(payload, path)
    if config.slug != slug:
        raise ConfigError(f"Config slug {config.slug!r} does not match requested slug {slug!r}")
    return config
