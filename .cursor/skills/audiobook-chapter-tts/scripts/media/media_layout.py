"""Canonical ELR podcast video / cover layout (minimum 2K)."""

from __future__ import annotations

# YouTube-ready 16:9 — at least 2K (2560×1440). Do not ship 1080p finals.
WIDTH = 2560
HEIGHT = 1440

# Lower-middle waveform panel (scaled from 1920×1080 layout)
WAVE_WIDTH = 747
WAVE_HEIGHT = 117
WAVE_X = (WIDTH - WAVE_WIDTH) // 2
WAVE_Y = 1093

# ASS karaoke (centre, safely above the lower waveform panel)
ASS_FONT_SIZE = 136
ASS_MARGIN_V = 0
ASS_OUTLINE = 6
ASS_SHADOW = 0
ASS_WORDS_PER_LINE = 5
