from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[5] / "workspace" / "characters" / "registry.json"


@dataclass(frozen=True)
class HostVisual:
    host_id: str
    name: str
    show_id: str
    gender: str
    age_band: str
    role: str
    visual_anchor: str
    default_wardrobe: str
    palette: str


@dataclass(frozen=True)
class ShowVisual:
    show_id: str
    female_host: HostVisual
    male_host: HostVisual
    level_badge: str
    scene_mood: str
    layout: dict[str, Any]


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _host_from_dict(payload: dict[str, Any]) -> HostVisual:
    return HostVisual(
        host_id=str(payload["hostId"]),
        name=str(payload["name"]),
        show_id=str(payload["showId"]),
        gender=str(payload["gender"]),
        age_band=str(payload["ageBand"]),
        role=str(payload["role"]),
        visual_anchor=str(payload["visualAnchor"]),
        default_wardrobe=str(payload["defaultWardrobe"]),
        palette=str(payload["palette"]),
    )


def get_show_visual(show_id: str) -> ShowVisual:
    registry = load_registry()
    show = registry["shows"][show_id]
    hosts = registry["hosts"]
    return ShowVisual(
        show_id=show_id,
        female_host=_host_from_dict(hosts[show["femaleHost"]]),
        male_host=_host_from_dict(hosts[show["maleHost"]]),
        level_badge=str(show["levelBadge"]),
        scene_mood=str(show["sceneMood"]),
        layout=registry["layout"],
    )


def host_visual_block(host: HostVisual, *, side: str, outfit_hint: str = "") -> str:
    wardrobe = outfit_hint.strip() or host.default_wardrobe
    return (
        f"{host.name} ({host.gender}, {host.age_band}, {host.role}) on the {side}: "
        f"{host.visual_anchor}. Wearing {wardrobe}. Palette hints: {host.palette}."
    )


def build_scene_image_prompt(
    *,
    show_id: str,
    scene_hint: str = "",
    outfit_hint_female: str = "",
    outfit_hint_male: str = "",
    action_hint: str = "",
    for_video_bg: bool = False,
) -> str:
    show = get_show_visual(show_id)
    layout = show.layout
    scene = scene_hint.strip().rstrip(".") or show.scene_mood.rstrip(".")
    action = action_hint.strip().rstrip(".") or "engaged in natural podcast conversation, looking toward center"
    female_side = str(layout.get("femaleHostSide", "left"))
    male_side = str(layout.get("maleHostSide", "right"))

    hosts_block = " ".join(
        [
            host_visual_block(show.female_host, side=female_side, outfit_hint=outfit_hint_female),
            host_visual_block(show.male_host, side=male_side, outfit_hint=outfit_hint_male),
        ]
    )

    center_rule = (
        "Leave the center third of the frame relatively clean and uncluttered for subtitles. "
        "Absolutely no text, letters, logos, or watermarks anywhere in the image."
        if for_video_bg
        else (
            "Leave the center third relatively clean for later text overlay. "
            "Absolutely no text, letters, logos, or watermarks in the generated image."
        )
    )

    return (
        f"YouTube podcast scene illustration, exact size 2560x1440 pixels (2K 16:9). "
        f"Art style: {layout.get('artStyle')}. "
        f"Symmetrical composition: {layout.get('deskLayout')}. "
        f"{hosts_block} "
        f"Scene: {scene}. Action: {action}. "
        f"Accent mood for show {show_id}, level {show.level_badge}. "
        f"{center_rule} "
        "Bright warm inviting lighting. "
        "Draw hosts as stylized illustrated characters with comic outlines and flat shading — "
        "never photoreal faces, never live-action humans, never 3D render skin. No solid black void."
    )


def build_cover_image_prompt(
    *,
    show_id: str,
    hook_text: str,
    youtube_payload: dict[str, Any] | None = None,
) -> str:
    from media.thumbnail_tokens import load_show_tokens

    tokens = load_show_tokens(show_id)
    show = get_show_visual(show_id)
    payload = youtube_payload or {}
    cover_text = parse_cover_text_layers(hook_text, payload)
    scene_hint = str(payload.get("coverScene", "")).strip()
    outfit_female = str(payload.get("coverOutfitFemale", "")).strip()
    outfit_male = str(payload.get("coverOutfitMale", "")).strip()
    action_hint = str(payload.get("coverAction", "")).strip()

    scene_block = build_scene_image_prompt(
        show_id=show_id,
        scene_hint=scene_hint,
        outfit_hint_female=outfit_female,
        outfit_hint_male=outfit_male,
        action_hint=action_hint,
        for_video_bg=True,
    ).replace(
        "Leave the center third of the frame relatively clean and uncluttered for subtitles. "
        "Absolutely no text, letters, logos, or watermarks anywhere in the image.",
        "Integrate a bold title into the centre of the artwork; do not use a blank slide-like rectangle.",
    )

    text_lines = [
        f'Top-left small level badge: "{show.level_badge}".',
        f'Top-right small show label: "{tokens.label.split(" ·", 1)[0].title()}".',
    ]
    if cover_text.get("prefix"):
        text_lines.append(f'Small connector text: "{cover_text["prefix"]}".')
    if cover_text.get("main"):
        text_lines.append(f'Largest central headline: "{cover_text["main"]}".')
    if cover_text.get("suffix"):
        text_lines.append(f'Accent pill directly below: "{cover_text["suffix"]}".')

    return (
        f"{scene_block} "
        "This is the final native 16:9 YouTube thumbnail: bake the following exact typography into the image, "
        "with high contrast and natural integration into the scene. "
        f"{' '.join(text_lines)} "
        f"Use accent color {tokens.bar_color}. Render every quoted phrase exactly. "
        "No extra text, no duplicate labels, no watermark."
    )


def parse_cover_text_layers(hook_text: str, payload: dict[str, Any] | None = None) -> dict[str, str]:
    if payload:
        cover_text = payload.get("coverText")
        if isinstance(cover_text, dict):
            return {
                "prefix": str(cover_text.get("prefix", "")).strip(),
                "main": str(cover_text.get("main", "")).strip(),
                "suffix": str(cover_text.get("suffix", "")).strip(),
                "badge": str(cover_text.get("badge", "")).strip(),
            }

    hook = " ".join(hook_text.strip().split())
    if not hook:
        return {"prefix": "", "main": "ENGLISH PODCAST", "suffix": "", "badge": ""}

    match = re.match(r"^(Practice|Talk About|How To)\s+(.+)$", hook, flags=re.IGNORECASE)
    if match:
        prefix = match.group(1).title().replace("How To", "How To")
        rest = match.group(2).strip()
        if "(" in rest:
            main, suffix = rest.split("(", 1)
            return {
                "prefix": prefix,
                "main": main.strip().upper(),
                "suffix": suffix.rstrip(")").strip().upper(),
                "badge": "",
            }
        words = rest.split()
        if len(words) > 4:
            return {
                "prefix": prefix,
                "main": " ".join(words[:4]).upper(),
                "suffix": " ".join(words[4:]).upper(),
                "badge": "",
            }
        return {"prefix": prefix, "main": rest.upper(), "suffix": "", "badge": ""}

    words = hook.split()
    if len(words) <= 4:
        return {"prefix": "", "main": hook.upper(), "suffix": "", "badge": ""}
    return {
        "prefix": "",
        "main": " ".join(words[:4]).upper(),
        "suffix": " ".join(words[4:]).upper(),
        "badge": "",
    }
