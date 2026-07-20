from __future__ import annotations

import argparse
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import analysis_dir, browser_profile_dir, ensure_dir, has_chrome_user_profile

DEFAULT_CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"
URL = "https://studio.youtube.com/channel/{channel_id}/editing/images"

PROBE_JS = """
() => {
  const out = { buttons: [], fileInputs: [], texts: [] };
  const seen = new Set();
  const walk = (root) => {
    if (!root) return;
    root.querySelectorAll('button, ytcp-button, tp-yt-paper-button').forEach(el => {
      const label = (el.getAttribute('aria-label') || el.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 120);
      if (label && !seen.has(label)) {
        seen.add(label);
        out.buttons.push(label);
      }
    });
    root.querySelectorAll('input[type="file"]').forEach((el, i) => {
      out.fileInputs.push({ index: i, accept: el.accept || '', hidden: el.hidden, id: el.id || '' });
    });
    if (root.shadowRoot) walk(root.shadowRoot);
    root.querySelectorAll('*').forEach(el => { if (el.shadowRoot) walk(el.shadowRoot); });
  };
  walk(document);
  ['Profile picture', '频道图片', 'Banner', '横幅', 'Branding', '品牌', 'Upload', '上传', 'Change', '更改'].forEach(t => {
    if (document.body && document.body.innerText.includes(t)) out.texts.push(t);
  });
  return out;
}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    args = parser.parse_args()
    corpus_root = Path(args.workspace_root)
    if not has_chrome_user_profile(corpus_root):
        raise SystemExit("No chrome profile")

    profile_dir = browser_profile_dir(corpus_root)
    config = account_browser_config(profile_dir, headless=True)
    url = URL.format(channel_id=args.channel_id)
    out_dir = ensure_dir(analysis_dir(corpus_root))

    with YouTubeBrowserSession(config=config) as session:
        assert session._page is not None
        page = session._page
        session.goto(url)
        page.wait_for_timeout(2000)
        skip = page.locator('a:has-text("跳至 YOUTUBE 工作室"), a:has-text("Skip to YouTube Studio")').first
        if skip.count():
            skip.click()
            page.wait_for_timeout(5000)
        probe = page.evaluate(PROBE_JS)
        shot = out_dir / "studio_branding_probe.png"
        session.screenshot(shot)
        result = {
            "url": page.url,
            "title": page.title(),
            "page_count": len(session._context.pages) if session._context else 0,
            "probe": probe,
            "screenshot": shot.as_posix(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
