from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = Path(__file__).resolve().parent
MEDIA_SCRIPTS = REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(MEDIA_SCRIPTS))

from media.align_media_words import (  # noqa: E402
    align_audio_words,
    align_turn_clips,
    align_turn_clips_scripted,
    spoken_text_from_turns,
    write_words_json,
)
from media.generate_karaoke_ass import write_karaoke_ass  # noqa: E402
from media.generate_media_srt import write_media_srt  # noqa: E402
from media.thumbnail_tokens import tokens_from_show  # noqa: E402
from media.turn_alignment import assign_words_to_turns  # noqa: E402
from episode_artifacts import artifact_paths, load_json, resolve_episode_audio, write_json  # noqa: E402

SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"


def reference_text_for_manifest(manifest: dict[str, Any]) -> str:
    turns = manifest.get("turns") or []
    if turns:
        return spoken_text_from_turns(turns)
    return str(manifest.get("spokenText", "")).strip()


def master_turn_clips_from_dir(workspace: Path, manifest: dict[str, Any], master_dir: Path) -> list[Path]:
    clips: list[Path] = []
    for turn in manifest["turns"]:
        path = master_dir / f"{turn['id']}_{turn['filename']}"
        if not path.is_file():
            raise FileNotFoundError(f"Missing mastered turn: {path}")
        clips.append(path)
    return clips


def main() -> int:
    parser = argparse.ArgumentParser(description="Align episode audio and generate ASS + SRT subtitles.")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument(
        "--audio",
        help="Override episode wav (defaults to master.wav when present, else raw.wav)",
    )
    parser.add_argument(
        "--clips",
        nargs="+",
        help="Optional per-turn wavs (same order as manifest turns). Prefer _master_turns after mastering.",
    )
    parser.add_argument(
        "--master-turns-dir",
        help="Directory with pNNN_turn_NNN.wav clips; resolves list from manifest (no long CLI).",
    )
    parser.add_argument(
        "--scripted-only",
        action="store_true",
        help="Audiobook-style: clip WAV duration + script text only (no Whisper per turn).",
    )
    parser.add_argument("--gap-sec", type=float, default=0.35, help="Silence between clips when using --clips")
    parser.add_argument("--model-size", default="base")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--compute-type", default="int8")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    paths = artifact_paths(workspace, args.episode)
    audio_path = resolve_episode_audio(
        workspace,
        args.episode,
        Path(args.audio) if args.audio else None,
    )

    show = load_json(SHOW_CONFIG_PATH)["shows"][args.show]
    tokens = tokens_from_show(show, args.show)

    manifest_turns: list[dict[str, Any]] = []
    reference_text = ""
    if paths["manifest"].is_file():
        manifest = load_json(paths["manifest"])
        manifest_turns = manifest.get("turns") or []
        reference_text = reference_text_for_manifest(manifest)

    if paths["manifest"].is_file():
        manifest = load_json(paths["manifest"])
        manifest_turns = manifest.get("turns") or []
        reference_text = reference_text_for_manifest(manifest)

    if args.clips:
        if not manifest_turns:
            raise ValueError("--clips requires manifest turns")
        clip_paths = [Path(path) for path in args.clips]
    elif args.master_turns_dir:
        if not manifest_turns:
            raise ValueError("--master-turns-dir requires manifest turns")
        clip_paths = master_turn_clips_from_dir(workspace, manifest, Path(args.master_turns_dir))
    else:
        clip_paths = []

    if clip_paths:
        if args.scripted_only:
            alignment = align_turn_clips_scripted(
                clip_paths,
                manifest_turns,
                gap_sec=args.gap_sec,
            )
        else:
            alignment = align_turn_clips(
                clip_paths,
                manifest_turns,
                gap_sec=args.gap_sec,
                model_size=args.model_size,
                device=args.device,
                compute_type=args.compute_type,
            )
        words = alignment["words"]
        turns = alignment.get("turns") or []
    else:
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio not found: {audio_path}")
        alignment = align_audio_words(
            audio_path,
            model_size=args.model_size,
            device=args.device,
            compute_type=args.compute_type,
            reference_text=reference_text or None,
            vad_filter=False,
        )
        words = alignment["words"]
        turns = assign_words_to_turns(words, manifest_turns) if manifest_turns else []
        if turns:
            alignment["turns"] = turns

    for key in ("wordsJson", "karaokeAss", "srt", "subtitleReport"):
        paths[key].parent.mkdir(parents=True, exist_ok=True)
    write_words_json(paths["wordsJson"], alignment)
    write_karaoke_ass(paths["karaokeAss"], words, tokens, turns=turns or None)
    write_media_srt(paths["srt"], words, turns=turns or None)

    report: dict[str, Any] = {
        "schema": "episode-subtitle-report-v1",
        "showId": args.show,
        "episodeId": args.episode,
        "audio": str(audio_path).replace("\\", "/") if audio_path.is_file() else None,
        "wordsJson": str(paths["wordsJson"]).replace("\\", "/"),
        "karaokeAss": str(paths["karaokeAss"]).replace("\\", "/"),
        "srt": str(paths["srt"]).replace("\\", "/"),
        "wordCount": len(words),
        "turnCount": len(turns),
        "referenceCoverage": alignment.get("referenceCoverage"),
        "alignmentMode": alignment.get("alignmentMode", "whole-file"),
    }
    write_json(paths["subtitleReport"], report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
