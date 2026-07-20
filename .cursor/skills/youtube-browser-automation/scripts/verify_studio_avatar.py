from __future__ import annotations

from pathlib import Path

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import analysis_dir, browser_profile_dir, ensure_dir

URL = "https://studio.youtube.com/channel/UC9QpAkVpv8l1ZQ3X4UtU37A/editing/profile"


def main() -> int:
    corpus = Path("workspace/dialogue_podcast_research/youtube_corpus")
    config = account_browser_config(browser_profile_dir(corpus), headless=False)
    out = ensure_dir(analysis_dir(corpus)) / "studio_avatar_check.png"
    with YouTubeBrowserSession(config) as session:
        page = session._page
        session.goto(URL)
        page.wait_for_timeout(2000)
        skip = page.locator('a:has-text("跳至 YOUTUBE 工作室"), a:has-text("Skip to YouTube Studio")').first
        if skip.count():
            skip.click()
            page.wait_for_timeout(5000)
        page.get_by_text("照片", exact=False).first.scroll_into_view_if_needed()
        page.wait_for_timeout(2000)
        session.screenshot(out)
        imgs = page.evaluate(
            """() => Array.from(document.querySelectorAll('img'))
            .map(i => i.src).filter(s => s.includes('googleusercontent')).slice(0, 8)"""
        )
        print({"screenshot": out.as_posix(), "imgs": imgs})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
