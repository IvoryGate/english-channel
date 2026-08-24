"""Stable launcher for pack_episode.py — same pattern as other production monitors.

Run in your own terminal (not Cursor agent shell):

  .\\.conda-env\\python.exe scripts\\run_episode_pack.py ^
    --show series_b --episode episode_001 ^
    --workspace workspace\\shows\\series_b\\episode_001
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
PACK_SCRIPT = REPO_ROOT / "workspace" / "shows" / "tools" / "pack_episode.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from gpu_production_lock import GpuProductionLock  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch episode pack with log file (audiobook-style).")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--log", default="")
    parser.add_argument("--skip-qc", action="store_true")
    parser.add_argument("--skip-master", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--qc-no-asr", action="store_true")
    parser.add_argument("--compose-encoder", default="libx264")
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    args, _unknown = parser.parse_known_args()

    log_path = Path(args.log) if args.log else REPO_ROOT / "logs" / f"episode_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(Path(args.python)),
        "-u",
        str(PACK_SCRIPT),
        "--show",
        args.show,
        "--episode",
        args.episode,
        "--workspace",
        str(Path(args.workspace).resolve()),
        "--episode-num",
        str(args.episode_num),
        "--youtube-root",
        args.youtube_root,
        "--log",
        str(log_path),
    ]
    if args.skip_qc:
        cmd.append("--skip-qc")
    if args.skip_master:
        cmd.append("--skip-master")
    if args.skip_export:
        cmd.append("--skip-export")
    if args.qc_no_asr:
        cmd.append("--qc-no-asr")
    cmd.extend(["--compose-encoder", args.compose_encoder])

    print(f"log={log_path}", flush=True)
    print(f"cmd={' '.join(cmd)}", flush=True)
    label = f"pack_{args.show}_{args.episode}"
    with GpuProductionLock(label):
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
