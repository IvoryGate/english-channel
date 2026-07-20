from __future__ import annotations

"""Normalize generated cover art to a fixed 16:9 canvas (default 2560x1440).

Image-generation tools rarely emit a true 16:9 frame (e.g. they produce 3:2
1536x1024 even when "16:9" is requested), and podcast covers bake text
(level badge, show label, hook title, brand tag) into the pixels. Naive
cropping cuts that text; stretching distorts it. This module offers several
normalization modes, chosen per artifact:

- ``auto`` / ``top-crop``: scale to fill, crop from bottom. Use for the
  **video background** (no text to preserve) so it fills the frame cleanly.
- ``contain``: scale to fit, pad sides with the edge color. Preserves all
  text but leaves solid side bars.
- ``blur-fill``: scale to fill width, center-crop to height, light Gaussian
  blur. A soft, color-matched backdrop with no readable text — used as the
  background layer under a sharp cover.
- ``blur-fill-composite``: ``blur-fill`` backdrop + the sharp cover contained
  on top with **rounded corners** and **feathered edges** and a small safe
  margin. This is the default for **episode covers/thumbnails**: the 16:9
  frame is seamless (no solid bars), all baked-in text is preserved (never
  cropped), and the cover blends softly into the blurred backdrop.

Defaults are tuned for ELR dialogue-series covers: blur_radius=8 (若隐若现),
safe_margin=0.04, corner_radius=48, feather=16. See
``docs/shows/thumbnail_templates.md`` for the full methodology.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


DEFAULT_WIDTH = 2560
DEFAULT_HEIGHT = 1440
ASPECT_TOLERANCE = 0.01


def _target_ratio(width: int, height: int) -> float:
    return width / height


def _is_target_size(size: tuple[int, int], width: int, height: int) -> bool:
    return size == (width, height)


def _is_target_aspect(size: tuple[int, int], width: int, height: int) -> bool:
    src_w, src_h = size
    target_ratio = _target_ratio(width, height)
    src_ratio = src_w / src_h
    return abs(src_ratio - target_ratio) <= ASPECT_TOLERANCE


def _resize_exact(image: Image.Image, width: int, height: int) -> Image.Image:
    if image.size == (width, height):
        return image
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _crop_to_ratio(
    image: Image.Image,
    width: int,
    height: int,
    *,
    anchor: str,
) -> Image.Image:
    target_ratio = _target_ratio(width, height)
    src_w, src_h = image.size
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        crop_w = int(round(src_h * target_ratio))
        crop_h = src_h
        left = (src_w - crop_w) // 2
        top = 0
    else:
        crop_w = src_w
        crop_h = int(round(src_w / target_ratio))
        left = 0
        if anchor == "top":
            top = 0
        elif anchor == "bottom":
            top = src_h - crop_h
        else:
            top = (src_h - crop_h) // 2

    return image.crop((left, top, left + crop_w, top + crop_h))


def _contain_pad(image: Image.Image, width: int, height: int, safe_margin: float = 0.0) -> Image.Image:
    src_w, src_h = image.size
    scale = min(width / src_w, height / src_h)
    if safe_margin > 0.0:
        scale *= (1.0 - safe_margin)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (width, height))
    # Sample the pad color from the left and right edge strips (mid-height) rather
    # than the whole-image average, so baked-in cover text doesn't muddy the fill
    # color — the edges are typically wall/background, matching the side bars.
    edge_w = max(2, src_w // 20)
    mid_y = src_h // 2
    left_strip = image.crop((0, mid_y - src_h // 8, edge_w, mid_y + src_h // 8)).resize((1, 1), Image.Resampling.LANCZOS).getpixel((0, 0))
    right_strip = image.crop((src_w - edge_w, mid_y - src_h // 8, src_w, mid_y + src_h // 8)).resize((1, 1), Image.Resampling.LANCZOS).getpixel((0, 0))
    left_pad = tuple(int(round((left_strip[i] + right_strip[i]) / 2)) for i in range(3))
    canvas.paste(left_pad, (0, 0, width, height))
    left = (width - new_w) // 2
    top = (height - new_h) // 2
    canvas.paste(resized, (left, top))
    return canvas


def _blur_fill(image: Image.Image, width: int, height: int, blur_radius: float = 8.0) -> Image.Image:
    """Scale to fill width, center-crop to height, apply gentle Gaussian blur.

    A light blur (若隐若现) keeps shapes/colors recognizable as a soft backdrop
    while avoiding hard edges or distracting detail behind the sharp cover.
    """
    src_w, src_h = image.size
    scale = width / src_w
    new_w = width
    new_h = max(height, int(round(src_h * scale)))
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    top = (new_h - height) // 2
    cropped = resized.crop((0, top, width, top + height))
    return cropped.filter(ImageFilter.GaussianBlur(radius=blur_radius))


def _blur_fill_composite(
    image: Image.Image,
    width: int,
    height: int,
    blur_radius: float = 8.0,
    safe_margin: float = 0.04,
    corner_radius: int = 48,
    feather: float = 16.0,
) -> Image.Image:
    """Blurred fill background + sharp cover centered with rounded, feathered edges.

    The sharp layer is contained (small margin all around) so the blurred fill
    shows on all four sides. Rounded corners + edge feather let the cover blend
    softly into the backdrop instead of a hard seam. All baked-in text preserved.
    """
    from PIL import ImageDraw

    bg = _blur_fill(image, width, height, blur_radius=blur_radius)
    src_w, src_h = image.size
    scale = min(width / src_w, height / src_h)
    if safe_margin > 0.0:
        scale *= (1.0 - safe_margin)
    new_w = max(1, int(round(src_w * scale)))
    new_h = max(1, int(round(src_h * scale)))
    sharp = image.resize((new_w, new_h), Image.Resampling.LANCZOS).convert("RGBA")

    # Rounded-corner mask with feathered edges for a soft transition into the blur.
    mask = Image.new("L", (new_w, new_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, new_w - 1, new_h - 1), radius=corner_radius, fill=255)
    if feather > 0.0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
    sharp.putalpha(mask)

    canvas = bg.convert("RGBA")
    canvas.alpha_composite(sharp, ((width - new_w) // 2, (height - new_h) // 2))
    return canvas.convert("RGB")


def normalize_youtube_cover(
    input_path: Path,
    output_path: Path | None = None,
    *,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    mode: str = "auto",
    safe_margin: float = 0.0,
) -> Path:
    output_path = output_path or input_path

    with Image.open(input_path) as image:
        rgb = image.convert("RGB")
        src_w, src_h = rgb.size

        if _is_target_size((src_w, src_h), width, height):
            normalized = rgb
        elif mode == "resize" and _is_target_aspect((src_w, src_h), width, height):
            normalized = _resize_exact(rgb, width, height)
        elif mode == "contain":
            normalized = _contain_pad(rgb, width, height, safe_margin=safe_margin)
        elif mode == "blur-fill":
            normalized = _blur_fill(rgb, width, height)
        elif mode == "blur-fill-composite":
            normalized = _blur_fill_composite(rgb, width, height, safe_margin=safe_margin)
        elif mode == "center-crop":
            normalized = _resize_exact(_crop_to_ratio(rgb, width, height, anchor="center"), width, height)
        elif mode == "top-crop":
            normalized = _resize_exact(_crop_to_ratio(rgb, width, height, anchor="top"), width, height)
        elif mode == "auto":
            if _is_target_aspect((src_w, src_h), width, height):
                normalized = _resize_exact(rgb, width, height)
            else:
                normalized = _resize_exact(_crop_to_ratio(rgb, width, height, anchor="top"), width, height)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        normalized.save(output_path, format="JPEG", quality=92, optimize=True)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize a cover image to YouTube 16:9 (default 2560x1440 / 2K)."
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", help="Defaults to overwriting --input.")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument(
        "--mode",
        choices=("auto", "resize", "top-crop", "center-crop", "contain", "blur-fill", "blur-fill-composite"),
        default="auto",
        help=(
            "auto: resize if already ~16:9, otherwise top-crop (keeps top text). "
            "top-crop: crop from bottom only. contain: pad without cropping. "
            "blur-fill: blurred fill (video bg layer). "
            "blur-fill-composite: blurred fill + sharp rounded cover (episode thumbnails)."
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path
    result = normalize_youtube_cover(
        input_path,
        output_path,
        width=args.width,
        height=args.height,
        mode=args.mode,
    )
    with Image.open(result) as image:
        print(f"output={result.as_posix()}", flush=True)
        print(f"size={image.size[0]}x{image.size[1]}", flush=True)
        print(f"aspect={image.size[0] / image.size[1]:.4f}", flush=True)
        print(f"mode={args.mode}", flush=True)


if __name__ == "__main__":
    main()
