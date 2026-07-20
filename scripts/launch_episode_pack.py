"""Launch episode pack in background — audiobook monitor parity.

Agents: use --detach so the job survives Cursor shell timeouts.
Humans: omit --detach to run in the foreground terminal.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
PACK_SCRIPT = REPO_ROOT / "workspace" / "shows" / "tools" / "pack_episode.py"


def build_pack_cmd(args: argparse.Namespace, log_path: Path) -> list[str]:
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
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch episode pack (foreground or detached background).")
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
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    parser.add_argument(
        "--detach",
        action="store_true",
        help="Background Popen (agent long jobs). Prints pid + log path and exits immediately.",
    )
    args = parser.parse_args()

    log_path = Path(args.log) if args.log else REPO_ROOT / "logs" / f"episode_pack_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_pack_cmd(args, log_path)

    print(f"log={log_path.as_posix()}", flush=True)
    print(f"cmd={' '.join(cmd)}", flush=True)

    if args.detach:
        with log_path.open("a", encoding="utf-8", newline="\n") as log_file:
            log_file.write(f"[detach start] {' '.join(cmd)}\n")
            log_file.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"},
            )
        print(f"pid={proc.pid}", flush=True)
        print("Pack running in background. Tail log for progress.", flush=True)
        return 0

    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
