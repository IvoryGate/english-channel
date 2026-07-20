"""Render a ~2-minute preview of each series' episode_001, composed to video.

For each series (serially — limited GPU, no parallel renders):
  1. Build a trimmed preview manifest with the first N turns (~280 words ≈ 2 min).
  2. Copy youtube.json + video_bg.jpg into the preview workspace.
  3. render_episode.py (one VoxCPM load, serial turns, --no-self-check for speed).
  4. master_episode_audio.py (loudness + denoise).
  5. generate_episode_subtitles.py --scripted-only (audiobook timing).
  6. compose_episode_video.py → preview mp4.

Run detached (long GPU job):
  & $py scripts/run_episode_preview.py --detach
Log: logs/episode_preview_<ts>.log
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from episode_artifacts import load_json, write_json  # noqa: E402

PREVIEW_WORD_TARGET = 280  # ≈2 min at ~140 wpm

SERIES_ORDER = ["series_a", "series_b", "series_c"]


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def pick_preview_turns(turns: list[dict[str, Any]], target: int = PREVIEW_WORD_TARGET) -> list[dict[str, Any]]:
    cum = 0
    out: list[dict[str, Any]] = []
    for turn in turns:
        out.append(turn)
        cum += int(turn.get("wordCount") or 0)
        if cum >= target:
            break
    return out


def build_preview_workspace(series: str, src_workspace: Path, preview_workspace: Path) -> dict[str, Any]:
    """Create the preview workspace with a trimmed manifest + copied assets."""
    src_manifest_path = src_workspace / "000_episode_001.episode_manifest.json"
    manifest = load_json(src_manifest_path)

    preview_turns = pick_preview_turns(manifest["turns"])
    preview_manifest = dict(manifest)
    preview_manifest["episodeId"] = "episode_001_preview"
    preview_manifest["turns"] = preview_turns
    preview_manifest["title"] = str(manifest.get("title", "")) + " [PREVIEW]"
    preview_manifest["estimatedDuration"] = "~2 minutes (preview)"
    preview_manifest["previewOf"] = "episode_001"
    preview_manifest["previewWordCount"] = sum(int(t.get("wordCount") or 0) for t in preview_turns)

    preview_workspace.mkdir(parents=True, exist_ok=True)
    (preview_workspace / "audio" / "turns").mkdir(parents=True, exist_ok=True)
    (preview_workspace / "video").mkdir(parents=True, exist_ok=True)
    (preview_workspace / "subtitles").mkdir(parents=True, exist_ok=True)
    (preview_workspace / "reports").mkdir(parents=True, exist_ok=True)

    preview_manifest_path = preview_workspace / "000_episode_001_preview.episode_manifest.json"
    write_json(preview_manifest_path, preview_manifest)

    # Copy youtube.json (for show tokens / cover fields) — renamed to preview id.
    src_youtube = src_workspace / "000_episode_001.youtube.json"
    if src_youtube.is_file():
        shutil.copy2(src_youtube, preview_workspace / "000_episode_001_preview.youtube.json")

    # Copy the already-generated video_bg.jpg into the preview video dir.
    src_bg = src_workspace / "video" / "000_episode_001.video_bg.jpg"
    if src_bg.is_file():
        shutil.copy2(src_bg, preview_workspace / "video" / "000_episode_001_preview.video_bg.jpg")
    # Also copy thumbnail png if present (export not needed for preview, but harmless).
    src_thumb = src_workspace / "video" / "000_episode_001.thumbnail.png"
    if src_thumb.is_file():
        shutil.copy2(src_thumb, preview_workspace / "video" / "000_episode_001_preview.thumbnail.png")

    return preview_manifest


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> int:
    log("  $ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(cwd), env=env)
    return int(proc.returncode)


def process_series(series: str, py: str, env: dict[str, str]) -> int:
    src_workspace = REPO / "workspace" / "shows" / series / "episode_001"
    preview_workspace = REPO / "workspace" / "shows" / series / "episode_001_preview"
    manifest_path = preview_workspace / "000_episode_001_preview.episode_manifest.json"

    log(f"=== {series} preview ===")
    if not src_workspace.is_dir():
        log(f"  skip: missing source workspace {src_workspace}")
        return 0

    manifest = build_preview_workspace(series, src_workspace, preview_workspace)
    n_turns = len(manifest["turns"])
    n_words = int(manifest.get("previewWordCount") or 0)
    gap = float(manifest.get("renderSettings", {}).get("interTurnSilenceSec", 0.3))
    log(f"  preview: {n_turns} turns, {n_words} words, gap={gap}s")

    # 1 — Render turns (serial, one VoxCPM load)
    log("  step 1: render")
    code = run_cmd(
        [py, "-u", str(TOOLS / "render_episode.py"), "--manifest", str(manifest_path), "--no-self-check"],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        log(f"  render FAILED (exit {code})")
        return code

    # 2 — Master
    log("  step 2: master")
    code = run_cmd(
        [py, "-u", str(TOOLS / "master_episode_audio.py"), "--manifest", str(manifest_path)],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        log(f"  master FAILED (exit {code})")
        return code

    master_dir = preview_workspace / "audio" / "_master_turns"

    # 3 — Subtitles (scripted-only, audiobook timing)
    log("  step 3: subtitles")
    code = run_cmd(
        [
            py, "-u", str(TOOLS / "generate_episode_subtitles.py"),
            "--show", series, "--episode", "episode_001_preview",
            "--workspace", str(preview_workspace.resolve()),
            "--master-turns-dir", str(master_dir.resolve()),
            "--scripted-only", "--gap-sec", str(gap),
        ],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        log(f"  subtitles FAILED (exit {code})")
        return code

    # 4 — Compose video
    log("  step 4: compose")
    code = run_cmd(
        [
            py, "-u", str(TOOLS / "compose_episode_video.py"),
            "--show", series, "--episode", "episode_001_preview",
            "--workspace", str(preview_workspace.resolve()),
        ],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        log(f"  compose FAILED (exit {code})")
        return code

    mp4 = preview_workspace / "video" / "000_episode_001_preview.mp4"
    if mp4.is_file():
        size_mb = mp4.stat().st_size / (1024 * 1024)
        log(f"  DONE: {mp4} ({size_mb:.1f} MB)")
    else:
        log(f"  WARN: expected mp4 not found at {mp4}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Render ~2min preview of each series episode_001, composed to video (serial).")
    parser.add_argument("--series", nargs="*", default=SERIES_ORDER, help="Subset of series to process (default: all three, in order).")
    args = parser.parse_args()

    py = str(REPO / ".conda-env" / "python.exe")
    if not Path(py).is_file():
        py = sys.executable
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    log(f"preview driver started; series={args.series}; python={py}")
    overall = 0
    for series in args.series:
        code = process_series(series, py, env)
        if code != 0:
            overall = code
            log(f"  stopping — {series} failed")
            break
    log(f"preview driver finished (exit {overall})")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
