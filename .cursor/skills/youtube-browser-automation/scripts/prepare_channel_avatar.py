"""Generate a full-bleed square YouTube channel avatar for English Listening Room."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 800
OUT = Path("workspace/dialogue_podcast_research/youtube_corpus/branding/channel_avatar_elr_800.png")


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/georgiab.ttf"]
        if bold
        else ["C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _draw_study_background(draw: ImageDraw.ImageDraw, size: int) -> None:
    # Warm vertical gradient
    for y in range(size):
        t = y / size
        r = int(72 + (118 - 72) * t)
        g = int(48 + (88 - 48) * t)
        b = int(36 + (62 - 36) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    # Bookshelves left
    draw.rectangle((0, 120, 170, size), fill=(58, 38, 28))
    for row in range(6):
        y = 150 + row * 95
        draw.line([(0, y), (170, y)], fill=(42, 28, 20), width=3)
        for col, hue in enumerate([(120, 70, 45), (90, 55, 35), (145, 95, 55)]):
            draw.rectangle((18 + col * 48, y - 70, 58 + col * 48, y - 8), fill=hue)

    # Window + lamp right
    draw.rectangle((size - 190, 110, size - 20, 320), fill=(180, 200, 215))
    draw.rectangle((size - 205, 95, size - 5, 335), outline=(110, 85, 60), width=6)
    draw.polygon(
        [(size - 130, 360), (size - 70, 360), (size - 55, 390), (size - 145, 390)],
        fill=(55, 45, 35),
    )
    draw.ellipse((size - 150, 300, size - 50, 370), fill=(220, 180, 90))
    draw.rectangle((size - 108, 370, size - 92, 430), fill=(70, 55, 40))

    # Desk foreground
    draw.rectangle((120, size - 170, size - 80, size - 120), fill=(96, 68, 46))
    draw.rectangle((150, size - 145, 290, size - 125), fill=(210, 185, 150))
    draw.ellipse((300, size - 165, 360, size - 105), fill=(230, 225, 210))
    draw.rectangle((318, size - 145, 342, size - 115), fill=(180, 60, 50))


def _draw_headphones(draw: ImageDraw.ImageDraw, cx: int, cy: int) -> None:
    draw.arc((cx - 70, cy - 35, cx + 70, cy + 55), start=200, end=-20, fill=(245, 235, 210), width=10)
    draw.rounded_rectangle((cx - 78, cy - 10, cx - 48, cy + 40), radius=12, fill=(30, 28, 26))
    draw.rounded_rectangle((cx + 48, cy - 10, cx + 78, cy + 40), radius=12, fill=(30, 28, 26))


def _draw_arc_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    cx: int,
    cy: int,
    radius: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    chars = list(text)
    if not chars:
        return
    span = 118
    start_angle = 90 + span / 2
    step = span / max(len(chars) - 1, 1)
    for i, ch in enumerate(chars):
        angle = math.radians(start_angle - i * step)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        bbox = draw.textbbox((0, 0), ch, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tx, ty = x - w / 2, y - h / 2
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
            draw.text((tx + dx, ty + dy), ch, font=font, fill=(35, 24, 16))
        draw.text((tx, ty), ch, font=font, fill=fill)


def build_avatar(output: Path = OUT) -> Path:
    img = Image.new("RGB", (SIZE, SIZE), (80, 55, 38))
    draw = ImageDraw.Draw(img)
    _draw_study_background(draw, SIZE)

    elr_font = _load_font(210, bold=True)
    arc_font = _load_font(46, bold=True)

    elr = "ELR"
    bbox = draw.textbbox((0, 0), elr, font=elr_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((SIZE - tw) / 2, 250 - th / 2), elr, font=elr_font, fill=(248, 236, 210))

    _draw_headphones(draw, SIZE // 2, 430)
    _draw_arc_text(
        draw,
        "ENGLISH LISTENING ROOM",
        cx=SIZE // 2,
        cy=SIZE // 2 + 40,
        radius=285,
        font=arc_font,
        fill=(255, 252, 240),
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG", optimize=True)
    return output


if __name__ == "__main__":
    path = build_avatar()
    print(path.as_posix(), path.stat().st_size)
