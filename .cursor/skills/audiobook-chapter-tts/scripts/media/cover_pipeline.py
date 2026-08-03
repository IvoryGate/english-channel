from __future__ import annotations

from pathlib import Path
from typing import Any

from media.host_visuals import build_cover_image_prompt, build_scene_image_prompt, get_show_visual, parse_cover_text_layers
from media.thumbnail_overlay import compose_thumbnail_from_scene
from media.thumbnail_tokens import ThumbnailTokens, tokens_from_show

REPO_ROOT = Path(__file__).resolve().parents[5]
SHOW_CONFIG_PATH = REPO_ROOT / "workspace" / "shows" / "tools" / "show_config.json"


def load_show_tokens(show_id: str) -> ThumbnailTokens:
    import json

    show = json.loads(SHOW_CONFIG_PATH.read_text(encoding="utf-8"))["shows"][show_id]
    return tokens_from_show(show, show_id)


def build_prompt_bundle(
    *,
    show_id: str,
    hook_text: str,
    youtube_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = youtube_payload or {}
    scene_hint = str(payload.get("coverScene", "")).strip()
    outfit_female = str(payload.get("coverOutfitFemale", "")).strip()
    outfit_male = str(payload.get("coverOutfitMale", "")).strip()
    action_hint = str(payload.get("coverAction", "")).strip()
    cover_text = parse_cover_text_layers(hook_text, payload)
    show_visual = get_show_visual(show_id)

    return {
        "schema": "elr-cover-prompt-bundle-v1",
        "showId": show_id,
        "hosts": {
            "female": show_visual.female_host.name,
            "male": show_visual.male_host.name,
        },
        "levelBadge": show_visual.level_badge,
        "coverText": cover_text,
        "coverImagePrompt": build_cover_image_prompt(
            show_id=show_id,
            hook_text=hook_text,
            youtube_payload=payload,
        ),
        "videoBgImagePrompt": build_scene_image_prompt(
            show_id=show_id,
            scene_hint=scene_hint,
            outfit_hint_female=outfit_female,
            outfit_hint_male=outfit_male,
            action_hint=action_hint,
            for_video_bg=True,
        ),
    }


def normalize_generated_cover(
    source_image: Path,
    output_jpg: Path,
    *,
    mode: str = "blur-fill-composite",
    safe_margin: float = 0.0,
    blur_radius: float = 24.0,
) -> Path:
    from normalize_youtube_cover import normalize_youtube_cover

    output_jpg.parent.mkdir(parents=True, exist_ok=True)
    # blur-fill-composite / contain: pass safe_margin (usually 0 — height-fill, no top/bottom gap).
    margin = safe_margin if mode in ("contain", "blur-fill-composite") else 0.0
    normalize_youtube_cover(
        source_image,
        output_jpg,
        mode=mode,
        safe_margin=margin,
        blur_radius=blur_radius,
    )
    return output_jpg


def prepare_outputs_from_scene(
    *,
    scene_source: Path,
    thumbnail_png: Path,
    video_bg_jpg: Path,
    show_id: str,
    hook_text: str,
    youtube_payload: dict[str, Any] | None = None,
    video_bg_source: Path | None = None,
) -> dict[str, Any]:
    tokens = load_show_tokens(show_id)
    show_visual = get_show_visual(show_id)
    show = __import__("json").loads(SHOW_CONFIG_PATH.read_text(encoding="utf-8"))["shows"][show_id]
    cover_text = parse_cover_text_layers(hook_text, youtube_payload)

    normalized_scene = scene_source.with_suffix(".scene.norm.jpg")
    normalize_generated_cover(scene_source, normalized_scene, mode="auto")

    video_bg_path = video_bg_source
    if video_bg_source and video_bg_source.is_file():
        normalized_bg = video_bg_source.with_suffix(".bg.norm.jpg")
        normalize_generated_cover(video_bg_source, normalized_bg, mode="auto")
        video_bg_path = normalized_bg

    report = compose_thumbnail_from_scene(
        normalized_scene,
        tokens=tokens,
        cover_text=cover_text,
        level_badge=show_visual.level_badge,
        show_label=str(show.get("publicName", tokens.label)),
        thumbnail_png=thumbnail_png,
        video_bg_jpg=video_bg_jpg,
        video_bg_scene=video_bg_path,
    )
    report["showId"] = show_id
    report["hookText"] = hook_text
    return report


def prepare_outputs_from_generated(
    *,
    cover_source: Path,
    thumbnail_png: Path,
    video_bg_jpg: Path,
    video_bg_source: Path | None = None,
) -> dict[str, str]:
    if not cover_source.is_file():
        raise FileNotFoundError(f"Generated cover not found: {cover_source}")

    thumbnail_png.parent.mkdir(parents=True, exist_ok=True)
    cover_jpg = thumbnail_png.with_name(f"{thumbnail_png.stem}_cover.jpg")
    # Thumbnail = blurred cover fill (seamless 16:9, no side bars) + sharp cover
    # centered on top (all baked-in text preserved, never cropped).
    normalize_generated_cover(cover_source, cover_jpg, mode="blur-fill-composite", safe_margin=0.0)

    from PIL import Image

    with Image.open(cover_jpg) as image:
        image.convert("RGB").save(thumbnail_png, format="PNG")

    # Video bg = direct top-crop fill (original method). Clean 16:9 from the
    # dedicated bg_source (no text), no blur needed.
    bg_source = video_bg_source if video_bg_source and video_bg_source.is_file() else cover_source
    normalize_generated_cover(bg_source, video_bg_jpg, mode="auto")

    return {
        "mode": "generated-cover",
        "coverSource": str(cover_source).replace("\\", "/"),
        "videoBgSource": str(bg_source).replace("\\", "/"),
        "thumbnailPng": str(thumbnail_png).replace("\\", "/"),
        "videoBgJpg": str(video_bg_jpg).replace("\\", "/"),
    }


def prepare_outputs_from_baked_scene(
    *,
    cover_source: Path,
    thumbnail_png: Path,
    video_bg_jpg: Path,
    video_bg_source: Path | None = None,
) -> dict[str, str]:
    """Export a native 16:9 cover whose typography is baked into the scene."""
    if not cover_source.is_file():
        raise FileNotFoundError(f"Generated baked cover not found: {cover_source}")

    thumbnail_png.parent.mkdir(parents=True, exist_ok=True)
    normalize_generated_cover(cover_source, thumbnail_png, mode="auto")
    bg_source = video_bg_source if video_bg_source and video_bg_source.is_file() else cover_source
    normalize_generated_cover(bg_source, video_bg_jpg, mode="auto")
    return {
        "mode": "native-16x9-baked-cover",
        "coverSource": str(cover_source).replace("\\", "/"),
        "videoBgSource": str(bg_source).replace("\\", "/"),
        "thumbnailPng": str(thumbnail_png).replace("\\", "/"),
        "videoBgJpg": str(video_bg_jpg).replace("\\", "/"),
    }
