from __future__ import annotations

import errno
import os
import sys


def _windows_process_state(pid: int) -> str:
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        # Access denied or sandbox invisibility is not proof of termination.
        return "dead" if ctypes.get_last_error() == 87 else "unknown"
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            return "unknown"
        return "alive" if code.value == 259 else "dead"
    finally:
        kernel.CloseHandle(handle)


def process_state(pid: int) -> str:
    if pid <= 0:
        return "dead"
    if sys.platform == "win32":
        try:
            return _windows_process_state(pid)
        except Exception:
            return "unknown"
    try:
        os.kill(pid, 0)
        return "alive"
    except OSError as exc:
        return "dead" if exc.errno == errno.ESRCH else "unknown"


def pid_alive(pid: int) -> bool:
    # Never reclaim an exclusive resource on an inconclusive process probe.
    return process_state(pid) != "dead"
