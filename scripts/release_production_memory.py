"""Release GPU/RAM held by stale ELR production processes (Windows-first).

After a VoxCPM crash or a long A→B→C render marathon, orphaned python
subprocesses and a stale GPU lock can leave CUDA memory and virtual memory
pressured. This script:

1. Prints system memory (physical + virtual free/total)
2. Removes a stale ``logs/gpu_production.lock`` when the holder PID is dead
3. Terminates zombie project python processes (render/monitor/pack/resume)
4. Clears PyTorch CUDA cache in a short-lived subprocess

It cannot replace a reboot when Windows page file is exhausted — if free
virtual memory stays below ~2 GB after cleanup, the script warns and exits 1.

Usage:
  python scripts/release_production_memory.py
  python scripts/release_production_memory.py --dry-run
  python scripts/release_production_memory.py --no-kill
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_PYTHON = REPO / ".conda-env" / "python.exe"
LOCK_PATH = REPO / "logs" / "gpu_production.lock"

# Substrings that identify ELR production workers (not arbitrary python).
PRODUCTION_MARKERS = (
    "render_episode.py",
    "monitor_episode",
    "pack_episode.py",
    "run_episode_pack.py",
    "resume_episode_production.py",
    "compose_episode_video.py",
    "smoke_voxcpm2.py",
)

MIN_FREE_VIRTUAL_GB = 2.0


@dataclass
class MemorySnapshot:
    total_physical_gb: float
    free_physical_gb: float
    total_virtual_gb: float
    free_virtual_gb: float

    def as_lines(self) -> list[str]:
        return [
            f"  physical: {self.free_physical_gb:.1f} / {self.total_physical_gb:.1f} GB free",
            f"  virtual:  {self.free_virtual_gb:.1f} / {self.total_virtual_gb:.1f} GB free",
        ]


def _memory_snapshot() -> MemorySnapshot | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return None
        gb = 1024**3
        return MemorySnapshot(
            total_physical_gb=stat.ullTotalPhys / gb,
            free_physical_gb=stat.ullAvailPhys / gb,
            total_virtual_gb=stat.ullTotalPageFile / gb,
            free_virtual_gb=stat.ullAvailPageFile / gb,
        )
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    sys.path.insert(0, str(REPO / "scripts"))
    from gpu_production_lock import pid_alive  # noqa: E402

    return pid_alive(pid)


def _list_python_processes() -> list[tuple[int, str]]:
    if sys.platform != "win32":
        return []
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO),
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        raw = json.loads(result.stdout)
        rows = raw if isinstance(raw, list) else [raw]
        out: list[tuple[int, str]] = []
        for row in rows:
            pid = int(row.get("ProcessId") or 0)
            cmd = str(row.get("CommandLine") or "")
            if pid > 0:
                out.append((pid, cmd))
        return out
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return []


def _is_production_process(cmd: str) -> bool:
    lowered = cmd.lower()
    if "english-channel" not in lowered and str(REPO).lower() not in lowered:
        return False
    return any(marker.lower() in lowered for marker in PRODUCTION_MARKERS)


def _clear_stale_gpu_lock(*, dry_run: bool) -> str | None:
    if not LOCK_PATH.is_file():
        return None
    try:
        lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        lock = {"pid": -1}
    holder = int(lock.get("pid") or -1)
    if holder > 0 and _pid_alive(holder):
        return f"gpu lock held by live pid={holder} label={lock.get('label', '?')}"
    if dry_run:
        return f"would remove stale gpu lock (pid={holder} dead)"
    LOCK_PATH.unlink(missing_ok=True)
    return f"removed stale gpu lock (pid={holder} was dead)"


def _kill_process(pid: int, *, dry_run: bool) -> bool:
    if dry_run:
        return True
    if sys.platform == "win32":
        import ctypes

        PROCESS_TERMINATE = 0x0001
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if not h:
            return False
        try:
            return bool(ctypes.windll.kernel32.TerminateProcess(h, 1))
        finally:
            ctypes.windll.kernel32.CloseHandle(h)
    try:
        os.kill(pid, 9)
        return True
    except OSError:
        return False


def _clear_cuda_cache() -> str:
    py = str(DEFAULT_PYTHON if DEFAULT_PYTHON.is_file() else sys.executable)
    snippet = (
        "import gc; gc.collect()\n"
        "try:\n"
        " import torch\n"
        " if torch.cuda.is_available():\n"
        "  torch.cuda.empty_cache()\n"
        "  torch.cuda.synchronize()\n"
        "  print('cuda cache cleared')\n"
        " else:\n"
        "  print('cuda not available')\n"
        "except Exception as e:\n"
        " print(f'cuda clear skipped: {e}')\n"
    )
    proc = subprocess.run([py, "-c", snippet], capture_output=True, text=True, cwd=str(REPO))
    line = (proc.stdout or proc.stderr or "").strip().splitlines()
    return line[-1] if line else f"cuda clear exit={proc.returncode}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Release GPU/RAM from stale ELR production processes.")
    parser.add_argument("--dry-run", action="store_true", help="Report actions without killing or deleting lock.")
    parser.add_argument("--no-kill", action="store_true", help="Skip terminating zombie processes.")
    args = parser.parse_args()

    me = os.getpid()
    print("release_production_memory")
    before = _memory_snapshot()
    if before:
        print("memory before:")
        print("\n".join(before.as_lines()))
    else:
        print("memory before: (unavailable on this platform)")

    lock_msg = _clear_stale_gpu_lock(dry_run=args.dry_run)
    if lock_msg:
        print(lock_msg)

    killed: list[str] = []
    skipped: list[str] = []
    if not args.no_kill:
        for pid, cmd in _list_python_processes():
            if pid in {me, os.getppid()}:
                continue
            if not _is_production_process(cmd):
                continue
            short = cmd if len(cmd) <= 120 else cmd[:117] + "..."
            if args.dry_run:
                killed.append(f"  would kill pid={pid} {short}")
                continue
            if _kill_process(pid, dry_run=False):
                killed.append(f"  killed pid={pid}")
            else:
                skipped.append(f"  failed pid={pid}")

    if killed:
        print("production processes:")
        print("\n".join(killed))
    elif not args.no_kill:
        print("production processes: none found")

    if skipped:
        print("could not terminate:")
        print("\n".join(skipped))

    if not args.dry_run:
        gc.collect()
        print(_clear_cuda_cache())

    after = _memory_snapshot()
    if after:
        print("memory after:")
        print("\n".join(after.as_lines()))
        if after.free_virtual_gb < MIN_FREE_VIRTUAL_GB:
            print(
                f"\nWARNING: free virtual memory {after.free_virtual_gb:.1f} GB "
                f"< {MIN_FREE_VIRTUAL_GB:.0f} GB — close apps or reboot before resuming render."
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
