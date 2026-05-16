from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    worker_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(worker_root))
    os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    import pytest

    args = sys.argv[1:] or [str(worker_root / "tests")]
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
