from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, urlparse

from worker.youtube_podcast_research.workspace import clean_text, write_json


@dataclass
class BrowserConfig:
    headless: bool = True
    profile_dir: Path | None = None
    locale: str = "en-US"
    slow_mo_ms: int = 0
    timeout_ms: int = 30_000
    persistent: bool = False
    browser_channel: str | None = None


def account_browser_config(profile_dir: Path, *, headless: bool = False) -> BrowserConfig:
    return BrowserConfig(
        headless=headless,
        profile_dir=profile_dir,
        persistent=True,
        browser_channel="chrome",
    )


def discovery_browser_config(profile_dir: Path | None, *, headless: bool) -> BrowserConfig:
    use_persistent = bool(profile_dir and (profile_dir / "chrome_user_data").exists())
    if use_persistent:
        return BrowserConfig(
            headless=headless,
            profile_dir=profile_dir,
            persistent=True,
            browser_channel="chrome",
        )
    return BrowserConfig(headless=headless, profile_dir=profile_dir, persistent=False, browser_channel=None)


@dataclass
class YouTubeBrowserSession:
    config: BrowserConfig = field(default_factory=BrowserConfig)
    _playwright: Any = None
    _browser: Any = None
    _context: Any = None
    _page: Any = None
    _persistent: bool = False

    def __enter__(self) -> YouTubeBrowserSession:
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def start(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise SystemExit(
                "playwright is required. Install with:\n"
                "  .\\.conda-env\\python.exe -m pip install -r apps/worker-py/requirements.txt\n"
                "  .\\.conda-env\\python.exe -m playwright install chromium"
            ) from exc

        self._playwright = sync_playwright().start()
        self._persistent = self.config.persistent

        if self._persistent:
            self._start_persistent_context()
        else:
            self._start_ephemeral_context()

    def _start_persistent_context(self) -> None:
        assert self._playwright is not None
        assert self.config.profile_dir is not None
        user_data_dir = self.config.profile_dir / "chrome_user_data"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(user_data_dir),
            "headless": self.config.headless,
            "locale": self.config.locale,
            "slow_mo": self.config.slow_mo_ms,
            "viewport": None,
            "ignore_default_args": ["--enable-automation"],
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }
        channel = self._resolve_browser_channel()
        if channel:
            launch_kwargs["channel"] = channel

        try:
            self._context = self._playwright.chromium.launch_persistent_context(**launch_kwargs)
        except Exception as exc:
            raise SystemExit(
                "Could not launch installed Chrome/Edge for Google login.\n"
                "Install Google Chrome, then rerun save_browser_session.py --headful\n"
                f"Details: {exc}"
            ) from exc

        self._context.set_default_timeout(self.config.timeout_ms)
        self._normalize_persistent_pages()
        self._browser = None

    def _normalize_persistent_pages(self) -> None:
        """Reuse one tab; close stale tabs left from prior sessions or manual Chrome launches."""
        assert self._context is not None
        pages = list(self._context.pages)
        if not pages:
            self._page = self._context.new_page()
            return
        self._page = pages[0]
        for extra in pages[1:]:
            try:
                if not extra.is_closed():
                    extra.close()
            except Exception:
                continue

    def _resolve_browser_channel(self) -> str | None:
        if self.config.browser_channel:
            return self.config.browser_channel
        return "chrome"

    def _start_ephemeral_context(self) -> None:
        assert self._playwright is not None
        launch_kwargs: dict[str, Any] = {"headless": self.config.headless, "slow_mo": self.config.slow_mo_ms}
        self._browser = self._playwright.chromium.launch(**launch_kwargs)
        context_kwargs: dict[str, Any] = {"locale": self.config.locale}
        if self.config.profile_dir:
            self.config.profile_dir.mkdir(parents=True, exist_ok=True)
            storage_state = self._storage_state_path()
            if storage_state:
                context_kwargs["storage_state"] = storage_state
        self._context = self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self.config.timeout_ms)
        self._page = self._context.new_page()

    def close(self) -> None:
        if self._context and self.config.profile_dir and not self._persistent:
            self.save_storage_state()
        if self._context:
            for page in list(self._context.pages):
                try:
                    if not page.is_closed():
                        page.close()
                except Exception:
                    continue
        if self._persistent and self._context:
            self._context.close()
        else:
            for resource in (self._context, self._browser):
                if resource:
                    resource.close()
        if self._playwright:
            self._playwright.stop()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _storage_state_path(self) -> str | None:
        if not self.config.profile_dir:
            return None
        path = self.config.profile_dir / "storage_state.json"
        return str(path) if path.exists() else None

    def save_storage_state(self) -> None:
        if not self._context or not self.config.profile_dir or self._persistent:
            return
        path = self.config.profile_dir / "storage_state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._context.storage_state(path=str(path))

    def goto(self, url: str) -> None:
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded")

    def search(self, query: str, *, scroll_rounds: int = 2) -> list[dict[str, Any]]:
        assert self._page is not None
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
        self.goto(url)
        self._page.wait_for_timeout(1500)
        self._dismiss_consent_if_present()
        for _ in range(max(scroll_rounds, 0)):
            self._page.mouse.wheel(0, 2500)
            self._page.wait_for_timeout(900)
        return self.extract_search_results()

    def _dismiss_consent_if_present(self) -> None:
        assert self._page is not None
        selectors = (
            'button:has-text("Accept all")',
            'button:has-text("Reject all")',
            'button:has-text("I agree")',
        )
        for selector in selectors:
            locator = self._page.locator(selector)
            if locator.count() > 0:
                try:
                    locator.first.click(timeout=2000)
                    self._page.wait_for_timeout(500)
                    return
                except Exception:
                    continue

    def extract_search_results(self) -> list[dict[str, Any]]:
        assert self._page is not None
        script = """
        () => {
          const cards = Array.from(document.querySelectorAll('ytd-video-renderer, ytd-grid-video-renderer'));
          return cards.map(card => {
            const titleEl = card.querySelector('#video-title, a#video-title');
            const channelEl = card.querySelector('#channel-name a, ytd-channel-name a');
            const metaEl = card.querySelector('#metadata-line, #metadata');
            const href = titleEl ? titleEl.href : '';
            return {
              title: titleEl ? titleEl.textContent.trim() : '',
              url: href,
              channel_name: channelEl ? channelEl.textContent.trim() : '',
              channel_url: channelEl ? channelEl.href : '',
              metadata_text: metaEl ? metaEl.textContent.trim() : '',
            };
          }).filter(item => item.url);
        }
        """
        raw_items = self._page.evaluate(script)
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw_items:
            video_id = extract_video_id(str(item.get("url") or ""))
            if not video_id or video_id in seen:
                continue
            seen.add(video_id)
            metadata_text = str(item.get("metadata_text") or "")
            results.append(
                {
                    "video_id": video_id,
                    "title": clean_text(str(item.get("title") or "")),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel_name": clean_text(str(item.get("channel_name") or "")),
                    "channel_url": str(item.get("channel_url") or ""),
                    "metadata_text": metadata_text,
                    "views_text": parse_views_text(metadata_text),
                }
            )
        return results

    def screenshot(self, path: Path) -> None:
        assert self._page is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._page.screenshot(path=str(path), full_page=True)


