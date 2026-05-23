from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path

from audiobook_workspace import (
    DEFAULT_GLOBAL_CONTROL,
    chapter_id,
    clean_reference_path,
    ensure_segment_defaults,
    manifest_path,
    segment_filename,
    source_text_path,
    speaker_slug,
    word_count,
    workspace_path,
    write_json,
)


def html_to_plain(raw: str) -> str:
    raw = re.sub(r"<script.*?</script>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"</?(?:p|div|br|h\d|li|blockquote|section)[^>]*>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if lines and lines[-1] != "" and len(line.split()) <= 2 and not re.search(r"[.!?:;\"']\s*$", line):
            lines[-1] = f"{lines[-1]} {line}"
        else:
            lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def read_epub_chapter_file(path: Path, chapter: int) -> str | None:
    roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    markers = [rf"\bchapter\s+{chapter}\b"]
    if chapter < len(roman):
        markers.append(rf"\bchapter\s+{roman[chapter]}\b")
    best: tuple[int, str] | None = None
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith((".xhtml", ".html", ".htm")):
                continue
            raw = archive.read(name).decode("utf-8", errors="ignore")
            if not any(re.search(marker, raw, flags=re.I) for marker in markers):
                continue
            text = html_to_plain(raw)
            for marker in markers:
                match = re.search(marker, text, flags=re.I)
                if match:
                    text = text[match.end() :].strip()
                    break
            else:
                continue
            next_match = re.search(r"\bchapter\s+([ivxlcdm]+|\d+)\b", text, flags=re.I)
            if next_match:
                text = text[: next_match.start()].strip()
            if len(text) < 200:
                continue
            if best is None or len(text) > best[0]:
                best = (len(text), text)
    return best[1] if best else None


def read_epub_text(path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith((".xhtml", ".html", ".htm"))]
        for name in names:
            raw = archive.read(name).decode("utf-8", errors="ignore")
            parts.append(html_to_plain(raw))
    return "\n\n".join(parts)


def read_source(path: Path) -> str:
    if path.suffix.lower() == ".epub":
        return read_epub_text(path)
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_chapter(text: str, chapter: int) -> str:
    roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    markers = [rf"chapter\s+{chapter}\b"]
    if chapter < len(roman):
        markers.append(rf"chapter\s+{roman[chapter]}\b")
    start_match = None
    for marker in markers:
        match = re.search(marker, text, flags=re.I)
        if match and (start_match is None or match.start() < start_match.start()):
            start_match = match
    if not start_match:
        return text.strip()

    rest = text[start_match.end() :]
    next_match = re.search(r"\bchapter\s+([ivxlcdm]+|\d+)\b", rest, flags=re.I)
    chapter_text = rest[: next_match.start()] if next_match else rest
    return re.sub(r"\n{3,}", "\n\n", chapter_text).strip()


def unclosed_dialogue_quotes(text: str) -> bool:
    if text.count('"') % 2 == 1:
        return True
    for left, right in (("\u201c", "\u201d"), ("\u2018", "\u2019")):
        if text.count(left) > text.count(right):
            return True
    return False


def is_dialogue_continuation(previous: str, sentence: str) -> bool:
    if unclosed_dialogue_quotes(previous):
        return True
    if previous.rstrip().endswith((';', ',')) and sentence[:1].islower():
        return True
    if previous.rstrip().endswith(';') and sentence.startswith(
        ("that ", "and ", "but ", "which ", "who ", "when ", "where ")
    ):
        return True
    return False


def merge_dialogue_turns(sentences: list[str]) -> list[str]:
    merged: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if merged and is_dialogue_continuation(merged[-1], sentence):
            merged[-1] = f"{merged[-1]} {sentence}"
        else:
            merged.append(sentence)
    return merged


def draft_segments(text: str) -> list[dict[str, object]]:
    paragraphs = [re.sub(r"\s+", " ", item).strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
    segments = []
    order = 1
    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        for sentence in merge_dialogue_turns(sentences):
            speaker = "narrator"
            kind = "narration"
            if sentence.startswith(('"', "\u201c")):
                kind = "dialogue"
                speaker = "unknown_speaker"
            words = word_count(sentence)
            segments.append(
                {
                    "id": f"{order:03d}",
                    "order": order,
                    "filename": segment_filename(order, speaker),
                    "kind": kind,
                    "speaker": speaker,
                    "deliveryCue": "plain understated narration" if kind == "narration" else "restrained dialogue delivery",
                    "text": sentence,
                    "wordCount": words,
                }
            )
            order += 1
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(description="Draft a chapter source and segment manifest.")
    parser.add_argument("--book", required=True)
    parser.add_argument("--chapter", required=True, type=int)
    parser.add_argument("--source", required=True)
    parser.add_argument("--workspace-root", default="workspace")
    parser.add_argument("--reference")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    workspace = workspace_path(args.book, args.chapter, args.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    source_path_arg = Path(args.source)
    if source_path_arg.suffix.lower() == ".epub":
        chapter_text = read_epub_chapter_file(source_path_arg, args.chapter)
        if not chapter_text:
            chapter_text = extract_chapter(read_epub_text(source_path_arg), args.chapter)
    else:
        chapter_text = extract_chapter(read_source(source_path_arg), args.chapter)
    source_path = source_text_path(workspace)
    if args.overwrite or not source_path.exists():
        source_path.write_text(chapter_text + "\n", encoding="utf-8", newline="\n")

    manifest_file = manifest_path(workspace)
    if manifest_file.exists() and not args.overwrite:
        raise FileExistsError(f"Manifest already exists: {manifest_file}. Use --overwrite to replace it.")

    manifest = {
        "bookTitle": args.book,
        "bookSlug": workspace.parent.name,
        "chapterNumber": args.chapter,
        "chapterId": chapter_id(args.chapter),
        "workspace": str(workspace).replace("\\", "/"),
        "sourceTextPath": str(source_path).replace("\\", "/"),
        "referenceAudioOriginal": args.reference,
        "referenceAudioClean": str(clean_reference_path(workspace)).replace("\\", "/"),
        "cleanReference": True,
        "globalControl": DEFAULT_GLOBAL_CONTROL,
        "segments": draft_segments(chapter_text),
    }
    ensure_segment_defaults(manifest)
    write_json(manifest_file, manifest)
    print(f"workspace={workspace}")
    print(f"source={source_path}")
    print(f"manifest={manifest_file}")
    print(f"segments={len(manifest['segments'])}")


if __name__ == "__main__":
    main()
