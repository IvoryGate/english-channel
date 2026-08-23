"""Run full production for all three series' episode_001, serially.

For each series (A → B → C), one after another (limited GPU — no parallel renders):
  monitor_episode_production.py (per-turn render with retry → pack: thumbnail → QC → master → subs → compose → youtube packaging → export)

Resume-safe: monitor_render skips turns whose WAV already exists, so an
interrupted run can be re-launched without --force.

Launch detached (long GPU job):
  & $py scripts/run_all_series_full.py --detach
Log: logs/all_series_full_<ts>.log
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"
sys.path.insert(0, str(REPO / "scripts"))
from gpu_production_lock import acquire_gpu_lock, DEFAULT_RENDER_BATCH_SIZE, release_gpu_lock, validate_render_batch_size  # noqa: E402

# series -> (cfgValue) from workspace/shows/tools/show_config.json renderSettings
SERIES_CFG = {
    "series_a": 2.35,
    "series_b": 2.15,
    "series_c": 2.35,
}
SERIES_ORDER = ["series_a", "series_b", "series_c"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log_line(log_path: Path, msg: str) -> None:
    line = msg.rstrip()
    print(line, flush=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def run_one(series: str, py: str, log_path: Path, youtube_root: str, qc_no_asr: bool, batch_size: int, episode: str, episode_num: int) -> int:
    workspace = REPO / "workspace" / "shows" / series / episode
    cfg = SERIES_CFG[series]
    cmd = [
        py, "-u", str(REPO / "scripts" / "monitor_episode_production.py"),
        "--show", series,
        "--episode", episode,
        "--workspace", str(workspace.resolve()),
        "--episode-num", str(episode_num),
        "--youtube-root", youtube_root,
        "--cfg", str(cfg),
        "--batch-size", str(batch_size),
        "--retry-on-failure", "2",
        "--log", str(log_path.with_suffix(f".{series}.log")),
    ]
    if qc_no_asr:
        cmd.append("--qc-no-asr")
    log_line(log_path, f"[{utc_now()}] === {series} full production start (cfg={cfg}, batch={batch_size}) ===")
    log_line(log_path, "  $ " + " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO), env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"})
    log_line(log_path, f"[{utc_now()}] === {series} finished exit={proc.returncode} ===")
    return int(proc.returncode)


def acquire_lock(log_path: Path) -> int | None:
    """Global GPU production lock — one VoxCPM/ffmpeg compose job at a time."""
    _ = log_path
    return acquire_gpu_lock("run_all_series_full")


def release_lock(log_path: Path) -> None:
    _ = log_path
    release_gpu_lock()


def main() -> int:
    parser = argparse.ArgumentParser(description="Full production for all three series episode_001, serial.")
    parser.add_argument("--series", nargs="*", default=SERIES_ORDER)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument(
        "--qc-no-asr",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Pack QC layer-1 only (default True; render's compose_and_qc already ran full ASR).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_RENDER_BATCH_SIZE,
        help=f"Turns per VoxCPM subprocess (default {DEFAULT_RENDER_BATCH_SIZE}; load once per batch).",
    )
    parser.add_argument("--episode", default="episode_001", help="Episode dir id (e.g. episode_001, episode_002).")
    parser.add_argument("--episode-num", type=int, default=1, help="Episode number for packaging/youtube.")
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()

    validate_render_batch_size(args.batch_size)

    py = str(DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else sys.executable)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = REPO / "logs" / f"all_series_full_{ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if args.detach:
        # Guard: refuse to detach-spawn if a live instance already holds the lock.
        if acquire_lock(log_path) is None:
            return 2
        release_lock(log_path)  # child will re-acquire
        cmd = [py, "-u", str(Path(__file__).resolve()), *[a for a in sys.argv[1:] if a != "--detach"]]
        log_handle = log_path.open("a", encoding="utf-8", newline="\n")
        log_handle.write(f"[{utc_now()}] detach start {' '.join(cmd)}\n")
        log_handle.flush()
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO),
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env={**os.environ, "KMP_DUPLICATE_LIB_OK": "TRUE"},
        )
        print(f"log={log_path.as_posix()}", flush=True)
        print(f"pid={proc.pid}", flush=True)
        return 0

    # Child (non-detach): acquire lock for the duration of the run.
    if acquire_lock(log_path) is None:
        return 2
    log_line(log_path, f"[{utc_now()}] all-series full production started; series={args.series}; python={py}")
    overall = 0
    try:
        for series in args.series:
            code = run_one(series, py, log_path, args.youtube_root, args.qc_no_asr, args.batch_size, args.episode, args.episode_num)
            if code != 0:
                overall = code
                log_line(log_path, f"[{utc_now()}] STOPPING — {series} failed (exit {code})")
                break
        log_line(log_path, f"[{utc_now()}] all-series full production finished (exit {overall})")
    finally:
        release_lock(log_path)
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
