from __future__ import annotations

import re
from typing import Any

from .config import BookConfig
from .io import sha256_text
from .paths import chapter_id


ABBREVIATIONS = ("Mr.", "Mrs.", "Ms.", "Dr.", "St.", "etc.", "e.g.", "i.e.")


def normalize_coverage_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _protect_abbreviations(value: str) -> str:
    protected = value
    for token in ABBREVIATIONS:
        protected = protected.replace(token, token.replace(".", "\u0000"))
    return protected


def _sentence_units(paragraph: str) -> list[str]:
    protected = _protect_abbreviations(paragraph.strip())
    if not protected:
        return []
    pieces = re.split(r"(?<=[.!?])\s+(?=[\"“‘']?[A-Z])", protected)
    return [piece.replace("\u0000", ".").strip() for piece in pieces if piece.strip()]


def _kind(value: str) -> str:
    stripped = value.lstrip()
    if stripped.startswith(("\"", "“", "‘")):
        return "dialogue"
    if re.search(r"[\"“][^\"”]+[\"”]", value):
        return "dialogue"
    return "narration"


def _word_count(value: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+(?:[’'-][A-Za-z]+)*\b", value))


def _split_long_unit(value: str, max_words: int) -> list[str]:
    if max_words < 8 or _word_count(value) <= max_words:
        return [value]
    tokens = value.split()
    chunks: list[str] = []
    while tokens:
        if len(tokens) <= max_words:
            chunks.append(" ".join(tokens))
            break
        end = max_words
        minimum = max(8, max_words // 2)
        for candidate in range(max_words, minimum - 1, -1):
            if re.search(r"[,;:—–-][\"”’']?$", tokens[candidate - 1]):
                end = candidate
                break
        chunks.append(" ".join(tokens[:end]))
        tokens = tokens[end:]
    return chunks


def rechunk_manifest_payload(
    payload: dict[str, Any], *, max_words: int, preserve_through: int = 0
) -> dict[str, Any]:
    source_segments = payload.get("segments")
    if not isinstance(source_segments, list) or not source_segments:
        raise ValueError("Segment manifest is empty")
    output: list[dict[str, Any]] = []
    for original in source_segments:
        order = int(original["order"])
        if order <= preserve_through:
            output.append(dict(original))
            continue
        display = str(original["displayText"])
        spoken = str(original["spokenText"])
        if display != spoken or original.get("pronunciationSubstitutions"):
            pieces = [display]
        else:
            pieces = _split_long_unit(display, max_words)
        for piece in pieces:
            index = len(output) + 1
            item = dict(original)
            item.update(
                {
                    "id": f"{index:03d}",
                    "order": index,
                    "filename": f"{index:03d}_narrator.wav",
                    "displayText": piece,
                    "spokenText": piece if display == spoken else spoken,
                    "wordCount": _word_count(piece),
                }
            )
            output.append(item)
    if normalize_coverage_text(" ".join(str(item["displayText"]) for item in output)) != normalize_coverage_text(
        " ".join(str(item["displayText"]) for item in source_segments)
    ):
        raise ValueError("Rechunking changed normalized display-text coverage")
    result = dict(payload)
    result["segments"] = output
    return result


def build_segment_manifest(config: BookConfig, chapter_number: int, source_text: str) -> dict[str, Any]:
    units: list[str] = []
    max_words = int(config.render.get("maxSegmentWords", 30))
    for paragraph in re.split(r"\n\s*\n", source_text):
        for unit in _sentence_units(re.sub(r"\s+", " ", paragraph).strip()):
            units.extend(_split_long_unit(unit, max_words))
    if not units:
        raise ValueError("Cannot segment an empty chapter")
    normalized_source = normalize_coverage_text(source_text)
    normalized_segments = normalize_coverage_text(" ".join(units))
    if normalized_source != normalized_segments:
        raise ValueError("Segment display text does not preserve normalized source coverage")

    profile_id = str(config.voice["profileId"])
    short_threshold = int(config.render.get("shortSegmentWordThreshold", 12))
    segments: list[dict[str, Any]] = []
    for index, text in enumerate(units, start=1):
        kind = _kind(text)
        words = _word_count(text)
        segments.append(
            {
                "id": f"{index:03d}",
                "order": index,
                "filename": f"{index:03d}_narrator.wav",
                "kind": kind,
                "speaker": "narrator",
                "voiceProfile": profile_id,
                "deliveryCue": str(
                    config.voice["dialogueCue"] if kind == "dialogue" else config.voice["narrationCue"]
                ),
                "displayText": text,
                "spokenText": text,
                "pronunciationSubstitutions": [],
                "wordCount": words,
                "shortSegment": words <= short_threshold,
            }
        )
    cid = chapter_id(chapter_number)
    return {
        "schema": "classic-listening-segments-v1",
        "bookTitle": config.title,
        "bookSlug": config.slug,
        "chapterNumber": chapter_number,
        "chapterId": cid,
        "voiceMode": "single",
        "voiceProfile": profile_id,
        "globalControl": config.voice["globalControl"],
        "sourceSha256": sha256_text(source_text.rstrip("\n") + "\n"),
        "normalizedSourceSha256": sha256_text(normalized_source),
        "normalizedSourceWordCount": _word_count(normalized_source),
        "cfgValue": config.voice["cfgValue"],
        "inferenceTimesteps": config.voice["inferenceTimesteps"],
        "interSegmentSilenceSec": config.render["interSegmentSilenceSec"],
        "segments": segments,
    }
