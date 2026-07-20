"""Skill entry — monitor episode production (render→pack→export)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT = REPO_ROOT / "scripts" / "monitor_episode_production.py"


def main() -> int:
    if not SCRIPT.is_file():
        print(f"error: not found: {SCRIPT}", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(SCRIPT), *sys.argv[1:]], cwd=str(REPO_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
