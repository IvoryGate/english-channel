from __future__ import annotations

from pathlib import Path
from typing import Any

from media.media_layout import (
    ASS_FONT_SIZE,
    ASS_MARGIN_V,
    ASS_OUTLINE,
    ASS_SHADOW,
    ASS_WORDS_PER_LINE,
    HEIGHT,
    WIDTH,
)
from media.thumbnail_tokens import ThumbnailTokens, ass_color_bgr

PLAY_RES_X = WIDTH
PLAY_RES_Y = HEIGHT
WORDS_PER_LINE = ASS_WORDS_PER_LINE
# Per-series font: Series C (Polished English) uses Manrope to differentiate the
# premium tier; A and B use Inter. Both are bundled in assets/fonts/ (OFL).
# libass falls back to a default sans if the named family is missing, so we also
# point compose_media_video.py at assets/fonts/ via fonts_dir.
SERIES_FONT_NAME = {
    "series_a": "Inter",
    "series_b": "Inter",
    "series_c": "Manrope",
}
DEFAULT_FONT_NAME = "Inter"
FONT_SIZE = ASS_FONT_SIZE
MARGIN_V = ASS_MARGIN_V
ASS_ALIGNMENT = 5
OUTLINE = ASS_OUTLINE
SHADOW = ASS_SHADOW


def _ass_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:d}:{minutes:02d}:{secs:05.2f}"


def _chunk_words(words: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [words[i : i + size] for i in range(0, len(words), size)]


def _karaoke_line(words: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for word in words:
        duration_cs = max(1, int(round((float(word["end"]) - float(word["start"])) * 100)))
        text = str(word["word"]).strip()
        # \kf = progressive left-to-right fill (classic karaoke), not whole-word \k pop
        parts.append(f"{{\\kf{duration_cs}}}{text}")
    return " ".join(parts)


def _header(tokens: ThumbnailTokens) -> list[str]:
    # ASS karaoke: SecondaryColour = waiting words, PrimaryColour = spoken highlight
    primary = ass_color_bgr(tokens.subtitle_primary_color)
    secondary = ass_color_bgr(tokens.subtitle_secondary_color)
    outline = ass_color_bgr(tokens.subtitle_outline_color)
    back = ass_color_bgr("#000000", alpha=0)
    font_name = SERIES_FONT_NAME.get(tokens.show_id, DEFAULT_FONT_NAME)

    return [
        "[Script Info]",
        "Title: ELR Karaoke",
        "ScriptType: v4.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        f"PlayResX: {PLAY_RES_X}",
        f"PlayResY: {PLAY_RES_Y}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        (
            f"Style: Default,{font_name},{FONT_SIZE},{primary},{secondary},{outline},{back},"
            f"-1,0,0,0,100,100,0,0,1,{OUTLINE},{SHADOW},{ASS_ALIGNMENT},80,80,{MARGIN_V},1"
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]


def _events_for_turn_words(turn_words: list[dict[str, Any]]) -> list[str]:
    events: list[str] = []
    for chunk in _chunk_words(turn_words, WORDS_PER_LINE):
        start = float(chunk[0]["start"])
        end = float(chunk[-1]["end"])
        text = _karaoke_line(chunk)
        events.append(
            f"Dialogue: 0,{_ass_timestamp(start)},{_ass_timestamp(end)},Default,,0,0,0,,{text}"
        )
    return events


def generate_karaoke_ass(
    words: list[dict[str, Any]],
    tokens: ThumbnailTokens,
    *,
    turns: list[dict[str, Any]] | None = None,
) -> str:
    if not words and not turns:
        raise ValueError("Cannot generate ASS without aligned words")

    events: list[str] = []
    if turns:
        for turn in turns:
            turn_words = turn.get("words") or []
            if turn_words:
                events.extend(_events_for_turn_words(turn_words))
    else:
        events.extend(_events_for_turn_words(words))

    return "\n".join(_header(tokens) + events) + "\n"


def write_karaoke_ass(
    path: Path,
    words: list[dict[str, Any]],
    tokens: ThumbnailTokens,
    *,
    turns: list[dict[str, Any]] | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_karaoke_ass(words, tokens, turns=turns), encoding="utf-8", newline="\n")
