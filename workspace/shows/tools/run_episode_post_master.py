"""Deprecated: use pack_episode.py via scripts/run_episode_pack.py."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from pack_episode import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
