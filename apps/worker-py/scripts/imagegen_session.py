"""Start the daily persistent Chromium session for web ChatGPT image generation."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from worker.imagegen.session import main as session_main

    return session_main()


if __name__ == "__main__":
    raise SystemExit(main())
