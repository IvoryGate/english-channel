"""Launch episode renders the same way audiobook monitor launches chapters.

Uses subprocess with repo cwd + log files. Avoids nesting GPU jobs inside
Cursor/PowerShell Wait chains that destabilize long CUDA runs on 8GB laptops.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
DEFAULT_SCRIPT = REPO_ROOT / "workspace" / "shows" / "tools" / "render_episode.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def main() -> int:
    parser = argparse.ArgumentParser(description="Stable audiobook-style episode render launcher.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--segments", default="", help="Optional turn ids, e.g. p003")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--log", default="", help="Log path; default logs/episode_render_<ts>.log")
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    args = parser.parse_args()

    os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    log_path = Path(args.log) if args.log else REPO_ROOT / "logs" / f"episode_render_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(Path(args.python)),
        "-u",
        str(DEFAULT_SCRIPT),
        "--manifest",
        str(Path(args.manifest).resolve()),
        "--device",
        args.device,
    ]
    if args.segments:
        cmd.extend(["--segments", args.segments])
    if args.skip_existing:
        cmd.append("--skip-existing")
    if args.force:
        cmd.append("--force")

    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        log.write(f"[{utc_now()}] start {' '.join(cmd)}\n")
        log.flush()
        print(f"log={log_path}", flush=True)
        print(f"cmd={' '.join(cmd)}", flush=True)
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=os.environ.copy(),
        )
        log.write(proc.stdout or "")
        if not (proc.stdout or "").endswith("\n"):
            log.write("\n")
        log.write(f"[{utc_now()}] exit={proc.returncode}\n")
        log.flush()
        # Mirror to console for interactive use.
        sys.stdout.write(proc.stdout or "")
        sys.stdout.flush()
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
