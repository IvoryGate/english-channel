from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKER = REPO / "apps" / "worker-py"
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))

from worker.channel.transport import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--repo-root", str(REPO), *sys.argv[1:]]))
