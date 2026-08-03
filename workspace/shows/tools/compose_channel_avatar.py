"""Compose a crisp 2K YouTube badge avatar with perfectly symmetric arc text."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = 2048
CENTER = SIZE // 2
OUTER_R = 1000
RING_OUTER = 1000
RING_INNER = 820
FACE_R = 790
TEXT_RADIUS = 912

IVORY = (247, 241, 230)
COCOA = (74, 49, 36)
ROSE = (196, 140, 138)
TAUPE = (118, 88, 70)
WHITE = (255, 255, 255)
CREAM_BG = (245, 240, 232)


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _circular_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (CENTER - radius, CENTER - radius, CENTER + radius, CENTER + radius),
        fill=255,
    )
    return mask


def _prepare_face(source: Path) -> Image.Image:
    face = Image.open(source).convert("RGBA")
    side = min(face.size)
    left = (face.width - side) // 2
    top = max(0, (face.height - side) // 2 - side // 16)
    face = face.crop((left, top, left + side, top + side))
    face = face.resize((FACE_R * 2, FACE_R * 2), Image.Resampling.LANCZOS)

    subject = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    subject.paste(face, (CENTER - FACE_R, CENTER - FACE_R + 16), face)

    bg = Image.new("RGBA", (SIZE, SIZE), (*TAUPE, 255))
    vignette = Image.new("L", (SIZE, SIZE), 0)
    vdraw = ImageDraw.Draw(vignette)
    vdraw.ellipse(
        (CENTER - FACE_R, CENTER - FACE_R, CENTER + FACE_R, CENTER + FACE_R),
        fill=255,
    )
    vignette = vignette.filter(ImageFilter.GaussianBlur(14))
    return Image.composite(subject, bg, vignette)


def _draw_rings(draw: ImageDraw.ImageDraw) -> None:
    draw.ellipse(
        (CENTER - RING_OUTER, CENTER - RING_OUTER, CENTER + RING_OUTER, CENTER + RING_OUTER),
        outline=COCOA,
        width=36,
    )
    draw.ellipse(
        (
            CENTER - RING_OUTER + 30,
            CENTER - RING_OUTER + 30,
            CENTER + RING_OUTER - 30,
            CENTER + RING_OUTER - 30,
        ),
        outline=IVORY,
        width=152,
    )
    draw.ellipse(
        (CENTER - RING_INNER, CENTER - RING_INNER, CENTER + RING_INNER, CENTER + RING_INNER),
        outline=COCOA,
        width=16,
    )
    draw.ellipse(
        (
            CENTER - RING_INNER + 22,
            CENTER - RING_INNER + 22,
            CENTER + RING_INNER - 22,
            CENTER + RING_INNER - 22,
        ),
        outline=(210, 186, 164),
        width=4,
    )


def _glyph(ch: str, font: ImageFont.FreeTypeFont) -> tuple[Image.Image, tuple[float, float]]:
    """Render one character and return image + ink centroid."""
    bbox = font.getbbox(ch)
    pad = 24
    w = max(1, bbox[2] - bbox[0]) + pad * 2
    h = max(1, bbox[3] - bbox[1]) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((pad - bbox[0], pad - bbox[1]), ch, font=font, fill=COCOA)

    alpha = img.split()[-1]
    ink = alpha.point(lambda a: 255 if a > 16 else 0)
    abox = ink.getbbox()
    if not abox:
        return img, (w / 2, h / 2)
    cx = (abox[0] + abox[2]) / 2
    cy = (abox[1] + abox[3]) / 2
    return img, (cx, cy)


def _draw_arc_text(base: Image.Image, text: str, radius: float, font: ImageFont.FreeTypeFont) -> Image.Image:
    glyphs: list[tuple[str, Image.Image, tuple[float, float], float]] = []
    spacing = 8.0
    for ch in text:
        img, centroid = _glyph(ch, font)
        # advance ≈ ink width
        abox = img.split()[-1].getbbox() or (0, 0, img.width, img.height)
        advance = float(abox[2] - abox[0])
        glyphs.append((ch, img, centroid, advance))

    total = sum(g[3] for g in glyphs) + spacing * (len(glyphs) - 1)
    # Arc length positions of glyph centers, left → right.
    # Center of whole string maps to top of circle (angle = π/2).
    positions: list[float] = []
    cursor = 0.0
    for _, _, _, advance in glyphs:
        positions.append(cursor + advance / 2.0)
        cursor += advance + spacing

    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for (_, glyph, (gcx, gcy), _), arc_pos in zip(glyphs, positions):
        # Symmetric: left end and right end share equal |Δangle| from top.
        mid = math.pi / 2 + (total / 2.0 - arc_pos) / radius
        x = CENTER + radius * math.cos(mid)
        y = CENTER - radius * math.sin(mid)
        rot_deg = math.degrees(mid) - 90

        rotated = glyph.rotate(rot_deg, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))

        # Map original ink centroid through rotation/expand.
        # Approximate paste so rotated image center ~= projected glyph center.
        # Better: rotate around centroid by pasting into a larger canvas first.
        gw, gh = glyph.size
        holder = Image.new("RGBA", (gw * 3, gh * 3), (0, 0, 0, 0))
        holder.paste(glyph, (gw, gh), glyph)
        # centroid in holder coords
        hcx, hcy = gcx + gw, gcy + gh
        holder = holder.rotate(rot_deg, resample=Image.Resampling.BICUBIC, center=(hcx, hcy), expand=False)
        # After rotate-around-center without expand, centroid stays at (hcx, hcy)
        paste_x = int(round(x - hcx))
        paste_y = int(round(y - hcy))
        layer.alpha_composite(holder, (paste_x, paste_y))

    return Image.alpha_composite(base, layer)


def _draw_elr_capsule(draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont) -> None:
    text = "ELR"
    tw = font.getlength(text)
    pad_x, pad_y = 48, 18
    box_w = tw + pad_x * 2
    box_h = font.size + pad_y * 2
    x0 = CENTER - box_w / 2
    y0 = CENTER + RING_INNER - 36 - box_h / 2
    x1 = x0 + box_w
    y1 = y0 + box_h
    draw.rounded_rectangle((x0 + 3, y0 + 5, x1 + 3, y1 + 5), radius=42, fill=(60, 40, 30, 55))
    draw.rounded_rectangle((x0, y0, x1, y1), radius=42, fill=ROSE, outline=WHITE, width=7)
    draw.text(((x0 + x1 - tw) / 2, y0 + pad_y - 2), text, font=font, fill=WHITE)


def _draw_side_marks(draw: ImageDraw.ImageDraw) -> None:
    for sign in (-1, 1):
        cx = CENTER + sign * 905
        cy = CENTER + 30
        r = 16
        points = []
        for i in range(8):
            ang = math.radians(-90 + i * 45)
            rad = r if i % 2 == 0 else r * 0.42
            points.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        draw.polygon(points, fill=COCOA)


def compose(character_path: Path, output_path: Path) -> Path:
    face = _prepare_face(character_path)
    canvas = Image.new("RGBA", (SIZE, SIZE), (*CREAM_BG, 255))
    face_mask = _circular_mask(SIZE, FACE_R)
    canvas.paste(face, (0, 0), face_mask)

    ring_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ring_layer, "RGBA")
    _draw_rings(draw)
    _draw_side_marks(draw)
    canvas = Image.alpha_composite(canvas, ring_layer)

    title_font = _load_font(r"C:\Windows\Fonts\timesbd.ttf", 74)
    canvas = _draw_arc_text(canvas, "ENGLISH LISTENING ROOM", radius=TEXT_RADIUS, font=title_font)

    overlay = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    _draw_elr_capsule(odraw, _load_font(r"C:\Windows\Fonts\timesbd.ttf", 62))
    canvas = Image.alpha_composite(canvas, overlay)

    outer_mask = _circular_mask(SIZE, OUTER_R)
    out = Image.new("RGBA", (SIZE, SIZE), (*CREAM_BG, 255))
    out.paste(canvas, (0, 0), outer_mask)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rgb = Image.new("RGB", (SIZE, SIZE), CREAM_BG)
    rgb.paste(out, mask=out.split()[-1])
    rgb.save(output_path, format="PNG", optimize=True)
    return output_path


def main() -> None:
    src = Path(r"C:\Users\27370\.cursor\projects\h-english-channel\assets\elr_avatar_character_only.png")
    out = Path(r"C:\Users\27370\.cursor\projects\h-english-channel\assets\english_listening_room_youtube_avatar_2k.png")
    repo_out = Path(r"h:\english-channel\workspace\shows\branding\english_listening_room_youtube_avatar_2k.png")
    path = compose(src, out)
    repo_out.parent.mkdir(parents=True, exist_ok=True)
    Image.open(path).save(repo_out, format="PNG", optimize=True)

    # Verify first/last glyph ink Y symmetry for QA.
    im = Image.open(path).convert("RGB")
    pixels = im.load()
    left_ys = []
    right_ys = []
    for y in range(40, 280):
        for x in range(180, 420):
            r, g, b = pixels[x, y]
            if r < 110 and g < 90 and b < 80:
                left_ys.append(y)
                break
        for x in range(SIZE - 420, SIZE - 180):
            r, g, b = pixels[x, y]
            if r < 110 and g < 90 and b < 80:
                right_ys.append(y)
                break
    left_y = min(left_ys) if left_ys else -1
    right_y = min(right_ys) if right_ys else -1
    print(f"wrote={path.as_posix()} size={im.size}")
    print(f"repo={repo_out.as_posix()}")
    print(f"arc_top_y left={left_y} right={right_y} delta={abs(left_y - right_y)}")


if __name__ == "__main__":
    main()

