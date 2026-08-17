"""Full episode production monitor: render (per-turn retry) → pack → optional export.

Audiobook parity for unattended Series A/B/C delivery after scripts are approved.

  python scripts/monitor_episode_production.py \\
    --show series_b --episode episode_001 --workspace ... --force --detach
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
MONITOR_RENDER = REPO_ROOT / "scripts" / "monitor_episode_render.py"
PACK_SCRIPT = REPO_ROOT / "workspace" / "shows" / "tools" / "pack_episode.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from gpu_production_lock import DEFAULT_RENDER_BATCH_SIZE, GpuProductionLock, release_gpu_lock, validate_render_batch_size  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_production(args: argparse.Namespace, log_path: Path) -> int:
    manifest = Path(args.workspace).resolve() / f"000_{args.episode}.episode_manifest.json"
    py = str(Path(args.python))

    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        def write(msg: str) -> None:
            line = msg.rstrip()
            print(line, flush=True)
            log.write(line + "\n")
            log.flush()

        write(f"[{utc_now()}] production started show={args.show} episode={args.episode}")

        render_cmd = [
            py,
            "-u",
            str(MONITOR_RENDER),
            "--manifest",
            str(manifest),
            "--device",
            args.device,
            "--cfg",
            str(args.cfg),
            "--batch-size",
            str(args.batch_size),
            "--retry-on-failure",
            str(args.retry_on_failure),
            "--log-file",
            str(log_path.with_suffix(".render.log")),
        ]
        if args.force:
            render_cmd.append("--force")
        if args.qc_no_asr:
            render_cmd.append("--no-self-check")
        write(f"render: {' '.join(render_cmd)}")
        proc = subprocess.Popen(
            render_cmd,
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            write(line)
        render_code = int(proc.wait())
        if render_code != 0:
            write(f"[{utc_now()}] render failed exit={render_code}")
            return render_code

        pack_cmd = [
            py,
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
            str(log_path.with_suffix(".pack.log")),
        ]
        if args.qc_no_asr:
            pack_cmd.append("--qc-no-asr")
        if args.skip_export:
            pack_cmd.append("--skip-export")
        pack_cmd.extend(["--compose-encoder", "libx264"])
        write(f"pack: {' '.join(pack_cmd)}")
        proc = subprocess.Popen(
            pack_cmd,
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            write(line)
        code = int(proc.wait())
        write(f"[{utc_now()}] production finished exit={code}")
        return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor full episode production (render→pack→optional export).")
    parser.add_argument("--show", required=True)
    parser.add_argument("--episode", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cfg", type=float, default=2.15)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_RENDER_BATCH_SIZE)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--retry-on-failure", type=int, default=2)
    parser.add_argument("--qc-no-asr", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--log", default="")
    parser.add_argument("--python", default=str(DEFAULT_PYTHON))
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()

    validate_render_batch_size(args.batch_size)

    log_path = Path(args.log) if args.log else REPO_ROOT / "logs" / f"monitor_episode_{args.show}_{args.episode}.log"

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
        return 0

    label = f"monitor_{args.show}_{args.episode}"
    with GpuProductionLock(label):
        return run_production(args, log_path)


if __name__ == "__main__":
    raise SystemExit(main())
