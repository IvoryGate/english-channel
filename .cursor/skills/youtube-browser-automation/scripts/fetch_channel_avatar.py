from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path

import _bootstrap  # noqa: F401

DEFAULT_CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"


def fetch_channel_html(channel_id: str) -> str:
    url = f"https://www.youtube.com/channel/{channel_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="ignore")


def extract_avatar_urls(html: str) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(r"https://yt3\.googleusercontent\.com/[^\"\\]+", html):
        url = match.group(0)
        if any(token in url for token in ("=s48", "=s88", "=s176", "=s240", "=s800")):
            urls.append(url)
    # Fallback: avatar object in ytInitialData
    avatar_block = re.search(r'"avatar"\s*:\s*\{\s*"thumbnails"\s*:\s*(\[[^\]]+\])', html)
    if avatar_block:
        try:
            thumbs = json.loads(avatar_block.group(1))
            urls.extend(str(item.get("url", "")) for item in thumbs if item.get("url"))
        except json.JSONDecodeError:
            pass
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def pick_best_avatar(urls: list[str]) -> str:
    if not urls:
        return ""
    ranked = sorted(urls, key=lambda u: int(re.search(r"=s(\d+)", u).group(1)) if re.search(r"=s(\d+)", u) else 0, reverse=True)
    return ranked[0]


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=30).read()
    output.write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch YouTube channel avatar.")
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--output", default="workspace/dialogue_podcast_research/youtube_corpus/analysis/channel_avatar.jpg")
    args = parser.parse_args()

    html = fetch_channel_html(args.channel_id)
    urls = extract_avatar_urls(html)
    best = pick_best_avatar(urls)
    if not best:
        print(json.dumps({"error": "avatar_not_found", "candidate_count": 0}, ensure_ascii=False))
        return 1
    output = Path(args.output)
    download(best, output)
    print(json.dumps({"avatar_url": best, "output": output.as_posix(), "candidates": len(urls)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
