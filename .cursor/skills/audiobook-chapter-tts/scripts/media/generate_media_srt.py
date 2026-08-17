from __future__ import annotations

from pathlib import Path
from typing import Any


def _srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _chunk_words(words: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [words[i : i + size] for i in range(0, len(words), size)]


def _blocks_for_words(words: list[dict[str, Any]], *, words_per_cue: int) -> list[str]:
    blocks: list[str] = []
    for chunk in _chunk_words(words, words_per_cue):
        start = float(chunk[0]["start"])
        end = float(chunk[-1]["end"])
        text = " ".join(str(word["word"]).strip() for word in chunk)
        blocks.append(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{text}")
    return blocks


def generate_media_srt(
    words: list[dict[str, Any]],
    *,
    words_per_cue: int = 8,
    turns: list[dict[str, Any]] | None = None,
) -> str:
    cue_blocks: list[str] = []
    if turns:
        for turn in turns:
            turn_words = turn.get("words") or []
            cue_blocks.extend(_blocks_for_words(turn_words, words_per_cue=words_per_cue))
    else:
        cue_blocks.extend(_blocks_for_words(words, words_per_cue=words_per_cue))

    numbered: list[str] = []
    for index, block in enumerate(cue_blocks, start=1):
        numbered.append(f"{index}\n{block}\n")
    return "\n".join(numbered)


def write_media_srt(
    path: Path,
    words: list[dict[str, Any]],
    *,
    words_per_cue: int = 8,
    turns: list[dict[str, Any]] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        generate_media_srt(words, words_per_cue=words_per_cue, turns=turns),
        encoding="utf-8",
        newline="\n",
    )
