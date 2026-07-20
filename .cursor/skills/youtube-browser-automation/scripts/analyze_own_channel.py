from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.browser import YouTubeBrowserSession, account_browser_config
from worker.youtube_podcast_research.workspace import (
    analysis_dir,
    browser_profile_dir,
    clean_text,
    composite_trend_score,
    ensure_dir,
    keyword_counts,
    write_json,
)

DEFAULT_CHANNEL_ID = "UC9QpAkVpv8l1ZQ3X4UtU37A"


def load_yt_dlp() -> Any:
    import yt_dlp

    return yt_dlp


def parse_upload_date(value: str | None) -> datetime | None:
    if not value or not re.fullmatch(r"\d{8}", str(value)):
        return None
    return datetime.strptime(str(value), "%Y%m%d").replace(tzinfo=timezone.utc)


def fetch_public_videos(channel_id: str, limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    yt_dlp = load_yt_dlp()
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    opts: dict[str, Any] = {"quiet": True, "ignoreerrors": True, "playlistend": limit}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    channel = {
        "id": info.get("channel_id") or channel_id,
        "name": info.get("channel") or info.get("uploader"),
        "url": info.get("channel_url") or f"https://www.youtube.com/channel/{channel_id}",
        "description": str(info.get("description") or "")[:3000],
        "channel_follower_count": int(info.get("channel_follower_count") or 0),
        "playlist_count": info.get("playlist_count"),
    }
    videos: list[dict[str, Any]] = []
    for entry in info.get("entries") or []:
        if not entry:
            continue
        videos.append(
            {
                "id": entry.get("id"),
                "title": clean_text(str(entry.get("title") or "")),
                "view_count": int(entry.get("view_count") or 0),
                "like_count": int(entry.get("like_count") or 0),
                "comment_count": int(entry.get("comment_count") or 0),
                "duration": entry.get("duration"),
                "upload_date": entry.get("upload_date"),
                "url": entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                "description": str(entry.get("description") or "")[:1500],
            }
        )
    return channel, videos


def classify_title(title: str) -> list[str]:
    labels: list[str] = []
    patterns = {
        "question": re.compile(r"\?|\b(why|what|how|when|where|which)\b", re.I),
        "how_to": re.compile(r"\bhow to\b|\blearn\b|\bpractice\b|\bimprove\b", re.I),
        "list": re.compile(r"\b\d+\b|\b(tips|ways|phrases|things)\b", re.I),
        "conversation": re.compile(r"\b(conversation|dialogue|podcast|speaking|talk)\b", re.I),
        "story": re.compile(r"\b(story|life|day|experience|mistake)\b", re.I),
    }
    for label, pattern in patterns.items():
        if pattern.search(title):
            labels.append(label)
    return labels or ["general"]


def summarize_videos(videos: list[dict[str, Any]]) -> dict[str, Any]:
    views = [v["view_count"] for v in videos if v.get("view_count")]
    durations = [int(v["duration"]) for v in videos if v.get("duration")]
    pattern_counter: Counter[str] = Counter()
    for video in videos:
        pattern_counter.update(classify_title(video.get("title", "")))

    scored = []
    for video in videos:
        score = composite_trend_score(
            {
                "view_count": video.get("view_count"),
                "like_count": video.get("like_count"),
                "comment_count": video.get("comment_count"),
                "upload_date": video.get("upload_date"),
            },
            title=video.get("title", ""),
            description=video.get("description", ""),
        )
        scored.append({**video, "trend_score": score["trend_score"], "engagement_rate": score["engagement_rate"]})

    upload_dates = [parse_upload_date(v.get("upload_date")) for v in videos]
    upload_dates = [d for d in upload_dates if d]
    return {
        "video_count": len(videos),
        "total_views": sum(views),
        "average_views": round(mean(views), 1) if views else 0,
        "median_views": median(views) if views else 0,
        "average_duration_sec": round(mean(durations), 1) if durations else 0,
        "title_patterns": dict(pattern_counter.most_common()),
        "title_keywords": keyword_counts([v.get("title", "") for v in videos], limit=15),
        "top_by_views": sorted(scored, key=lambda item: int(item.get("view_count") or 0), reverse=True)[:8],
        "top_by_trend_score": sorted(scored, key=lambda item: float(item.get("trend_score") or 0), reverse=True)[:8],
        "recent_videos": sorted(
            [v for v in scored if v.get("upload_date")],
            key=lambda item: str(item.get("upload_date")),
            reverse=True,
        )[:8],
        "upload_span": {
            "earliest": min(upload_dates).strftime("%Y-%m-%d") if upload_dates else None,
            "latest": max(upload_dates).strftime("%Y-%m-%d") if upload_dates else None,
        },
    }


def scrape_studio_dashboard(profile_dir: Path, channel_id: str) -> dict[str, Any]:
    config = account_browser_config(profile_dir, headless=True)
    url = f"https://studio.youtube.com/channel/{channel_id}"
    script = """
    () => {
      const text = document.body ? document.body.innerText : '';
      const pick = (pattern) => {
        const m = text.match(pattern);
        return m ? m[1].trim() : '';
      };
      return {
        title: document.title || '',
        url: location.href,
        heading: (document.querySelector('h1, yt-formatted-string#title') || {}).textContent?.trim?.() || '',
        body_excerpt: text.slice(0, 4000),
        subscriberText: pick(/([\\d.,]+[KMB]?)\\s*(subscriber|订阅者|位订阅者)/i),
        viewsText: pick(/([\\d.,]+[KMB]?)\\s*(views|次观看|观看)/i),
        hasSignIn: /Sign in|登录/.test(text),
      };
    }
    """
    with YouTubeBrowserSession(config=config) as session:
        assert session._page is not None
        session.goto(url)
        session._page.wait_for_timeout(5000)
        return session._page.evaluate(script)


def build_recommendations(channel: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    recs: list[str] = []
    patterns = summary.get("title_patterns") or {}
    avg_views = float(summary.get("average_views") or 0)
    avg_duration = float(summary.get("average_duration_sec") or 0)

    if patterns.get("conversation", 0) >= patterns.get("list", 0):
        recs.append("Your catalog already leans conversational; keep polishing daily-talk titles with one concrete situation per video.")
    else:
        recs.append("Top titles skew list/how-to shaped; test more scene-first or paradox titles to match polished_english positioning.")

    if avg_duration and avg_duration < 480:
        recs.append("Average runtime is under 8 minutes; for polished_english full episodes, consider a 15-20 minute lane if retention allows.")
    elif avg_duration and avg_duration > 1200:
        recs.append("Average runtime is long; ensure early stake and a mid-episode pocket to protect retention.")

    if avg_views:
        recs.append("Use top-performing title shapes as packaging inspiration only; write original Leo/Mia scripts rather than copying competitor phrasing.")

    if not channel.get("description"):
        recs.append("Channel description is empty or very short; add a clear B1-B2 promise and who the show is for.")

    recs.append("Next ops step: compare your top 5 videos against competitor briefs from youtube-corpus-analysis before drafting episode_002.")
    return recs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze the connected YouTube channel.")
    parser.add_argument("--workspace-root", default="workspace/dialogue_podcast_research/youtube_corpus")
    parser.add_argument("--channel-id", default=DEFAULT_CHANNEL_ID)
    parser.add_argument("--video-limit", type=int, default=50)
    parser.add_argument("--skip-studio", action="store_true")
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    output = Path(args.output) if args.output else analysis_dir(corpus_root) / "own_channel_analysis.json"
    ensure_dir(output.parent)

    channel, videos = fetch_public_videos(args.channel_id, limit=args.video_limit)
    summary = summarize_videos(videos)
    studio: dict[str, Any] = {}
    if not args.skip_studio:
        try:
            studio = scrape_studio_dashboard(browser_profile_dir(corpus_root), args.channel_id)
        except SystemExit as exc:
            studio = {"error": str(exc)}
        except Exception as exc:
            studio = {"error": str(exc)}

    analysis = {
        "schema": "youtube-own-channel-analysis-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "public_video_summary": summary,
        "studio_snapshot": studio,
        "recommendations": build_recommendations(channel, summary),
    }
    write_json(output, analysis)
    print(f"analysis={output.as_posix()}")
    print(f"channel={channel.get('name')} videos={summary.get('video_count')} avg_views={summary.get('average_views')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
