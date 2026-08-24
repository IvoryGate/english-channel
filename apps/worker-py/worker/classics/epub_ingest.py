from __future__ import annotations

import posixpath
import re
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

from .config import BookConfig
from .io import atomic_write_json, atomic_write_text, sha256_file, sha256_text
from .paths import ClassicPaths, chapter_id
from .segment import build_segment_manifest


class IngestError(RuntimeError):
    pass


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _member_path(opf_name: str, href: str) -> str:
    value = posixpath.normpath(posixpath.join(posixpath.dirname(opf_name), href))
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise IngestError(f"Unsafe EPUB member path: {href}")
    return value


def _opf_and_spine(archive: ZipFile) -> tuple[str, list[str]]:
    try:
        container = ET.fromstring(archive.read("META-INF/container.xml"))
    except (KeyError, ET.ParseError) as exc:
        raise IngestError("EPUB container.xml is missing or invalid") from exc
    rootfiles = [item.attrib.get("full-path", "") for item in container.iter() if _local_name(item.tag) == "rootfile"]
    if len(rootfiles) != 1 or not rootfiles[0]:
        raise IngestError(f"Expected one EPUB rootfile, found {rootfiles!r}")
    opf_name = rootfiles[0]
    try:
        package = ET.fromstring(archive.read(opf_name))
    except (KeyError, ET.ParseError) as exc:
        raise IngestError(f"EPUB package is missing or invalid: {opf_name}") from exc
    manifest = {
        item.attrib["id"]: item.attrib["href"]
        for item in package.iter()
        if _local_name(item.tag) == "item" and item.attrib.get("id") and item.attrib.get("href")
    }
    spine: list[str] = []
    for item in package.iter():
        if _local_name(item.tag) != "itemref":
            continue
        idref = item.attrib.get("idref", "")
        if idref not in manifest:
            raise IngestError(f"Spine idref is missing from manifest: {idref}")
        spine.append(_member_path(opf_name, manifest[idref]))
    if not spine:
        raise IngestError("EPUB spine is empty")
    return opf_name, spine


def _xhtml_blocks(value: bytes, member: str) -> list[tuple[str, str]]:
    try:
        document = ET.fromstring(value)
    except ET.ParseError as exc:
        raise IngestError(f"Invalid XHTML in EPUB member: {member}") from exc
    body = next((item for item in document.iter() if _local_name(item.tag) == "body"), None)
    if body is None:
        return []
    blocks: list[tuple[str, str]] = []
    for item in body.iter():
        tag = _local_name(item.tag)
        if tag not in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li"}:
            continue
        text = re.sub(r"\s+", " ", "".join(item.itertext())).strip()
        if text:
            blocks.append((tag, text))
    return blocks


def _chapter_from_blocks(
    blocks: list[tuple[str, str]],
    heading_pattern: re.Pattern[str],
    stop_markers: list[str],
) -> tuple[str, str] | None:
    heading_index = next(
        (index for index, (tag, text) in enumerate(blocks) if tag.startswith("h") and heading_pattern.fullmatch(text)),
        None,
    )
    if heading_index is None:
        return None
    heading = blocks[heading_index][1]
    body: list[str] = []
    stop = False
    for _tag, text in blocks[heading_index + 1 :]:
        for marker in stop_markers:
            marker_index = text.find(marker)
            if marker_index >= 0:
                prefix = text[:marker_index].strip()
                if prefix:
                    body.append(prefix)
                stop = True
                break
        if stop:
            break
        body.append(text)
    chapter_text = "\n\n".join(body).strip()
    if not chapter_text:
        raise IngestError(f"Chapter has no body text: {heading}")
    return heading, chapter_text


