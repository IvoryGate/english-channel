"""Resume or run serial episode production with global GPU lock.

Safe relaunch after interrupt — skips series whose mp4 already exists unless --force.

  python scripts/resume_episode_production.py --episode episode_003 --episode-num 3
  python scripts/resume_episode_production.py --episode episode_003 --series series_b series_c
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"
SERIES_ORDER = ["series_a", "series_b", "series_c"]

sys.path.insert(0, str(REPO / "scripts"))
from gpu_production_lock import (  # noqa: E402
    DEFAULT_RENDER_BATCH_SIZE,
    GpuProductionLock,
    release_gpu_lock,
    validate_render_batch_size,
)


def utc_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_line(log_path: Path, msg: str) -> None:
    line = f"[{utc_now()}] {msg}"
    print(line, flush=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def mp4_ready(workspace: Path, episode: str) -> bool:
    return (workspace / "video" / f"000_{episode}.mp4").is_file()


def main() -> int:
    parser = argparse.ArgumentParser(description="Serial episode production with GPU lock (resume-safe).")
    parser.add_argument("--episode", required=True)
    parser.add_argument("--episode-num", type=int, required=True)
    parser.add_argument("--series", nargs="*", default=SERIES_ORDER)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--force", action="store_true", help="Re-run even when mp4 exists.")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_RENDER_BATCH_SIZE,
        help=f"Turns per VoxCPM subprocess (default {DEFAULT_RENDER_BATCH_SIZE}).",
    )
    args = parser.parse_args()

    py = str(DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else sys.executable)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO / "logs" / f"resume_{args.episode}_{ts}.log"

    if args.detach:
        cmd = [py, "-u", str(Path(__file__).resolve()), *[a for a in sys.argv[1:] if a != "--detach"]]
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8", newline="\n") as log_file:
            log_file.write(f"[detach start] {' '.join(cmd)}\n")
            log_file.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO),
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"},
            )
        print(f"log={log_path.as_posix()}", flush=True)
        print(f"pid={proc.pid}", flush=True)
        return 0

    validate_render_batch_size(args.batch_size)
    overall = 0
    with GpuProductionLock(f"resume_{args.episode}"):
        try:
            for series in args.series:
                workspace = REPO / "workspace" / "shows" / series / args.episode
                if not args.force and mp4_ready(workspace, args.episode):
                    log_line(log_path, f"SKIP {series} — mp4 exists ({workspace / 'video'})")
                    continue

                # Pack-only when all turns exist but mp4 missing; else full render+pack.
                turns_dir = workspace / "audio" / "turns"
                turn_count = len(list(turns_dir.glob("*.wav"))) if turns_dir.is_dir() else 0
                manifest = workspace / f"000_{args.episode}.episode_manifest.json"
                import json

                expected = 0
                if manifest.is_file():
                    expected = len(json.loads(manifest.read_text(encoding="utf-8")).get("turns") or [])

                if turn_count >= expected and expected > 0 and not args.force:
                    log_line(log_path, f"{series} pack-only ({turn_count}/{expected} turns, no mp4)")
                    cmd = [
                        py, "-u", str(REPO / "scripts" / "run_episode_pack.py"),
                        "--show", series,
                        "--episode", args.episode,
                        "--workspace", str(workspace.resolve()),
                        "--episode-num", str(args.episode_num),
                        "--youtube-root", args.youtube_root,
                        "--qc-no-asr",
                        "--log", str(log_path.with_suffix(f".{series}.pack.log")),
                    ]
                else:
                    log_line(log_path, f"{series} full production (render+pack, batch-size={args.batch_size})")
                    cmd = [
                        py, "-u", str(REPO / "scripts" / "monitor_episode_production.py"),
                        "--show", series,
                        "--episode", args.episode,
                        "--workspace", str(workspace.resolve()),
                        "--episode-num", str(args.episode_num),
                        "--youtube-root", args.youtube_root,
                        "--batch-size", str(args.batch_size),
                        "--qc-no-asr",
                        "--log", str(log_path.with_suffix(f".{series}.log")),
                    ]
                    if args.force:
                        cmd.append("--force")

                log_line(log_path, "  $ " + " ".join(cmd))
                proc = subprocess.run(cmd, cwd=str(REPO), env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"})
                if proc.returncode != 0:
                    log_line(log_path, f"STOP {series} exit={proc.returncode}")
                    overall = int(proc.returncode)
                    break
                log_line(log_path, f"{series} OK")
            log_line(log_path, f"resume finished exit={overall}")
        finally:
            release_gpu_lock()
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