def extract_video_id(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.hostname and "youtu" in parsed.hostname:
        if parsed.path == "/watch":
            return (parse_qs(parsed.query).get("v") or [""])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/", 1)[-1].split("/", 1)[0]
        if parsed.hostname == "youtu.be":
            return parsed.path.lstrip("/").split("/", 1)[0]
    match = re.search(r"(?:v=|/shorts/|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
    return match.group(1) if match else ""


def parse_views_text(metadata_text: str) -> int | None:
    match = re.search(r"([\d.,]+)\s*([KMB])?\s*views", metadata_text, re.I)
    if not match:
        return None
    number = float(match.group(1).replace(",", ""))
    suffix = (match.group(2) or "").upper()
    multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(suffix, 1)
    return int(number * multiplier)


def run_search_batch(
    queries: list[str],
    *,
    profile_dir: Path | None,
    headless: bool,
    scroll_rounds: int,
    pause_seconds: float,
) -> dict[str, Any]:
    started = time.time()
    all_results: list[dict[str, Any]] = []
    by_query: dict[str, list[dict[str, Any]]] = {}
    config = discovery_browser_config(profile_dir, headless=headless)
    with YouTubeBrowserSession(config=config) as session:
        for query in queries:
            items = session.search(query, scroll_rounds=scroll_rounds)
            by_query[query] = items
            all_results.extend({**item, "query": query} for item in items)
            if pause_seconds:
                time.sleep(pause_seconds)
    deduped: dict[str, dict[str, Any]] = {}
    for item in all_results:
        deduped[item["video_id"]] = item
    return {
        "schema": "dialogue-podcast-youtube-discovery-v1",
        "query_count": len(queries),
        "result_count": len(deduped),
        "elapsed_seconds": round(time.time() - started, 2),
        "queries": by_query,
        "videos": list(deduped.values()),
    }