def _word_count(value: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+(?:[’'-][A-Za-z]+)*\b", value))


def ingest_book(repo_root: Path, config: BookConfig, *, force: bool = False) -> dict[str, Any]:
    source_path = config.repo_path(repo_root, str(config.source["path"]))
    if not source_path.is_file():
        raise IngestError(f"Source EPUB not found: {source_path}")
    actual_hash = sha256_file(source_path)
    expected_hash = str(config.source["sha256"]).lower()
    if actual_hash != expected_hash:
        raise IngestError(f"Source SHA-256 mismatch: expected {expected_hash}, got {actual_hash}")
    try:
        archive = ZipFile(source_path)
    except BadZipFile as exc:
        raise IngestError(f"Source is not a valid EPUB/ZIP: {source_path}") from exc

    heading_pattern = re.compile(str(config.source["chapterHeadingPattern"]), flags=re.IGNORECASE)
    stop_markers = [str(item) for item in config.source["boilerplateStopMarkers"]]
    chapters: list[dict[str, Any]] = []
    try:
        mime = archive.read("mimetype").decode("ascii", errors="replace").strip()
        if mime != "application/epub+zip":
            raise IngestError(f"Unexpected EPUB MIME marker: {mime!r}")
        opf_name, spine = _opf_and_spine(archive)
        for member in spine:
            try:
                blocks = _xhtml_blocks(archive.read(member), member)
            except KeyError as exc:
                raise IngestError(f"Spine member is missing: {member}") from exc
            result = _chapter_from_blocks(blocks, heading_pattern, stop_markers)
            if result is None:
                continue
            heading, text = result
            number = len(chapters) + 1
            chapters.append(
                {
                    "number": number,
                    "chapterId": chapter_id(number),
                    "heading": heading,
                    "sourceMember": member,
                    "wordCount": _word_count(text),
                    "sourceSha256": sha256_text(text + "\n"),
                    "text": text,
                }
            )
    finally:
        archive.close()

    if len(chapters) != config.chapter_count:
        raise IngestError(f"Expected {config.chapter_count} chapters, extracted {len(chapters)}")

    paths = ClassicPaths(repo_root, config.slug)
    inventory_chapters: list[dict[str, Any]] = []
    for chapter in chapters:
        number = int(chapter["number"])
        source_output = paths.source_text(number)
        manifest_output = paths.segments(number)
        if not force and (source_output.exists() or manifest_output.exists()):
            raise IngestError(f"Chapter output already exists; use --force: {paths.chapter(number)}")
        text = str(chapter.pop("text"))
        atomic_write_text(source_output, text)
        manifest = build_segment_manifest(config, number, text)
        atomic_write_json(manifest_output, manifest)
        item = dict(chapter)
        item["sourcePath"] = source_output.relative_to(repo_root).as_posix()
        item["manifestPath"] = manifest_output.relative_to(repo_root).as_posix()
        item["segmentCount"] = len(manifest["segments"])
        inventory_chapters.append(item)

    inventory: dict[str, Any] = {
        "schema": "classic-listening-inventory-v1",
        "bookSlug": config.slug,
        "title": config.title,
        "author": config.author,
        "language": config.language,
        "source": {
            "path": str(config.source["path"]),
            "sha256": actual_hash,
            "provider": config.source.get("provider"),
            "ebookId": config.source.get("ebookId"),
            "pageUrl": config.source.get("pageUrl"),
            "publicDomainStatement": config.source.get("publicDomainStatement"),
            "opfPath": opf_name,
            "spineItemCount": len(spine),
        },
        "chapterCount": len(inventory_chapters),
        "totalWordCount": sum(int(item["wordCount"]) for item in inventory_chapters),
        "chapters": inventory_chapters,
    }
    atomic_write_json(paths.inventory, inventory)
    production = {
        "schema": "classic-listening-production-v1",
        "bookSlug": config.slug,
        "voiceMode": config.voice["mode"],
        "voiceProfile": config.voice["profileId"],
        "referencePath": config.voice["referencePath"],
        "referenceSha256": str(config.voice["referenceSha256"]).lower(),
        "chapterState": {chapter_id(number): "INGESTED" for number in range(1, config.chapter_count + 1)},
    }
    atomic_write_json(paths.production, production)
    return inventory
