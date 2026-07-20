"""Skill entry point for episode pack — delegates to scripts/launch_episode_pack.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LAUNCH_SCRIPT = REPO_ROOT / "scripts" / "launch_episode_pack.py"


def main() -> int:
    if not LAUNCH_SCRIPT.is_file():
        print(f"error: launch script not found: {LAUNCH_SCRIPT}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(LAUNCH_SCRIPT), *sys.argv[1:]]
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
