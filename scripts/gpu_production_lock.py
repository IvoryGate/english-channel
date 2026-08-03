"""Global GPU production lock — one heavy GPU job at a time.

Covers VoxCPM turn render, Whisper ASR QC, and ffmpeg video compose (NVENC).
All production entry points must acquire this lock before touching GPU/RAM-heavy
work so a retry/relaunch cannot stack two VoxCPM loads or VoxCPM + NVENC.

Lock file: logs/gpu_production.lock  (JSON: pid, label, started_at)
Re-entrant: same PID may acquire again (monitor render → pack in one process).
"""

from __future__ import annotations

import atexit
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO / "logs" / "gpu_production.lock"

_holding = False
_holding_from_parent = False


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            try:
                exit_code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(h, ctypes.byref(exit_code)):
                    return False
                return exit_code.value == STILL_ACTIVE
            finally:
                kernel32.CloseHandle(h)
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_lock() -> dict[str, Any] | None:
    if not LOCK_PATH.is_file():
        return None
    try:
        return json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"pid": -1, "label": "corrupt-lock", "started_at": ""}


def acquire_gpu_lock(label: str) -> int | None:
    """Acquire the global GPU lock. Returns pid on success, None if another live process holds it."""
    global _holding, _holding_from_parent
    me = os.getpid()
    existing = _read_lock()
    if existing:
        old_pid = int(existing.get("pid") or -1)
        if old_pid == me:
            return me
        parent = os.getppid()
        if old_pid == parent and pid_alive(old_pid):
            _holding = True
            _holding_from_parent = True
            return me
        if pid_alive(old_pid):
            print(
                f"REFUSE GPU lock: pid={old_pid} label={existing.get('label', '?')} "
                f"started={existing.get('started_at', '?')}. "
                f"Only one VoxCPM/ffmpeg production job at a time. "
                f"Delete {LOCK_PATH.as_posix()} only if that process crashed.",
                flush=True,
            )
            return None

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pid": me, "label": label, "started_at": _utc_now()}
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _holding = True
    _holding_from_parent = False
    return me


def release_gpu_lock() -> None:
    global _holding, _holding_from_parent
    if _holding_from_parent:
        _holding = False
        _holding_from_parent = False
        return
    if not _holding:
        return
    try:
        if LOCK_PATH.is_file():
            data = _read_lock()
            if data and int(data.get("pid") or -1) == os.getpid():
                LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass
    _holding = False


DEFAULT_RENDER_BATCH_SIZE = 20
MAX_RENDER_BATCH_SIZE = 20


def validate_render_batch_size(batch_size: int) -> int:
    """Turns per VoxCPM subprocess — load once, render N turns, unload.

    Default 20 balances model-load overhead against the tested 8GB VRAM ceiling. Do not run
    an entire episode in one process (134+ turns); that still CUDA-crashes.
    """
    if batch_size < 1:
        print(f"ERROR: --batch-size must be >= 1 (got {batch_size}).", file=sys.stderr)
        raise SystemExit(2)
    if batch_size > MAX_RENDER_BATCH_SIZE:
        print(
            f"ERROR: --batch-size {batch_size} exceeds max {MAX_RENDER_BATCH_SIZE}. "
            f"See docs/shows/EPISODE_PIPELINE.md § GPU memory policy.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return batch_size


def enforce_batch_size_one(batch_size: int) -> int:
    """Deprecated alias — use validate_render_batch_size."""
    return validate_render_batch_size(batch_size)


class GpuProductionLock:
    """Context manager wrapper for acquire/release."""

    def __init__(self, label: str) -> None:
        self.label = label
        self.acquired = False

    def __enter__(self) -> "GpuProductionLock":
        if acquire_gpu_lock(self.label) is None:
            raise SystemExit(2)
        self.acquired = True
        return self

    def __exit__(self, *_exc: object) -> None:
        if self.acquired:
            release_gpu_lock()


atexit.register(release_gpu_lock)
