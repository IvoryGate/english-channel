"""Channel GPU resource lease — one heavy GPU job at a time.

Covers VoxCPM turn render, Whisper ASR QC, and ffmpeg video compose (NVENC).
All production entry points must acquire this lock before touching GPU/RAM-heavy
work so a retry/relaunch cannot stack two VoxCPM loads or VoxCPM + NVENC.

SQLite truth: workspace/channel/channel.sqlite.
Compatibility mirror: logs/gpu_production.lock.
Re-entrant: same PID may acquire again (monitor render → pack in one process).
"""

from __future__ import annotations

import atexit
import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO / "logs" / "gpu_production.lock"
WORKER = REPO / "apps" / "worker-py"
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))

from worker.channel.repo import SqliteChannelRepository  # noqa: E402
from worker.channel.schema import load_channel_policy, load_resource_policies  # noqa: E402
from worker.channel.service import (  # noqa: E402
    ChannelIdentityService,
    ResourceBusyError,
    ResourceLeaseService,
)
from worker.channel.providers.process import pid_alive as _pid_alive  # noqa: E402
from worker.channel.types import ResourceLease  # noqa: E402

_holding = False
_holding_from_parent = False
_hold_depth = 0
_lease: ResourceLease | None = None
_lease_service: ResourceLeaseService | None = None
_heartbeat_stop: threading.Event | None = None
_heartbeat_thread: threading.Thread | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def pid_alive(pid: int) -> bool:
    return _pid_alive(pid)


def _services() -> tuple[ResourceLeaseService, int]:
    repository = SqliteChannelRepository(REPO / "workspace" / "channel" / "channel.sqlite")
    identity = ChannelIdentityService(
        load_channel_policy(REPO / "configs" / "channel" / "control-plane.json"), repository
    )
    identity.initialize()
    policies = load_resource_policies(REPO / "configs" / "channel" / "resources.json")
    policy = next(item for item in policies if item.resource_id == "gpu_heavy")
    return ResourceLeaseService(repository, policies), policy.heartbeat_interval_sec


def _start_heartbeat(service: ResourceLeaseService, lease: ResourceLease, interval: int) -> None:
    global _heartbeat_stop, _heartbeat_thread, _lease
    stop = threading.Event()

    def run() -> None:
        global _lease
        while not stop.wait(interval):
            try:
                _lease = service.heartbeat(lease)
            except Exception as exc:
                print(f"RESOURCE LEASE HEARTBEAT FAILED: {exc}", file=sys.stderr, flush=True)
                return

    _heartbeat_stop = stop
    _heartbeat_thread = threading.Thread(target=run, name="gpu-lease-heartbeat", daemon=True)
    _heartbeat_thread.start()


def _read_lock() -> dict[str, Any] | None:
    if not LOCK_PATH.is_file():
        return None
    try:
        return json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"pid": -1, "label": "corrupt-lock", "started_at": ""}


def acquire_gpu_lock(label: str) -> int | None:
    """Acquire the global GPU lock. Returns pid on success, None if another live process holds it."""
    global _holding, _holding_from_parent, _hold_depth, _lease, _lease_service
    me = os.getpid()
    service, heartbeat_interval = _services()
    active = service.repository.active_lease("gpu_heavy")
    if active and active.owner_pid == me:
        _holding = True
        _hold_depth += 1
        return me
    if active and active.owner_pid == os.getppid() and pid_alive(active.owner_pid):
        _holding = True
        _holding_from_parent = True
        _hold_depth += 1
        return me
    existing = _read_lock()
    if existing:
        old_pid = int(existing.get("pid") or -1)
        if old_pid == me:
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

    owner_id = f"pid:{me}"
    try:
        lease = service.acquire(
            "gpu_heavy", owner_id=owner_id, owner_pid=me,
            parent_pid=os.getppid(), label=label,
        )
    except ResourceBusyError as exc:
        held = exc.lease
        print(
            f"REFUSE GPU lease: pid={held.owner_pid} label={held.label} "
            f"heartbeat={held.heartbeat_at} expires={held.expires_at}.",
            flush=True,
        )
        return None
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "pid": me, "label": label, "started_at": _utc_now(),
        "lease_id": lease.lease_id, "resource": lease.resource_id,
    }
    LOCK_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    _holding = True
    _holding_from_parent = False
    _hold_depth = 1
    _lease = lease
    _lease_service = service
    _start_heartbeat(service, lease, heartbeat_interval)
    return me


def release_gpu_lock() -> None:
    global _holding, _holding_from_parent, _hold_depth, _lease, _lease_service
    global _heartbeat_stop, _heartbeat_thread
    if _holding_from_parent:
        if _hold_depth > 1:
            _hold_depth -= 1
            return
        _holding = False
        _holding_from_parent = False
        _hold_depth = 0
        return
    if not _holding:
        return
    if _hold_depth > 1:
        _hold_depth -= 1
        return
    if _heartbeat_stop is not None:
        _heartbeat_stop.set()
    if _heartbeat_thread is not None and _heartbeat_thread is not threading.current_thread():
        _heartbeat_thread.join(timeout=2)
    if _lease is not None and _lease_service is not None:
        try:
            _lease_service.release(_lease)
        except Exception as exc:
            print(f"RESOURCE LEASE RELEASE FAILED: {exc}", file=sys.stderr, flush=True)
    try:
        if LOCK_PATH.is_file():
            data = _read_lock()
            if data and int(data.get("pid") or -1) == os.getpid():
                LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass
    _holding = False
    _hold_depth = 0
    _lease = None
    _lease_service = None
    _heartbeat_stop = None
    _heartbeat_thread = None


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
