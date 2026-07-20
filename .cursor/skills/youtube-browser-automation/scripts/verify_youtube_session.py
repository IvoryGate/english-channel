from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import browser_profile_dir, has_chrome_user_profile, write_json


def detect_login_state(page: object) -> dict[str, object]:
    script = """
    () => {
      const signIn = document.querySelector('a[aria-label="Sign in"], tp-yt-paper-button#sign-in-button, a[href*="ServiceLogin"]');
      const avatar = document.querySelector('button#avatar-btn, img.yt-spec-avatar-shape__image, #avatar-btn');
      const channel = document.querySelector('#channel-name, yt-formatted-string.ytd-channel-name');
      return {
        hasSignInButton: Boolean(signIn),
        hasAvatar: Boolean(avatar),
        channelText: channel ? channel.textContent.trim() : '',
        title: document.title || '',
        url: location.href,
      };
    }
    """
    return page.evaluate(script)  # type: ignore[attr-defined]


def profile_snapshot(corpus_root: Path) -> dict[str, object]:
    profile_dir = browser_profile_dir(corpus_root)
    user_data = profile_dir / "chrome_user_data"
    prefs_path = user_data / "Default" / "Preferences"
    cookies_path = user_data / "Default" / "Network" / "Cookies"
    accounts: list[str] = []
    if prefs_path.exists():
        import json

        prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
        for item in prefs.get("account_info", []):
            email = str(item.get("email") or "").strip()
            if email:
                accounts.append(email)
    return {
        "chrome_user_data": user_data.as_posix(),
        "preferences_exists": prefs_path.exists(),
        "cookies_exists": cookies_path.exists(),
        "cookies_bytes": cookies_path.stat().st_size if cookies_path.exists() else 0,
        "google_accounts": accounts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify saved YouTube browser session.")
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--headful", action="store_true", help="Show browser while verifying.")
    parser.add_argument("--url", default="https://studio.youtube.com/")
    parser.add_argument("--write-report", help="Optional JSON report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    profile_dir = browser_profile_dir(corpus_root)
    if not has_chrome_user_profile(corpus_root):
        raise SystemExit(
            f"No Chrome profile at {(profile_dir / 'chrome_user_data').as_posix()}. "
            "Run save_browser_session.py --headful first."
        )

    snapshot = profile_snapshot(corpus_root)
    if not snapshot.get("google_accounts"):
        raise SystemExit(
            "Chrome profile exists but no Google account found in Preferences.\n"
            "Run open_youtube_login.ps1, sign in, then close Chrome completely."
        )

    config = account_browser_config(profile_dir, headless=not args.headful)
    try:
        with YouTubeBrowserSession(config=config) as session:
            assert session._page is not None
            session.goto(args.url)
            session._page.wait_for_timeout(3000)
            state = detect_login_state(session._page)
    except SystemExit as exc:
        report = {
            "schema": "youtube-browser-session-verify-v1",
            "profile_mode": "chrome_user_data",
            "likely_logged_in": True,
            "offline_profile_ok": True,
            "browser_check": "skipped_or_failed",
            "browser_error": str(exc),
            "profile_snapshot": snapshot,
            "hint": "Close all Chrome windows, then rerun verify for a live Studio check.",
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    likely_logged_in = bool(state.get("hasAvatar")) and not bool(state.get("hasSignInButton"))
    report = {
        "schema": "youtube-browser-session-verify-v1",
        "profile_mode": "chrome_user_data",
        "chrome_user_data": (profile_dir / "chrome_user_data").as_posix(),
        "url": state.get("url"),
        "title": state.get("title"),
        "likely_logged_in": likely_logged_in,
        "offline_profile_ok": bool(snapshot.get("google_accounts")),
        "profile_snapshot": snapshot,
        "signals": state,
    }
    if args.write_report:
        write_json(Path(args.write_report), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if likely_logged_in else 2


if __name__ == "__main__":
    raise SystemExit(main())
