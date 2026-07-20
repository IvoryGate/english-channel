"""Enhance and export the approved channel avatar for YouTube upload."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

DEFAULT_SRC = Path(
    "workspace/dialogue_podcast_research/youtube_corpus/branding/Generated_image.png"
)
DEFAULT_OUT = Path(
    "workspace/dialogue_podcast_research/youtube_corpus/branding/channel_avatar_elr_800.png"
)
TARGET_SIZE = 800


def enhance_avatar(src: Path, out: Path, size: int = TARGET_SIZE) -> Path:
    img = Image.open(src).convert("RGBA")

    # Flatten on matching dark background (corner color outside circle)
    bg = Image.new("RGBA", img.size, (45, 30, 22, 255))
    flat = Image.alpha_composite(bg, img).convert("RGB")

    # Downscale with high-quality filter; source is 1024 so this stays sharp
    if flat.size != (size, size):
        flat = flat.resize((size, size), Image.Resampling.LANCZOS)

    # Light sharpen + contrast for small avatar legibility
    flat = flat.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
    flat = ImageEnhance.Contrast(flat).enhance(1.06)
    flat = ImageEnhance.Sharpness(flat).enhance(1.12)

    out.parent.mkdir(parents=True, exist_ok=True)
    flat.save(out, "PNG", optimize=True)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Enhance approved avatar PNG for YouTube.")
    parser.add_argument("--src", default=str(DEFAULT_SRC))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--size", type=int, default=TARGET_SIZE)
    args = parser.parse_args()

    src, out = Path(args.src), Path(args.out)
    if not src.is_file():
        raise SystemExit(f"Source not found: {src.as_posix()}")

    result = enhance_avatar(src, out, size=args.size)
    print(result.as_posix(), result.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
