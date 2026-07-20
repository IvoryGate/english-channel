from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import browser_profile_dir

DEFAULT_LOGIN_URL = "https://studio.youtube.com/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open installed Chrome with a persistent profile for YouTube login.")
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--headful", action="store_true", help="Required for manual login.")
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=600,
        help="Auto-close after N seconds when --no-wait-for-enter is set.",
    )
    parser.add_argument(
        "--no-wait-for-enter",
        action="store_true",
        help="Do not wait for Enter; close after --wait-seconds instead.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_LOGIN_URL,
        help="Page to open. Default: YouTube Studio (sign in from the normal Chrome UI).",
    )
    parser.add_argument(
        "--channel",
        default="chrome",
        choices=["chrome", "msedge"],
        help="Installed browser channel. Use chrome (Google Chrome) for Google login.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.headful:
        raise SystemExit("Manual login requires --headful.")

    profile_dir = browser_profile_dir(Path(args.workspace_root))
    config = account_browser_config(profile_dir, headless=False)
    config.browser_channel = args.channel
    user_data_dir = profile_dir / "chrome_user_data"

    print(f"profile_dir={profile_dir.as_posix()}")
    print(f"chrome_user_data={user_data_dir.as_posix()}")
    print("Opening installed Chrome (not Playwright Chromium) for Google / YouTube login...")
    print("Steps:")
    print("  1. Sign in with your YouTube channel Google account in the Chrome window.")
    print("  2. Confirm YouTube Studio loads and shows your channel.")
    print("  3. Return here and press Enter to finish and save the profile.")
    print("Do not share your password in chat. Login happens only in the browser.")
    print("If Google still blocks login, close this and sign in once manually in your normal Chrome,")
    print("then tell the agent to switch to CDP attach mode.")

    with YouTubeBrowserSession(config=config) as session:
        session.goto(args.url)
        if args.no_wait_for_enter:
            print(f"Waiting {args.wait_seconds}s before closing...")
            time.sleep(max(args.wait_seconds, 1))
        else:
            try:
                input("\nPress Enter after login is complete... ")
            except EOFError:
                print("No interactive terminal; falling back to timed wait.", file=sys.stderr)
                time.sleep(max(args.wait_seconds, 1))

    print(f"saved_profile={user_data_dir.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
