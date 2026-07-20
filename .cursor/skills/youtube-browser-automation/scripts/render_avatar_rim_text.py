"""Composite ELR logo + circular-rim arc text onto a full-bleed study background."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 800
CENTER = SIZE // 2
# YouTube avatar circle inscribed in square
AVATAR_RADIUS = 380

BG = Path("workspace/dialogue_podcast_research/youtube_corpus/branding/avatar_bg_study_full_bleed.png")
OUT_DIR = Path("workspace/dialogue_podcast_research/youtube_corpus/branding")


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ["C:/Windows/Fonts/timesbd.ttf", "C:/Windows/Fonts/georgiab.ttf"]
        if bold
        else ["C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/georgia.ttf"]
    )
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default()


def _draw_headphones(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    draw.arc((cx - 62, cy - 28, cx + 62, cy + 38), start=200, end=-20, fill=color, width=8)
    draw.rounded_rectangle((cx - 70, cy - 4, cx - 44, cy + 34), radius=10, fill=color)
    draw.rounded_rectangle((cx + 44, cy - 4, cx + 70, cy + 34), radius=10, fill=color)
    # laurel hints
    draw.arc((cx - 95, cy + 8, cx - 55, cy + 38), start=200, end=320, fill=(196, 160, 90), width=3)
    draw.arc((cx + 55, cy + 8, cx + 95, cy + 38), start=220, end=340, fill=(196, 160, 90), width=3)


def _draw_rim_text(
    base: Image.Image,
    text: str,
    *,
    radius: int,
    font_size: int,
    fill: tuple[int, int, int],
    stroke: tuple[int, int, int] | None,
    stroke_width: int,
    start_deg: float,
    end_deg: float,
) -> None:
    """Place caps along a circular arc matching the YouTube avatar crop."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = _font(font_size, bold=True)
    chars = list(text)
    n = len(chars)
    if n == 0:
        return
    for i, ch in enumerate(chars):
        t = i / (n - 1) if n > 1 else 0.5
        deg = start_deg + (end_deg - start_deg) * t
        rad = math.radians(deg)
        x = CENTER + radius * math.cos(rad)
        y = CENTER + radius * math.sin(rad)
        # tangent rotation so letters follow the circle
        rotation = deg + 90
        ch_img = Image.new("RGBA", (font_size * 2, font_size * 2), (0, 0, 0, 0))
        ch_draw = ImageDraw.Draw(ch_img)
        bbox = ch_draw.textbbox((0, 0), ch, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        ox, oy = (ch_img.size[0] - tw) // 2, (ch_img.size[1] - th) // 2
        if stroke:
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx or dy:
                        ch_draw.text((ox + dx, oy + dy), ch, font=font, fill=stroke)
        ch_draw.text((ox, oy), ch, font=font, fill=fill)
        rotated = ch_img.rotate(-rotation, resample=Image.Resampling.BICUBIC, expand=True)
        px = int(x - rotated.size[0] / 2)
        py = int(y - rotated.size[1] / 2)
        layer.paste(rotated, (px, py), rotated)
    base.alpha_composite(layer)


def render_variant(
    bg_path: Path,
    out_path: Path,
    *,
    rim_font: int,
    rim_radius: int,
    rim_fill: tuple[int, int, int],
    rim_stroke: tuple[int, int, int] | None = None,
    rim_stroke_width: int = 2,
) -> Path:
    base = Image.open(bg_path).convert("RGBA").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(base)

    elr_font = _font(196, bold=True)
    elr = "ELR"
    bbox = draw.textbbox((0, 0), elr, font=elr_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((SIZE - tw) / 2, 248 - th / 2), elr, font=elr_font, fill=(248, 236, 210))

    _draw_headphones(draw, CENTER, 418, (248, 236, 210))

    # Bottom semicircle rim — matches avatar crop circle
    _draw_rim_text(
        base,
        "ENGLISH LISTENING ROOM",
        radius=rim_radius,
        font_size=rim_font,
        fill=rim_fill,
        stroke=rim_stroke,
        stroke_width=rim_stroke_width,
        start_deg=205,
        end_deg=335,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path


def main() -> None:
    variants = [
        ("avatar_final_rim_v1_cream.png", 30, 332, (255, 248, 235), (40, 28, 18), 2),
        ("avatar_final_rim_v2_large_white.png", 34, 328, (255, 255, 250), (30, 22, 14), 3),
        ("avatar_final_rim_v3_gold.png", 32, 330, (245, 210, 140), (45, 30, 18), 2),
    ]
    for name, fs, r, fill, stroke, sw in variants:
        path = render_variant(BG, OUT_DIR / name, rim_font=fs, rim_radius=r, rim_fill=fill, rim_stroke=stroke, rim_stroke_width=sw)
        print(path.as_posix())


if __name__ == "__main__":
    main()
