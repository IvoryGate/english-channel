from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.rate_limit import (
    DEFAULT_ENRICH_PAUSE_SEC,
    DEFAULT_MAX_SLEEP_INTERVAL_SEC,
    DEFAULT_SLEEP_INTERVAL_SEC,
    YouTubeRateLimitError,
    guard_rate_limit,
    merge_ydl_opts,
    pause_between_requests,
)
from worker.youtube_podcast_research.browser import run_search_batch
from worker.youtube_podcast_research.workspace import (
    DEFAULT_CORPUS_ROOT,
    DEFAULT_SEARCH_QUERIES,
    browser_profile_dir,
    composite_trend_score,
    discovery_dir,
    dual_host_signals,
    ensure_dir,
    write_json,
)


def load_yt_dlp() -> Any:
    try:
        import yt_dlp
    except ImportError as exc:
        raise SystemExit(
            "yt-dlp is required. Install: .\\.conda-env\\python.exe -m pip install -r apps/worker-py/requirements.txt"
        ) from exc
    return yt_dlp


def enrich_with_yt_dlp(
    videos: list[dict[str, Any]],
    *,
    sleep_interval: float,
    max_sleep_interval: float,
    request_pause: float,
) -> list[dict[str, Any]]:
    yt_dlp = load_yt_dlp()
    opts = merge_ydl_opts(
        {"quiet": True, "no_warnings": True, "skip_download": True, "ignoreerrors": True},
        sleep_interval=sleep_interval,
        max_sleep_interval=max_sleep_interval,
    )
    enriched: list[dict[str, Any]] = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        for index, video in enumerate(videos):
            if index > 0:
                pause_between_requests(request_pause, label=f"enrich {video.get('url', '')[:48]}")
            item = dict(video)
            try:
                info = ydl.extract_info(item["url"], download=False) or {}
            except YouTubeRateLimitError:
                raise
            except Exception as exc:
                guard_rate_limit(exc)
                item["metadata_error"] = str(exc)
                enriched.append(item)
                continue
            item["metadata"] = {
                "view_count": int(info.get("view_count") or 0),
                "like_count": int(info.get("like_count") or 0),
                "comment_count": int(info.get("comment_count") or 0),
                "upload_date": info.get("upload_date"),
                "duration": info.get("duration"),
                "description": str(info.get("description") or "")[:2000],
            }
            score = composite_trend_score(
                item["metadata"],
                title=item.get("title", ""),
                description=str(item["metadata"].get("description") or ""),
            )
            item["trend_score"] = score["trend_score"]
            item["dual_host"] = score["dual_host"]
            enriched.append(item)
    return enriched


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover dual-host English podcast candidates on YouTube.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--query", action="append")
    parser.add_argument("--scroll-rounds", type=int, default=2)
    parser.add_argument("--pause-seconds", type=float, default=3.0, help="Browser scroll pause between actions.")
    parser.add_argument("--headful", action="store_true")
    parser.add_argument("--enrich", action="store_true")
    parser.add_argument("--dual-host-only", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--sleep-interval",
        type=float,
        default=DEFAULT_SLEEP_INTERVAL_SEC,
        help="yt-dlp sleep_interval for --enrich (default: 5).",
    )
    parser.add_argument(
        "--max-sleep-interval",
        type=float,
        default=DEFAULT_MAX_SLEEP_INTERVAL_SEC,
        help="yt-dlp max_sleep_interval for --enrich (default: 10).",
    )
    parser.add_argument(
        "--enrich-pause",
        type=float,
        default=DEFAULT_ENRICH_PAUSE_SEC,
        help="Extra pause seconds between each enriched video (default: 6).",
    )
    parser.add_argument(
        "--max-enrich",
        type=int,
        default=30,
        help="Cap how many discovery videos get yt-dlp enrichment per run (default: 30).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    ensure_dir(discovery_dir(corpus_root))
    queries = args.query or list(DEFAULT_SEARCH_QUERIES)
    if args.smoke:
        queries = queries[:1]
    scroll_rounds = 0 if args.smoke else args.scroll_rounds

    try:
        payload = run_search_batch(
            queries,
            profile_dir=browser_profile_dir(corpus_root),
            headless=not args.headful,
            scroll_rounds=scroll_rounds,
            pause_seconds=0.0 if args.smoke else args.pause_seconds,
        )

        if args.enrich or args.dual_host_only:
            to_enrich = payload["videos"][: args.max_enrich]
            if len(payload["videos"]) > len(to_enrich):
                print(f"rate_limit: enriching {len(to_enrich)} of {len(payload['videos'])} discovery videos (--max-enrich)")
            payload["videos"] = enrich_with_yt_dlp(
                to_enrich,
                sleep_interval=args.sleep_interval,
                max_sleep_interval=args.max_sleep_interval,
                request_pause=args.enrich_pause,
            )

        if args.dual_host_only:
            filtered: list[dict[str, Any]] = []
            for video in payload["videos"]:
                dual_host = video.get("dual_host")
                if dual_host is None:
                    dual_host = dual_host_signals(
                        str(video.get("title") or ""),
                        str((video.get("metadata") or {}).get("description") or ""),
                    )
                if dual_host.get("likely_dual_host"):
                    filtered.append(video)
            payload["videos"] = filtered
            payload["result_count"] = len(filtered)

        output = discovery_dir(corpus_root) / ("discovery_smoke.json" if args.smoke else "discovery_latest.json")
        write_json(output, payload)
        print(f"discovery={output}")
        print(f"videos={payload['result_count']}")
        return 0
    except YouTubeRateLimitError as exc:
        print(f"RATE_LIMIT: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
