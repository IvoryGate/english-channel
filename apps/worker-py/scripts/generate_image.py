"""Generate an image via the web ChatGPT image tool (attaches to the daily session).

See docs/IMAGEGEN_BROWSER.md for the session workflow and rules.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from worker.imagegen.chatgpt import main as generate_main

    return generate_main()


if __name__ == "__main__":
    raise SystemExit(main())
