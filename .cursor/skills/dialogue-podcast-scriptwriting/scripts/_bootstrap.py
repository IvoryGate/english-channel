"""Add worker package to sys.path when skill scripts run standalone."""

from __future__ import annotations

import sys
from pathlib import Path

WORKER_ROOT = Path(__file__).resolve().parents[4] / "apps" / "worker-py"
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))
