from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ThumbnailTokens:
    show_id: str
    bar_color: str
    label: str
    accent_color: str
    subtitle_primary_color: str
    subtitle_secondary_color: str
    subtitle_outline_color: str
    wave_bar_color: str
    bg_top: tuple[int, int, int]
    bg_bottom: tuple[int, int, int]


DEFAULT_TOKENS: dict[str, ThumbnailTokens] = {
    "series_a": ThumbnailTokens(
        show_id="series_a",
        bar_color="#E9A319",
        label="DAILY TALK · English Conversations",
        accent_color="#E9A319",
        subtitle_primary_color="#E9A319",
        subtitle_secondary_color="#B0B0B0",
        subtitle_outline_color="#3B2A1A",
        wave_bar_color="#EA580C",
        bg_top=(32, 24, 18),
        bg_bottom=(18, 14, 12),
    ),
    "series_b": ThumbnailTokens(
        show_id="series_b",
        bar_color="#2A9D8F",
        label="FIRST STEPS · Easy English",
        accent_color="#2A9D8F",
        subtitle_primary_color="#2A9D8F",
        subtitle_secondary_color="#B0B0B0",
        subtitle_outline_color="#1A4A47",
        wave_bar_color="#14B8A6",
        bg_top=(14, 28, 26),
        bg_bottom=(10, 16, 18),
    ),
    "series_c": ThumbnailTokens(
        show_id="series_c",
        bar_color="#5C4B7A",
        label="POLISHED ENGLISH · Real Talk",
        accent_color="#5C4B7A",
        subtitle_primary_color="#5C4B7A",
        subtitle_secondary_color="#B0B0B0",
        subtitle_outline_color="#2A1F3A",
        wave_bar_color="#E11D48",
        bg_top=(22, 18, 30),
        bg_bottom=(12, 10, 18),
    ),
}


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB, got {value!r}")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def ass_color_bgr(hex_color: str, alpha: int = 0) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"&H{alpha:02X}{b:02X}{g:02X}{r:02X}"


def tokens_from_show(show: dict[str, Any], show_id: str) -> ThumbnailTokens:
    thumb = show.get("thumbnail") or {}
    defaults = DEFAULT_TOKENS[show_id]
    return ThumbnailTokens(
        show_id=show_id,
        bar_color=str(thumb.get("barColor", defaults.bar_color)),
        label=str(thumb.get("label", defaults.label)),
        accent_color=str(thumb.get("accentColor", defaults.accent_color)),
        subtitle_primary_color=str(thumb.get("subtitlePrimaryColor", defaults.subtitle_primary_color)),
        subtitle_secondary_color=str(
            thumb.get("subtitleSecondaryColor", defaults.subtitle_secondary_color)
        ),
        subtitle_outline_color=str(thumb.get("subtitleOutlineColor", defaults.subtitle_outline_color)),
        wave_bar_color=str(thumb.get("waveBarColor", defaults.wave_bar_color)),
        bg_top=tuple(thumb.get("bgTop", defaults.bg_top)),
        bg_bottom=tuple(thumb.get("bgBottom", defaults.bg_bottom)),
    )


def load_show_tokens(show_id: str) -> ThumbnailTokens:
    import json
    from pathlib import Path

    show_config_path = Path(__file__).resolve().parents[5] / "workspace" / "shows" / "tools" / "show_config.json"
    show = json.loads(show_config_path.read_text(encoding="utf-8"))["shows"][show_id]
    return tokens_from_show(show, show_id)
