from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .workspace import atomic_write_json, ensure_workspace


def _caption_pages(text: str, max_chars: int = 50) -> list[str]:
    words = text.split()
    pages: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and len(candidate) > max_chars:
            pages.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        pages.append(" ".join(current))
    return pages or [text]


def build_render_props(manifest: dict[str, Any]) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for turn in manifest["turns"]:
        pages = _caption_pages(str(turn["text"]))
        start = float(turn["startSec"])
        end = float(turn["endSec"])
        page_duration = (end - start) / len(pages)
        for index, page in enumerate(pages):
            scenes.append(
                {
                    "speaker": turn["speaker"],
                    "text": page,
                    "startSec": round(start + index * page_duration, 3),
                    "endSec": round(start + (index + 1) * page_duration, 3),
                }
            )
    return {
        "format": manifest["format"],
        "cefr": manifest["cefr"],
        "durationSec": manifest["durationSec"],
        "hook": manifest["hook"],
        "hookEndSec": manifest.get("hookEndSec", 1.5),
        "scenes": scenes,
        "prompt": manifest["prompt"],
        "answer": manifest["answer"],
        "promptStartSec": manifest["promptStartSec"],
        "answerStartSec": manifest["answerStartSec"],
        "backgroundImage": manifest["visual"]["backgroundImage"],
        "brandLogo": manifest["visual"]["brandLogo"],
        "cta": manifest["cta"],
    }


def _remotion_command(repo_root: Path) -> list[str]:
    executable = "remotion.cmd" if os.name == "nt" else "remotion"
    direct_candidates = [
        repo_root / "node_modules" / ".bin" / executable,
        repo_root.parent.parent / "node_modules" / ".bin" / executable,
    ]
    for candidate in direct_candidates:
        if candidate.is_file():
            return [str(candidate)]
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("Remotion is unavailable. Run npm install in the repository.")
    return [npm, "exec", "--", "remotion"]


def _browser_executable() -> Path | None:
    configured = os.environ.get("REMOTION_BROWSER_EXECUTABLE")
    candidates = [
        Path(configured).resolve() if configured else None,
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
    ]
    return next((path for path in candidates if path is not None and path.is_file()), None)


def _mux_audio(silent_video: Path, audio_path: Path, output_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to mux Shorts audio")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(silent_video),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-b:a",
            "192k",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-t",
            str(output_path_duration(silent_video)),
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
    )


def output_path_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required to measure rendered Shorts")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return round(float(result.stdout.strip()), 3)


def render_short(
    repo_root: Path,
    manifest: dict[str, Any],
    *,
    audio_path: Path | None = None,
) -> Path:
    workspace = ensure_workspace(repo_root, str(manifest["shortId"]))
    background_image = manifest.get("visual", {}).get("backgroundImage")
    if not background_image:
        raise ValueError("A generated editorial background is required before rendering")
    background_path = repo_root / "public" / str(background_image)
    if not background_path.is_file():
        raise FileNotFoundError(f"Short background image does not exist: {background_path}")
    brand_logo = repo_root / "public" / str(manifest["visual"]["brandLogo"])
    if not brand_logo.is_file():
        raise FileNotFoundError(f"Short brand logo does not exist: {brand_logo}")
    props_path = workspace / "reports" / "render_props.json"
    atomic_write_json(props_path, build_render_props(manifest))
    silent_path = workspace / "video" / f"{manifest['shortId']}.silent.mp4"
    output_path = workspace / "video" / f"{manifest['shortId']}.mp4"
    command = [
        *_remotion_command(repo_root),
        "render",
        "src/shorts/index.ts",
        "EnglishListeningRoomShort",
        str(silent_path),
        f"--props={props_path}",
        "--codec=h264",
        "--crf=18",
        "--pixel-format=yuv420p",
    ]
    browser = _browser_executable()
    if browser is not None:
        command.append(f"--browser-executable={browser}")
    subprocess.run(command, cwd=repo_root, check=True)
    if audio_path is not None:
        if not audio_path.is_file():
            raise FileNotFoundError(f"Short audio does not exist: {audio_path}")
        _mux_audio(silent_path, audio_path, output_path)
        silent_path.unlink()
    else:
        silent_path.replace(output_path)
    return output_path
