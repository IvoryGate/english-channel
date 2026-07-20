from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from media.media_layout import HEIGHT, WIDTH
from media.thumbnail_tokens import ThumbnailTokens, hex_to_rgb

BAR_HEIGHT = 96
HOOK_MAX_CHARS_PER_LINE = 28
HOOK_MAX_LINES = 2


def _load_font(size: int, bold: bool = False, series: str | None = None) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
  fonts_dir = Path(__file__).resolve().parents[6] / "assets" / "fonts"
  use_manrope = series == "series_c"
  candidates = []
  if bold:
    if use_manrope:
      candidates.append(str(fonts_dir / "Manrope-Bold.ttf"))
    candidates.extend(
      [
        str(fonts_dir / "Inter-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
      ]
    )
  else:
    if use_manrope:
      candidates.append(str(fonts_dir / "Manrope-Regular.ttf"))
    candidates.extend(
      [
        str(fonts_dir / "Inter-Regular.ttf"),
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
      ]
    )
  for path in candidates:
    if path and Path(path).is_file():
      return ImageFont.truetype(path, size=size)
  return ImageFont.load_default()


def _draw_gradient(image: Image.Image, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
  draw = ImageDraw.Draw(image)
  for y in range(HEIGHT):
    ratio = y / max(1, HEIGHT - 1)
    color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
    draw.line([(0, y), (WIDTH, y)], fill=color)


def _wrap_hook(hook_text: str) -> list[str]:
  cleaned = " ".join(hook_text.strip().split())
  if not cleaned:
    return ["English Listening Room"]
  lines = textwrap.wrap(cleaned, width=HOOK_MAX_CHARS_PER_LINE)
  if len(lines) > HOOK_MAX_LINES:
    lines = lines[:HOOK_MAX_LINES]
    if len(lines[-1]) > 3:
      lines[-1] = lines[-1].rstrip(" .,;:") + "..."
  return lines


def render_thumbnail(tokens: ThumbnailTokens, hook_text: str) -> Image.Image:
  image = Image.new("RGB", (WIDTH, HEIGHT))
  _draw_gradient(image, tokens.bg_top, tokens.bg_bottom)
  draw = ImageDraw.Draw(image)

  bar_rgb = hex_to_rgb(tokens.bar_color)
  draw.rectangle([(0, 0), (WIDTH, BAR_HEIGHT)], fill=bar_rgb)

  label_font = _load_font(34, bold=True, series=tokens.show_id)
  hook_font = _load_font(86, bold=True, series=tokens.show_id)

  draw.text((48, 18), tokens.label, font=label_font, fill=(255, 255, 255))

  lines = _wrap_hook(hook_text)
  line_height = 98
  block_height = line_height * len(lines)
  y_start = (HEIGHT - block_height) // 2 - 20
  for index, line in enumerate(lines):
    bbox = draw.textbbox((0, 0), line, font=hook_font)
    text_w = bbox[2] - bbox[0]
    x = (WIDTH - text_w) // 2
    y = y_start + index * line_height
    draw.text((x + 2, y + 2), line, font=hook_font, fill=(0, 0, 0))
    draw.text((x, y), line, font=hook_font, fill=(255, 255, 255))

  return image


def save_thumbnail_outputs(
  tokens: ThumbnailTokens,
  hook_text: str,
  thumbnail_png: Path,
  video_bg_jpg: Path,
) -> dict[str, str]:
  image = render_thumbnail(tokens, hook_text)
  thumbnail_png.parent.mkdir(parents=True, exist_ok=True)
  image.save(thumbnail_png, format="PNG")
  image.save(video_bg_jpg, format="JPEG", quality=92, optimize=True)
  return {
    "thumbnailPng": str(thumbnail_png).replace("\\", "/"),
    "videoBgJpg": str(video_bg_jpg).replace("\\", "/"),
    "hookText": hook_text.strip(),
    "showId": tokens.show_id,
  }
