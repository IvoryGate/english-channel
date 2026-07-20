from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import run_search_batch
from worker.youtube_podcast_research.workspace import (
    DEFAULT_SEARCH_QUERIES,
    browser_profile_dir,
    discovery_dir,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search YouTube via Playwright and archive result metadata.")
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--query", action="append", help="Search query. Repeatable.")
    parser.add_argument("--scroll-rounds", type=int, default=2)
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--screenshot", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    queries = (args.query or list(DEFAULT_SEARCH_QUERIES))[:1] if args.smoke else (args.query or list(DEFAULT_SEARCH_QUERIES))
    scroll_rounds = 0 if args.smoke else args.scroll_rounds
    profile_dir = browser_profile_dir(corpus_root)

    payload = run_search_batch(
        queries,
        profile_dir=profile_dir,
        headless=not args.headful,
        scroll_rounds=scroll_rounds,
        pause_seconds=0.0 if args.smoke else 1.0,
    )

    output = discovery_dir(corpus_root) / ("browser_search_smoke.json" if args.smoke else "browser_search_latest.json")
    write_json(output, payload)

    if args.screenshot:
        from worker.youtube_podcast_research.browser import BrowserConfig, YouTubeBrowserSession

        screenshot_path = discovery_dir(corpus_root) / "browser_search_latest.png"
        with YouTubeBrowserSession(BrowserConfig(headless=not args.headful, profile_dir=profile_dir)) as session:
            session.search(queries[0], scroll_rounds=0)
            session.screenshot(screenshot_path)
        print(f"screenshot={screenshot_path}")

    print(f"search={output}")
    print(f"videos={payload['result_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
