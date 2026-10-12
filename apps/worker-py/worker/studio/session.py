"""Persistent Studio browser session for browser-only YouTube uploads.

Mirrors :mod:`worker.imagegen.session`: launch Playwright's bundled Chromium
as a subprocess with a repository-local persistent profile and a dedicated
CDP port (default 9335, ``ELR_STUDIO_CDP_PORT`` to override; the imagegen
session uses 9334 and vibecut 9333). The session starts on a blank page on
purpose — a startup URL navigation with no CDP client attached wedges the
DevTools endpoint on this machine — so the attaching client performs all
navigation to Studio after ``connect_over_cdp``.

The one-time YouTube login persists under
``workspace/runtime/studio-browser/chromium-profile/`` (gitignored).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_DIR = REPO_ROOT / "workspace" / "runtime" / "studio-browser"
PROFILE_DIR = RUNTIME_DIR / "chromium-profile"

CDP_PORT = int(os.environ.get("ELR_STUDIO_CDP_PORT", "9335"))
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"
STUDIO_HOME_URL = f"https://studio.youtube.com/channel/{CHANNEL_ID}"
STUDIO_UPLOAD_URL = f"{STUDIO_HOME_URL}/videos/upload"

STARTUP_PAGE = "about:blank"
STARTUP_WAIT_SEC = 20


def port_alive(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def cdp_ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    if port_alive(CDP_PORT):
        print(f"Session already running (CDP port {CDP_PORT}), nothing to do")
        return 0

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        executable = p.chromium.executable_path

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        executable,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={PROFILE_DIR.resolve()}",
        "--no-first-run",
        "--no-default-browser-check",
        "--lang=zh-CN",
        "--window-size=1440,900",
        STARTUP_PAGE,
    ]
    print(f"Starting Studio browser session... (CDP: http://127.0.0.1:{CDP_PORT})")
    process = subprocess.Popen(cmd)

    deadline = time.time() + STARTUP_WAIT_SEC
    while time.time() < deadline:
        if cdp_ready(CDP_PORT):
            break
        if process.poll() is not None:
            print(f"Error: browser exited early (code {process.returncode})", file=sys.stderr)
            return 1
        time.sleep(0.5)
    else:
        print(f"Error: CDP port {CDP_PORT} not ready within {STARTUP_WAIT_SEC}s", file=sys.stderr)
        process.terminate()
        return 1

    print("Session ready. Log into YouTube Studio once in the opened window; the login persists.")
    print("Upload with: python apps/worker-py/scripts/studio_upload.py --help")
    print("Press Ctrl+C to close at end of day (login persists for tomorrow).")
    try:
        while process.poll() is None:
            time.sleep(1)
        print("Browser exited.")
    except KeyboardInterrupt:
        print("\nClosing the Studio browser session...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
