from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(__file__).resolve().parent
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.cover_pipeline import (  # noqa: E402
    build_prompt_bundle,
    prepare_outputs_from_baked_scene,
    prepare_outputs_from_generated,
    prepare_outputs_from_scene,
)
from media.thumbnail_compositor import save_thumbnail_outputs  # noqa: E402
from media.thumbnail_tokens import tokens_from_show  # noqa: E402
from episode_artifacts import artifact_paths, load_json, write_json  # noqa: E402

SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"


def resolve_hook_text(args: argparse.Namespace, paths: dict[str, Path]) -> str:
    if args.hook:
        return args.hook.strip()
    if paths["youtube"].is_file():
        payload = load_json(paths["youtube"])
        hook = str(payload.get("hookText", "")).strip()
        if hook:
            return hook
    raise ValueError("Provide --hook or create youtube.json with hookText")


def load_youtube_payload(paths: dict[str, Path]) -> dict:
    if paths["youtube"].is_file():
        return load_json(paths["youtube"])
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare ELR episode thumbnail + video background.")
    parser.add_argument("--show", required=True, help="series_a | series_b | series_c")
    parser.add_argument("--episode", required=True, help="episode_001")
    parser.add_argument("--workspace", required=True, help="Episode workspace directory")
    parser.add_argument("--hook", help="Override hook text (otherwise read youtube.json)")
    parser.add_argument(
        "--from-image",
        help="Legacy generated cover image with typography baked in.",
    )
    parser.add_argument(
        "--from-scene",
        help="Native 16:9 no-text scene; optional programmatic title-overlay workflow.",
    )
    parser.add_argument(
        "--from-baked-scene",
        help="Native 16:9 final thumbnail with model-rendered typography; production default.",
    )
    parser.add_argument("--video-bg-from", help="Generated background scene without text")
    parser.add_argument("--dev-pil", action="store_true", help="Dev-only PIL compositor fallback")
    parser.add_argument("--print-prompts", action="store_true", help="Print image-generation prompts")
    args = parser.parse_args()

    paths = artifact_paths(Path(args.workspace), args.episode)
    # Ensure output subdirs exist before writing thumbnail/video bg/report.
    for key in ("thumbnailPng", "videoBgJpg", "thumbnailReport"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
    hook_text = resolve_hook_text(args, paths)
    youtube_payload = load_youtube_payload(paths)

    if args.print_prompts:
        print(json.dumps(build_prompt_bundle(show_id=args.show, hook_text=hook_text, youtube_payload=youtube_payload), ensure_ascii=False, indent=2))
        return 0

    if args.from_baked_scene:
        report = prepare_outputs_from_baked_scene(
            cover_source=Path(args.from_baked_scene),
            thumbnail_png=paths["thumbnailPng"],
            video_bg_jpg=paths["videoBgJpg"],
            video_bg_source=Path(args.video_bg_from) if args.video_bg_from else None,
        )
        report["hookText"] = hook_text
        report["showId"] = args.show
    elif args.from_scene:
        report = prepare_outputs_from_scene(
            scene_source=Path(args.from_scene),
            thumbnail_png=paths["thumbnailPng"],
            video_bg_jpg=paths["videoBgJpg"],
            show_id=args.show,
            hook_text=hook_text,
            youtube_payload=youtube_payload,
            video_bg_source=Path(args.video_bg_from) if args.video_bg_from else None,
        )
        report["mode"] = "native-16x9-scene"
    elif args.from_image:
        report = prepare_outputs_from_generated(
            cover_source=Path(args.from_image),
            thumbnail_png=paths["thumbnailPng"],
            video_bg_jpg=paths["videoBgJpg"],
            video_bg_source=Path(args.video_bg_from) if args.video_bg_from else None,
        )
        report["hookText"] = hook_text
        report["showId"] = args.show
        report["mode"] = "generated-cover"
    elif args.dev_pil:
        show = load_json(SHOW_CONFIG_PATH)["shows"][args.show]
        tokens = tokens_from_show(show, args.show)
        report = save_thumbnail_outputs(
            tokens,
            hook_text,
            paths["thumbnailPng"],
            paths["videoBgJpg"],
        )
        report["mode"] = "dev-pil"
    else:
        raise ValueError(
            "Production requires --from-baked-scene from built-in image generation (native 16:9 with baked typography). "
            "Use --print-prompts for coverImagePrompt + videoBgImagePrompt. "
            "--from-scene is the optional programmatic-overlay workflow; --from-image is only for legacy 3:2 covers."
        )

    write_json(paths["thumbnailReport"], report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
