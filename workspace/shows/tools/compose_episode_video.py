from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(__file__).resolve().parent
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.compose_media_video import compose_media_video  # noqa: E402
from media.thumbnail_tokens import tokens_from_show  # noqa: E402
from episode_artifacts import artifact_paths, load_json, resolve_episode_audio  # noqa: E402

SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"
FONTS_DIR = REPO_ROOT / "assets" / "fonts"
BRANDING_DIR = REPO_ROOT / "assets" / "branding" / "video"
BRANDING_START_EPISODE = 15


def episode_number(episode: str) -> int | None:
    match = re.search(r"(\d+)$", episode)
    return int(match.group(1)) if match else None


def branding_assets_for(episode: str, *, disabled: bool) -> tuple[Path | None, Path | None]:
    number = episode_number(episode)
    if disabled or number is None or number < BRANDING_START_EPISODE:
        return None, None
    intro = BRANDING_DIR / "english-listening-room-intro.mp4"
    outro = BRANDING_DIR / "english-listening-room-outro.mp4"
    missing = [str(path) for path in (intro, outro) if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Branding is required for episode {episode}, but assets are missing: {missing}")
    return intro, outro


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose ELR episode mp4 from bg + audio + ASS karaoke.")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--audio", help="Override episode wav (defaults to master.wav when present)")
    parser.add_argument("--background", help="Override video_bg.jpg path")
    parser.add_argument("--ass", help="Override karaoke ASS path")
    parser.add_argument("--output", help="Override output mp4 path")
    parser.add_argument("--no-branding", action="store_true", help="Do not append the standard ELR intro/outro for this run.")
    parser.add_argument(
        "--encoder",
        default="auto",
        help="Video encoder: auto (NVENC if usable else libx264), libx264, nvenc, qsv, amf.",
    )
    parser.add_argument(
        "--preset",
        default="veryfast",
        help="libx264 preset (default veryfast; quality is gated by -b:v/-maxrate, not preset).",
    )
    args = parser.parse_args()

    paths = artifact_paths(Path(args.workspace), args.episode)
    show = load_json(SHOW_CONFIG_PATH)["shows"][args.show]
    tokens = tokens_from_show(show, args.show)

    background = Path(args.background) if args.background else paths["videoBgJpg"]
    audio = resolve_episode_audio(
        Path(args.workspace),
        args.episode,
        Path(args.audio) if args.audio else None,
    )
    ass_path = Path(args.ass) if args.ass else paths["karaokeAss"]
    output = Path(args.output) if args.output else paths["mp4"]
    intro_mp4, outro_mp4 = branding_assets_for(args.episode, disabled=args.no_branding)

    for label, path in [("background", background), ("audio", audio), ("ass", ass_path)]:
        if not path.is_file():
            raise FileNotFoundError(f"Missing {label}: {path}")

    output.parent.mkdir(parents=True, exist_ok=True)
    paths["videoReport"].parent.mkdir(parents=True, exist_ok=True)
    fonts_dir = FONTS_DIR if FONTS_DIR.is_dir() else None
    report = compose_media_video(
        background_jpg=background,
        audio_wav=audio,
        ass_path=ass_path,
        output_mp4=output,
        intro_mp4=intro_mp4,
        outro_mp4=outro_mp4,
        tokens=tokens,
        fonts_dir=fonts_dir,
        report_path=paths["videoReport"],
        encoder=args.encoder,
        preset=args.preset,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
