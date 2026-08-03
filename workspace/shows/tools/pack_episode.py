"""Formal episode pack pipeline — audiobook monitor style.

Ordered steps (see docs/shows/ELR_YOUTUBE_PUBLISH.md):
  0. Thumbnail + video bg  render_episode_thumbnail.py  (hookText consistency check first)
  1. QC gate   check_episode.py  (layer1 fast; optional ASR on flagged turns)
  2. Master    master_episode_audio.py
  3. Subtitles generate_episode_subtitles.py  (--scripted-only, audiobook timing)
  4. Compose   compose_episode_video.py
  5. YouTube packaging  prepare_episode_youtube_packaging.py  (title + description with chapter timestamps, post-audio)
  6. Export    export_episode_to_youtube_dir.py

Run via scripts/run_episode_pack.py in your terminal — not inside Cursor agent shell.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parents[2]
DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"

sys.path.insert(0, str(TOOLS))
from episode_artifacts import artifact_paths  # noqa: E402
from episode_youtube_meta import hook_text_matches_title, sync_youtube_json  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class PackLogger:
    def __init__(self, log_path: Path | None) -> None:
        self._file = None
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = log_path.open("a", encoding="utf-8", newline="\n")

    def close(self) -> None:
        if self._file is not None:
            self._file.close()

    def write(self, message: str) -> None:
        line = message.rstrip()
        print(line, flush=True)
        if self._file is not None:
            self._file.write(line + "\n")
            self._file.flush()

    def log(self, message: str) -> None:
        self.write(f"[{utc_now()}] {message}")


def run_step(
    logger: PackLogger,
    label: str,
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> int:
    logger.log(f"{label} started")
    logger.write(f"  command: {' '.join(cmd)}")
    started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env or os.environ.copy(),
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        logger.write(f"    {line.rstrip()}")
    code = int(proc.wait())
    elapsed = time.monotonic() - started
    logger.log(f"{label} finished in {elapsed:.1f}s (exit {code})")
    return code


def _extract_draft_title(draft_path: Path) -> str:
    """Pull the `Title:` line from a draft.md frontmatter block."""
    if not draft_path.is_file():
        return ""
    for line in draft_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("title:"):
            return stripped.split(":", 1)[1].strip().strip("\"'")
        if stripped.lower().startswith("title："):
            return stripped.split("：", 1)[1].strip().strip("\"'")
    return ""


def check_hook_consistency(
    log: PackLogger,
    *,
    manifest: dict[str, Any],
    workspace: Path,
    episode: str,
) -> int:
    """Step 0a: sync then verify youtube.json hookText matches draft/manifest title.

    ``hookText`` is auto-derived from the draft ``Title:`` line (see
    ``episode_youtube_meta.py``). Agents hand-author cover scene/outfit only.
    """
    paths = artifact_paths(workspace, episode)
    youtube_path = paths["youtube"]
    if not youtube_path.is_file():
        log.log(f"error: missing {youtube_path.name} — create it with coverScene/Action/Outfit fields")
        return 2

    sync = sync_youtube_json(workspace, episode, manifest=manifest, write=True)
    if sync.get("changed"):
        log.log(
            f"synced youtube.json from draft Title → hookText='{sync.get('hookText')}'"
        )

    youtube = load_json(youtube_path)
    hook_text = str(youtube.get("hookText", "")).strip()
    if not hook_text:
        log.log("error: youtube.json hookText is empty after sync — check draft Title:")
        return 2

    title = str(sync.get("title") or manifest.get("title", "")).strip()
    if not title:
        title = _extract_draft_title(paths["draft"])

    if not title:
        log.log("warn: could not resolve episode title for hook consistency check — skipping comparison")
        return 0

    if hook_text_matches_title(hook_text, title):
        log.log(f"hookText consistent with title: '{hook_text}'")
        return 0

    log.log(f"error: hookText '{hook_text}' does not match title '{title}'")
    log.log("fix: update draft.md Title: — hookText is derived automatically at pack time")
    return 2


def run_thumbnail_step(
    log: PackLogger,
    *,
    show: str,
    episode: str,
    workspace: Path,
    manifest: dict[str, Any],
    py: str,
    env: dict[str, str],
) -> int:
    """Step 0: hookText consistency check, then render thumbnail + video bg."""
    code = check_hook_consistency(log, manifest=manifest, workspace=workspace, episode=episode)
    if code != 0:
        return code

    paths = artifact_paths(workspace, episode)
    scene_source = paths["coverBakedScene"]
    video_bg_source = paths["videoBgSource16x9"]

    if not scene_source.is_file():
        log.log(f"error: missing {scene_source.name} — run render_episode_thumbnail.py --print-prompts first,")
        log.log("       generate a native 16:9 baked cover with the image-gen tool, then save it as that file.")
        return 2

    cmd = [
        py,
        "-u",
        str(TOOLS / "render_episode_thumbnail.py"),
        "--show",
        show,
        "--episode",
        episode,
        "--workspace",
        str(workspace.resolve()),
        "--from-baked-scene",
        str(scene_source.resolve()),
    ]
    if video_bg_source.is_file():
        cmd.extend(["--video-bg-from", str(video_bg_source.resolve())])

    code = run_step(log, "thumbnail", cmd, cwd=REPO, env=env)
    if code != 0:
        return code

    report_path = paths["thumbnailReport"]
    if report_path.is_file():
        report = load_json(report_path)
        log.log(f"thumbnail report: {report.get('mode', 'unknown')} -> {report.get('thumbnailPng', '')}")
    return 0


def pack_episode(
    *,
    show: str,
    episode: str,
    workspace: Path,
    episode_num: int = 1,
    youtube_root: Path | None = None,
    skip_thumbnail: bool = False,
    skip_qc: bool = False,
    skip_master: bool = False,
    skip_export: bool = False,
    qc_no_asr: bool = False,
    auto_qc_repair: bool = True,
    qc_repair_max_rounds: int = 3,
    compose_encoder: str = "libx264",
    logger: PackLogger | None = None,
) -> int:
    log = logger or PackLogger(None)
    manifest_path = workspace / f"000_{episode}.episode_manifest.json"
    if not manifest_path.is_file():
        log.log(f"error: missing manifest {manifest_path}")
        return 2

    manifest = load_json(manifest_path)
    gap = float(manifest.get("renderSettings", {}).get("interTurnSilenceSec", 0.3))
    master_dir = workspace / "audio" / "_master_turns"

    py = str(DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else Path(sys.executable))
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # 0 — Thumbnail + video bg (with hookText consistency check)
    if not skip_thumbnail:
        code = run_thumbnail_step(
            log,
            show=show,
            episode=episode,
            workspace=workspace,
            manifest=manifest,
            py=py,
            env=env,
        )
        if code != 0:
            return code

    # 1 — QC (audiobook-style gate; auto-repair blocking turns before strict fail)
    if not skip_qc:
        if auto_qc_repair:
            repair_cmd = [
                py,
                "-u",
                str(TOOLS / "repair_episode_qc.py"),
                "--manifest",
                str(manifest_path.resolve()),
                "--max-rounds",
                str(qc_repair_max_rounds),
                "--device",
                "cuda",
                "--write-report",
                "--no-gpu-lock",
            ]
            if qc_no_asr:
                pass  # repair defaults to layer-1 QC (fast)
            else:
                repair_cmd.append("--with-asr")
            code = run_step(log, "qc-repair", repair_cmd, cwd=REPO, env=env)
            if code != 0:
                log.log("QC auto-repair failed — fix turns manually or rerun with --no-auto-qc-repair --skip-qc")
                return code
        qc_cmd = [
            py,
            "-u",
            str(TOOLS / "check_episode.py"),
            "--manifest",
            str(manifest_path.resolve()),
            "--write-report",
            "--strict",
        ]
        if qc_no_asr:
            qc_cmd.append("--no-asr")
        code = run_step(log, "qc", qc_cmd, cwd=REPO, env=env)
        if code != 0:
            log.log("QC step failed — fix turns or rerun with --skip-qc after human review")
            return code

    # 2 — Master
    master_wav = workspace / "audio" / f"000_{episode}.master.wav"
    if skip_master and master_wav.is_file():
        log.log(f"master skipped (exists): {master_wav.name}")
    else:
        code = run_step(
            log,
            "master",
            [py, "-u", str(TOOLS / "master_episode_audio.py"), "--manifest", str(manifest_path.resolve())],
            cwd=REPO,
            env=env,
        )
        if code != 0:
            return code

    # 3 — Subtitles (audiobook timing: no Whisper per turn)
    if not master_dir.is_dir():
        log.log(f"error: missing {master_dir} — run master first")
        return 2
    sub_cmd = [
        py,
        "-u",
        str(TOOLS / "generate_episode_subtitles.py"),
        "--show",
        show,
        "--episode",
        episode,
        "--workspace",
        str(workspace.resolve()),
        "--master-turns-dir",
        str(master_dir.resolve()),
        "--scripted-only",
        "--gap-sec",
        str(gap),
    ]
    code = run_step(log, "subtitles", sub_cmd, cwd=REPO, env=env)
    if code != 0:
        return code

    # 4 — Compose
    code = run_step(
        log,
        "compose",
        [
            py,
            "-u",
            str(TOOLS / "compose_episode_video.py"),
            "--show",
            show,
            "--episode",
            episode,
            "--workspace",
            str(workspace.resolve()),
            "--encoder",
            compose_encoder,
        ],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        return code

    # 5 — YouTube packaging (title + description with chapter timestamps)
    # Runs after audio render/master so turn durations are real. The export step
    # (6) consumes the description file this writes.
    code = run_step(
        log,
        "youtube-packaging",
        [
            py,
            "-u",
            str(TOOLS / "prepare_episode_youtube_packaging.py"),
            "--workspace",
            str(workspace.resolve()),
            "--episode",
            episode,
        ],
        cwd=REPO,
        env=env,
    )
    if code != 0:
        return code

    # 6 — Export
    if not skip_export:
        export_cmd = [
            py,
            "-u",
            str(TOOLS / "export_episode_to_youtube_dir.py"),
            "--show",
            show,
            "--episode-num",
            str(episode_num),
            "--workspace",
            str(workspace.resolve()),
        ]
        if youtube_root is not None:
            export_cmd.extend(["--youtube-root", str(youtube_root)])
        code = run_step(log, "export", export_cmd, cwd=REPO, env=env)
        if code != 0:
            return code

    log.log("pack complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Audiobook-style episode pack: thumbnail → QC → master → subs → compose → export.")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--log", default="", help="Append log file (default: logs/episode_pack_<ts>.log)")
    parser.add_argument("--skip-thumbnail", action="store_true", help="Skip step 0 (thumbnail + video bg + hookText check)")
    parser.add_argument("--skip-qc", action="store_true")
    parser.add_argument("--skip-master", action="store_true", help="Reuse existing master.wav")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--qc-no-asr", action="store_true", help="QC layer 1 only (fast, no Whisper)")
    parser.add_argument(
        "--no-auto-qc-repair",
        action="store_true",
        help="Skip repair_episode_qc auto-fix before strict QC (not recommended for Series C).",
    )
    parser.add_argument("--qc-repair-max-rounds", type=int, default=3)
    parser.add_argument(
        "--compose-encoder",
        default="libx264",
        help="ffmpeg video encoder for compose step (default libx264 — CPU encode, leaves GPU for VoxCPM).",
    )
    args = parser.parse_args()

    log_path = Path(args.log) if args.log else REPO / "logs" / f"episode_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = PackLogger(log_path)
    logger.log(f"pack started show={args.show} episode={args.episode}")
    logger.log(f"log={log_path.as_posix()}")

    try:
        code = pack_episode(
            show=args.show,
            episode=args.episode,
            workspace=Path(args.workspace),
            episode_num=args.episode_num,
            youtube_root=Path(args.youtube_root),
            skip_thumbnail=args.skip_thumbnail,
            skip_qc=args.skip_qc,
            skip_master=args.skip_master,
            skip_export=args.skip_export,
            qc_no_asr=args.qc_no_asr,
            auto_qc_repair=not args.no_auto_qc_repair,
            qc_repair_max_rounds=args.qc_repair_max_rounds,
            compose_encoder=args.compose_encoder,
            logger=logger,
        )
    finally:
        logger.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
