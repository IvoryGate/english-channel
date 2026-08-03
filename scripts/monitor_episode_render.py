"""Monitor ELR episode VoxCPM render — audiobook monitor_book_chapters parity.

Renders one turn (or small batch) per subprocess so CUDA crashes are recoverable.
After all turns exist, runs compose + QC once, then optional pack.

Usage:
  python scripts/monitor_episode_render.py --manifest ... --log-file logs/...
  python scripts/monitor_episode_production.py --show series_b --episode episode_001 --workspace ... --detach
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO_ROOT / ".conda-env" / "python.exe"
RENDER_EPISODE = REPO_ROOT / "workspace" / "shows" / "tools" / "render_episode.py"
TOOLS_DIR = REPO_ROOT / "workspace" / "shows" / "tools"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from gpu_production_lock import DEFAULT_RENDER_BATCH_SIZE, validate_render_batch_size  # noqa: E402
sys.path.insert(0, str(TOOLS_DIR))
from episode_artifacts import turn_wav_path  # noqa: E402

_stop_requested = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def _format_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


class MonitorLogger:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.log_path.open("a", encoding="utf-8", newline="\n")

    def close(self) -> None:
        self._file.close()

    def write(self, message: str) -> None:
        line = message.rstrip()
        print(line, flush=True)
        self._file.write(line + "\n")
        self._file.flush()

    def log(self, message: str) -> None:
        self.write(f"[{_format_ts(_utc_now())}] {message}")


def _handle_stop(signum: int, _frame: object | None) -> None:
    global _stop_requested
    _stop_requested = True


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_cfg(manifest_path: Path, cfg: float, logger: MonitorLogger) -> None:
    data = load_manifest(manifest_path)
    settings = dict(data.get("renderSettings") or {})
    settings["cfgValue"] = cfg
    data["renderSettings"] = settings
    manifest_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    logger.log(f"manifest cfgValue={cfg}")


def turn_wav(workspace: Path, turn: dict[str, Any]) -> Path:
    # Episode turn WAVs live under audio/turns/ (see episode_artifacts.turn_wav_path).
    return turn_wav_path(workspace, str(turn["filename"]))


def pending_turns(manifest: dict[str, Any], workspace: Path, *, force: bool) -> list[dict[str, Any]]:
    if force:
        return list(manifest["turns"])
    pending: list[dict[str, Any]] = []
    for turn in manifest["turns"]:
        if not turn_wav(workspace, turn).is_file():
            pending.append(turn)
    return pending


def chunk_turns(turns: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    size = max(1, batch_size)
    return [turns[i : i + size] for i in range(0, len(turns), size)]


def build_render_cmd(
    *,
    python: Path,
    manifest_path: Path,
    turn_ids: list[str],
    device: str,
    compose: bool,
    self_check: bool,
    skip_existing: bool = False,
) -> list[str]:
    cmd = [
        str(python),
        "-u",
        str(RENDER_EPISODE),
        "--manifest",
        str(manifest_path.resolve()),
        "--device",
        device,
    ]
    if turn_ids:
        cmd.extend(["--segments", ",".join(turn_ids)])
    if skip_existing:
        cmd.append("--skip-existing")
    if not compose:
        cmd.append("--no-compose")
    if not self_check:
        cmd.append("--no-self-check")
    return cmd


def run_subprocess(cmd: list[str], logger: MonitorLogger) -> int:
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    env.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    logger.write(f"  command: {' '.join(cmd)}")
    started = time.monotonic()
    process = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert process.stdout is not None
    for line in process.stdout:
        logger.write(f"    {line.rstrip()}")
    code = int(process.wait())
    logger.log(f"subprocess finished in {_format_duration(time.monotonic() - started)} (exit {code})")
    return code


def render_turn_batch(
    *,
    turn_ids: list[str],
    manifest_path: Path,
    python: Path,
    device: str,
    logger: MonitorLogger,
    retry_on_failure: int,
) -> int:
    attempts = 1 + max(retry_on_failure, 0)
    label = ",".join(turn_ids)
    for attempt in range(1, attempts + 1):
        if _stop_requested:
            logger.log(f"turns {label} cancelled (stop requested)")
            return 130
        attempt_label = f"attempt {attempt}/{attempts}" if attempts > 1 else "attempt 1/1"
        logger.log(f"render turns {label} ({attempt_label})")
        cmd = build_render_cmd(
            python=python,
            manifest_path=manifest_path,
            turn_ids=turn_ids,
            device=device,
            compose=False,
            self_check=False,
        )
        code = run_subprocess(cmd, logger)
        if code == 0:
            return 0
        if attempt < attempts:
            logger.log(f"turns {label} failed (exit {code}); retrying after 15s cooldown")
            time.sleep(15)
            continue
        logger.log(f"turns {label} failed after {attempts} attempt(s)")
        return code
    return 1


def compose_and_qc(
    *,
    manifest_path: Path,
    python: Path,
    device: str,
    logger: MonitorLogger,
    retry_on_failure: int,
    self_check: bool,
) -> int:
    attempts = 1 + max(retry_on_failure, 0)
    for attempt in range(1, attempts + 1):
        if _stop_requested:
            return 130
        logger.log(f"compose+qc (attempt {attempt}/{attempts})")
        cmd = build_render_cmd(
            python=python,
            manifest_path=manifest_path,
            turn_ids=[],
            device=device,
            compose=True,
            self_check=self_check,
            skip_existing=True,
        )
        # No segments + all wavs exist => skip model load, compose + QC only.
        code = run_subprocess(cmd, logger)
        if code == 0:
            return 0
        if attempt < attempts:
            time.sleep(10)
            continue
        return code
    return 1


def monitor_render(
    *,
    manifest_path: Path,
    python: Path,
    device: str,
    logger: MonitorLogger,
    batch_size: int,
    force: bool,
    retry_on_failure: int,
    cfg: float,
    no_self_check: bool,
) -> int:
    workspace = manifest_path.parent
    patch_cfg(manifest_path, cfg, logger)
    manifest = load_manifest(manifest_path)

    pending = pending_turns(manifest, workspace, force=force)
    total = len(manifest["turns"])
    logger.log(
        f"monitor render started turns={total} pending={len(pending)} "
        f"batch_size={batch_size} force={force}"
    )

    completed_batches = 0
    for batch in chunk_turns(pending, batch_size):
        if _stop_requested:
            return 130
        ids = [str(t["id"]) for t in batch]
        code = render_turn_batch(
            turn_ids=ids,
            manifest_path=manifest_path,
            python=python,
            device=device,
            logger=logger,
            retry_on_failure=retry_on_failure,
        )
        if code != 0:
            return code
        completed_batches += 1
        done = min(total, completed_batches * batch_size)
        logger.log(f"progress {done}/{total} turns rendered this run")

    still = pending_turns(load_manifest(manifest_path), workspace, force=False)
    if still:
        logger.log(f"error: {len(still)} turns still missing after render loop")
        return 1

    return compose_and_qc(
        manifest_path=manifest_path,
        python=python,
        device=device,
        logger=logger,
        retry_on_failure=retry_on_failure,
        self_check=not no_self_check,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor ELR episode turn render with retry/resume.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cfg", type=float, default=2.15)
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_RENDER_BATCH_SIZE,
        help=f"Turns per subprocess (default {DEFAULT_RENDER_BATCH_SIZE}; one model load per batch).",
    )
    parser.add_argument("--force", action="store_true", help="Re-render all turns even if WAV exists.")
    parser.add_argument("--retry-on-failure", type=int, default=2, help="Retries per batch (default 2).")
    parser.add_argument(
        "--no-self-check",
        action="store_true",
        help="Skip Whisper ASR in render compose+QC (pack runs layer-1 QC only with --qc-no-asr).",
    )
    parser.add_argument("--python", type=Path, default=DEFAULT_PYTHON)
    parser.add_argument("--log-file", type=Path, default=REPO_ROOT / "logs" / "monitor_episode_render.log")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_render_batch_size(args.batch_size)
    if not args.python.is_file():
        print(f"error: python not found: {args.python}", file=sys.stderr)
        return 2
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    logger = MonitorLogger(args.log_file)
    started = time.monotonic()
    code = 1
    try:
        code = monitor_render(
            manifest_path=manifest_path,
            python=args.python,
            device=args.device,
            logger=logger,
            batch_size=args.batch_size,
            force=args.force,
            retry_on_failure=args.retry_on_failure,
            cfg=args.cfg,
            no_self_check=args.no_self_check,
        )
    finally:
        logger.log(
            f"monitor render stopped (runtime {_format_duration(time.monotonic() - started)}, exit {code})"
        )
        logger.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
