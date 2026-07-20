from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import (
    DEFAULT_CORPUS_ROOT,
    composite_trend_score,
    ensure_dir,
    iter_video_records,
    trending_path,
    write_json,
)


def score_corpus(
    corpus_root: Path,
    *,
    dual_host_only: bool,
    min_views: int,
    limit: int,
) -> dict[str, Any]:
    ranked: list[dict[str, Any]] = []
    for record in iter_video_records(corpus_root):
        metadata = record["metadata"]
        title = str(metadata.get("title") or "")
        description = record["description"]
        transcript = record["transcript"]
        score = composite_trend_score(metadata, title=title, description=description, transcript=transcript)
        if int(score["view_count"]) < min_views:
            continue
        if dual_host_only and not score["dual_host"]["likely_dual_host"]:
            continue
        ranked.append(
            {
                "video_id": metadata.get("id"),
                "title": title,
                "url": metadata.get("webpage_url"),
                "channel_slug": record["channel"]["slug"],
                "channel_name": record["channel"]["name"],
                "upload_date": metadata.get("upload_date"),
                "has_transcript": bool(transcript.strip()),
                **score,
            }
        )

    ranked.sort(key=lambda item: float(item["trend_score"]), reverse=True)
    return {
        "schema": "dialogue-podcast-trending-videos-v1",
        "corpus_root": str(corpus_root.as_posix()),
        "filters": {"dual_host_only": dual_host_only, "min_views": min_views, "limit": limit},
        "video_count": len(ranked[:limit]),
        "videos": ranked[:limit],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank archived YouTube videos by engagement and growth signals.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--dual-host-only", action="store_true")
    parser.add_argument("--min-views", type=int, default=1000)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    output = Path(args.output) if args.output else trending_path(corpus_root)
    ensure_dir(output.parent)
    payload = score_corpus(
        corpus_root,
        dual_host_only=args.dual_host_only,
        min_views=args.min_views,
        limit=args.limit,
    )
    write_json(output, payload)
    print(f"trending={output}")
    print(f"videos={payload['video_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
