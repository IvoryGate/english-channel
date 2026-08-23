"""Skill entry point for continuous sequential chapter rendering.

Delegates to the repo monitor at scripts/monitor_book_chapters.py so the
implementation stays in one place while agents can invoke it from the skill
scripts directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MONITOR_SCRIPT = REPO_ROOT / "scripts" / "monitor_book_chapters.py"


def main() -> int:
    if not MONITOR_SCRIPT.is_file():
        print(f"error: monitor script not found: {MONITOR_SCRIPT}", file=sys.stderr)
        return 2

    cmd = [sys.executable, str(MONITOR_SCRIPT), *sys.argv[1:]]
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
