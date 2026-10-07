"""Daily persistent Chromium session for web ChatGPT image generation.

Start it once per working day, close it with Ctrl+C when done:

- Playwright's bundled Chromium with a persistent profile under
  ``workspace/runtime/imagegen/chromium-profile/`` (login survives across
  days, no re-login needed).
- Local CDP debug port (default 9334, override with ``EN_CHANNEL_CDP_PORT``
  so a vibecut session on 9333 can coexist).
- A blank tab. Navigation to ChatGPT is done by the attaching client
  (``generate_image.py``), never as a startup URL: verified on this
  machine that a startup navigation with no CDP client attached wedges
  the DevTools endpoint permanently, while client-driven ``page.goto``
  works and the session stays attachable.

``generate_image.py`` then attaches over CDP and never opens its own
window or runs login detection. This module launches the browser only —
all text input happens in ``chatgpt.py`` under its anti-fingerprint rules.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request

from .chatgpt import CDP_PORT, PROFILE_DIR

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
    print(f"Starting browser session... (CDP: http://127.0.0.1:{CDP_PORT})")
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

    print("Session ready. Generate with: python apps/worker-py/scripts/generate_image.py --prompt \"...\" --out <path>")
    print("Press Ctrl+C to close at end of day (login persists for tomorrow).")
    try:
        while process.poll() is None:
            time.sleep(1)
        print("Browser exited.")
    except KeyboardInterrupt:
        print("\nClosing the browser session...")
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
