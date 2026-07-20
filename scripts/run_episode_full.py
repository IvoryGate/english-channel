"""Full episode pipeline: VoxCPM re-render → master → pack → export.

Run detached for long jobs:
  python scripts/run_episode_full.py --show series_b --episode episode_001 --workspace ... --detach
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

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
RENDER_LAUNCHER = REPO_ROOT / "scripts" / "run_episode_render.py"
PACK_SCRIPT = REPO_ROOT / "workspace" / "shows" / "tools" / "pack_episode.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class JobLogger:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8", newline="\n")

    def close(self) -> None:
        self._file.close()

    def write(self, message: str) -> None:
        line = message.rstrip()
        print(line, flush=True)
        self._file.write(line + "\n")
        self._file.flush()

    def log(self, message: str) -> None:
        self.write(f"[{utc_now()}] {message}")


def run_step(logger: JobLogger, label: str, cmd: list[str], *, cwd: Path) -> int:
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    env.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    logger.log(f"{label} started")
    logger.write(f"  command: {' '.join(cmd)}")
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, env=env)
    if proc.stdout:
        logger.write("  stdout:")
        for line in proc.stdout.rstrip().splitlines():
            logger.write(f"    {line}")
    if proc.stderr:
        logger.write("  stderr:")
        for line in proc.stderr.rstrip().splitlines():
            logger.write(f"    {line}")
    logger.log(f"{label} finished in {time.monotonic() - started:.1f}s (exit {proc.returncode})")
    return int(proc.returncode)


def patch_manifest_cfg(manifest_path: Path, cfg: float) -> None:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    settings = dict(data.get("renderSettings") or {})
    if float(settings.get("cfgValue", cfg)) != cfg:
        settings["cfgValue"] = cfg
        data["renderSettings"] = settings
        manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def run_full_job(args: argparse.Namespace, log_path: Path) -> int:
    logger = JobLogger(log_path)
    workspace = Path(args.workspace).resolve()
    manifest_path = workspace / f"000_{args.episode}.episode_manifest.json"
    py = str(Path(args.python))

    try:
        logger.log(f"full job started show={args.show} episode={args.episode}")
        if not manifest_path.is_file():
            logger.log(f"error: missing manifest {manifest_path}")
            return 2

        patch_manifest_cfg(manifest_path, args.cfg)
        logger.log(f"manifest cfgValue={args.cfg}")

        render_log = log_path.with_suffix(".render.log")
        render_cmd = [
            py,
            "-u",
            str(RENDER_LAUNCHER),
            "--manifest",
            str(manifest_path),
            "--device",
            args.device,
            "--log",
            str(render_log),
        ]
        if args.force:
            render_cmd.append("--force")
        code = run_step(logger, "render", render_cmd, cwd=REPO_ROOT)
        if code != 0:
            return code

        pack_cmd = [
            py,
            "-u",
            str(PACK_SCRIPT),
            "--show",
            args.show,
            "--episode",
            args.episode,
            "--workspace",
            str(workspace),
            "--episode-num",
            str(args.episode_num),
            "--youtube-root",
            args.youtube_root,
            "--log",
            str(log_path.with_suffix(".pack.log")),
        ]
        if args.qc_no_asr:
            pack_cmd.append("--qc-no-asr")
        code = run_step(logger, "pack", pack_cmd, cwd=REPO_ROOT)
        if code != 0:
            return code

        logger.log("full job complete")
        return 0
    finally:
        logger.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Full episode re-render + pack + export.")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cfg", type=float, default=2.15, help="VoxCPM cfgValue written to manifest before render.")
    parser.add_argument("--force", action="store_true", help="Pass --force to render launcher.")
    parser.add_argument("--qc-no-asr", action="store_true", help="Fast QC layer 1 only during pack.")
    parser.add_argument("--log", default="")
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()

    log_path = Path(args.log) if args.log else REPO_ROOT / "logs" / f"episode_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    if args.detach:
        cmd = [str(Path(args.python)), "-u", str(Path(__file__).resolve()), *[a for a in sys.argv[1:] if a != "--detach"]]
        if "--log" not in sys.argv:
            cmd.extend(["--log", str(log_path)])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8", newline="\n") as log_file:
            log_file.write(f"[{utc_now()}] detach start {' '.join(cmd)}\n")
            log_file.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"},
            )
        print(f"log={log_path.as_posix()}", flush=True)
        print(f"pid={proc.pid}", flush=True)
        print("Full re-render + pack running in background.", flush=True)
        return 0

    return run_full_job(args, log_path)


if __name__ == "__main__":
    raise SystemExit(main())
