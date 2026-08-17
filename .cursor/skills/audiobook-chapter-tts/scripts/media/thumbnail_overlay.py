from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from media.media_layout import HEIGHT, WIDTH
from media.thumbnail_tokens import ThumbnailTokens, hex_to_rgb


def _crop_to_fill(image: Image.Image, target_w: int = WIDTH, target_h: int = HEIGHT) -> Image.Image:
    """Resize + center-crop to fill the target box without distortion.

    Source images from generative tools often arrive at 3:2 or other ratios;
    a plain resize would stretch them. We scale to cover the target, then crop
    the excess from the center so the final frame is exactly target_w x target_h.
    """
    img = image.convert("RGB")
    src_w, src_h = img.size
    if src_w == target_w and src_h == target_h:
        return img
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = round(src_w * scale), round(src_h * scale)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _load_font(
    size: int,
    *,
    bold: bool = False,
    script: bool = False,
    series: str | None = None,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Bundled OFL fonts (see assets/fonts/LICENSE.txt) at repo root.
    # Series C uses Manrope for main/label/badge to differentiate the premium tier;
    # A and B use Inter. Caveat (script) is shared across all series.
    fonts_dir = Path(__file__).resolve().parents[6] / "assets" / "fonts"

    def bundled(name: str) -> str | None:
        p = fonts_dir / name
        return str(p) if p.is_file() else None

    use_manrope = series == "series_c"
    candidates: list[str] = []
    if script:
        candidates.extend(
            [
                bundled("Caveat-Regular.ttf"),
                "C:/Windows/Fonts/segoesc.ttf",
                "C:/Windows/Fonts/ITCEDSCR.TTF",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )
    elif bold:
        if use_manrope:
            candidates.extend([bundled("Manrope-Bold.ttf")])
        candidates.extend(
            [
                bundled("Inter-Bold.ttf"),
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    else:
        if use_manrope:
            candidates.extend([bundled("Manrope-Regular.ttf")])
        candidates.extend(
            [
                bundled("Inter-Regular.ttf"),
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )
    for path in candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_height(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    y: int,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    stroke: int = 0,
    stroke_fill: tuple[int, int, int] | None = None,
) -> None:
    if not text:
        return
    width = _text_width(draw, text, font)
    x = (WIDTH - width) // 2
    draw.text((x, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def _draw_pill(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    y: int,
    font: ImageFont.ImageFont,
    fill_rgb: tuple[int, int, int],
    text_fill: tuple[int, int, int] = (255, 255, 255),
) -> None:
    if not text:
        return
    text_w = _text_width(draw, text, font)
    text_h = _text_height(draw, text, font)
    pad_x = 28
    pad_y = 12
    pill_w = text_w + pad_x * 2
    pill_h = text_h + pad_y * 2
    x0 = (WIDTH - pill_w) // 2
    y0 = y
    draw.rounded_rectangle(
        [(x0, y0), (x0 + pill_w, y0 + pill_h)],
        radius=18,
        fill=fill_rgb,
    )
    draw.text((x0 + pad_x, y0 + pad_y - 2), text, font=font, fill=text_fill)


def overlay_thumbnail_text(
    scene_image: Image.Image,
    *,
    tokens: ThumbnailTokens,
    cover_text: dict[str, str],
    level_badge: str,
    show_label: str,
) -> Image.Image:
    image = _crop_to_fill(scene_image, WIDTH, HEIGHT)
    draw = ImageDraw.Draw(image)
    accent = hex_to_rgb(tokens.accent_color)
    series = tokens.show_id

    badge_font = _load_font(30, bold=True, series=series)
    label_font = _load_font(28, bold=True, series=series)
    prefix_font = _load_font(54, script=True)
    main_font = _load_font(92, bold=True, series=series)
    suffix_font = _load_font(42, bold=True, series=series)
    bottom_font = _load_font(34, bold=True, series=series)

    draw.rounded_rectangle([(36, 28), (170, 78)], radius=20, fill=accent)
    draw.text((56, 38), level_badge, font=badge_font, fill=(20, 20, 20))

    label_w = _text_width(draw, show_label, label_font)
    draw.text((WIDTH - label_w - 40, 36), show_label, font=label_font, fill=(255, 255, 255))

    y = 300
    _draw_centered_text(draw, cover_text.get("prefix", ""), y=y, font=prefix_font, fill=accent)
    y += 70
    _draw_centered_text(
        draw,
        cover_text.get("main", ""),
        y=y,
        font=main_font,
        fill=(255, 255, 255),
        stroke=3,
        stroke_fill=(20, 20, 20),
    )
    y += 120
    _draw_pill(draw, cover_text.get("suffix", ""), y=y, font=suffix_font, fill_rgb=accent)

    badge = cover_text.get("badge", "").strip()
    if badge:
        _draw_pill(draw, badge, y=HEIGHT - 120, font=bottom_font, fill_rgb=(30, 30, 30))

    return image


def compose_thumbnail_from_scene(
    scene_path: Path,
    *,
    tokens: ThumbnailTokens,
    cover_text: dict[str, str],
    level_badge: str,
    show_label: str,
    thumbnail_png: Path,
    video_bg_jpg: Path,
    video_bg_scene: Path | None = None,
) -> dict[str, Any]:
    with Image.open(scene_path) as scene:
        thumbnail = overlay_thumbnail_text(
            scene,
            tokens=tokens,
            cover_text=cover_text,
            level_badge=level_badge,
            show_label=show_label,
        )

    thumbnail_png.parent.mkdir(parents=True, exist_ok=True)
    thumbnail.save(thumbnail_png, format="PNG")

    bg_source = video_bg_scene if video_bg_scene and video_bg_scene.is_file() else scene_path
    with Image.open(bg_source) as bg:
        _crop_to_fill(bg, WIDTH, HEIGHT).save(
            video_bg_jpg,
            format="JPEG",
            quality=92,
            optimize=True,
        )

    return {
        "mode": "scene-plus-overlay",
        "sceneSource": str(scene_path).replace("\\", "/"),
        "videoBgSource": str(bg_source).replace("\\", "/"),
        "thumbnailPng": str(thumbnail_png).replace("\\", "/"),
        "videoBgJpg": str(video_bg_jpg).replace("\\", "/"),
        "coverText": cover_text,
    }
