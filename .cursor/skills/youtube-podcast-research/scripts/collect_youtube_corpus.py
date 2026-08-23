from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.rate_limit import (
    DEFAULT_CHANNEL_PAUSE_SEC,
    DEFAULT_MAX_SLEEP_INTERVAL_SEC,
    DEFAULT_REQUEST_PAUSE_SEC,
    DEFAULT_SLEEP_INTERVAL_SEC,
    YouTubeRateLimitError,
    guard_rate_limit,
    merge_ydl_opts,
    pause_between_requests,
)
from worker.youtube_podcast_research.workspace import (
    DEFAULT_CHANNELS,
    DEFAULT_CORPUS_ROOT,
    analysis_dir,
    clean_text,
    ensure_dir,
    normalize_video_id,
    selected_videos_path,
    strip_vtt_to_text,
    transcript_files,
    video_dir,
    video_url,
    videos_dir,
    write_json,
    write_text,
)

METADATA_FIELDS = (
    "id",
    "webpage_url",
    "original_url",
    "title",
    "description",
    "channel",
    "channel_id",
    "channel_url",
    "uploader",
    "uploader_id",
    "duration",
    "view_count",
    "like_count",
    "comment_count",
    "upload_date",
    "timestamp",
    "categories",
    "tags",
    "availability",
    "age_limit",
    "language",
    "thumbnail",
)


def load_yt_dlp() -> Any:
    try:
        import yt_dlp
    except ImportError as exc:
        raise SystemExit(
            "yt-dlp is required. Install dependencies with: "
            ".\\.conda-env\\python.exe -m pip install -r apps/worker-py/requirements.txt"
        ) from exc
    return yt_dlp


def channel_listing_url(channel_url: str, popular: bool) -> str:
    base = channel_url.rstrip("/")
    if popular:
        return f"{base}/videos?view=0&sort=p&flow=grid"
    return f"{base}/videos"


def ydl_opts(**overrides: Any) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "extractor_args": {"youtube": {"skip": ["dash", "hls"]}},
    }
    opts.update(overrides)
    return opts


def ydl_opts_with_sleep(
    *,
    sleep_interval: float,
    max_sleep_interval: float,
    **overrides: Any,
) -> dict[str, Any]:
    return merge_ydl_opts(ydl_opts(**overrides), sleep_interval=sleep_interval, max_sleep_interval=max_sleep_interval)


def collect_candidate_ids(
    yt_dlp: Any,
    channel_url: str,
    candidate_limit: int,
    popular: bool,
    *,
    sleep_interval: float,
    max_sleep_interval: float,
) -> list[str]:
    opts = ydl_opts_with_sleep(
        sleep_interval=sleep_interval,
        max_sleep_interval=max_sleep_interval,
        extract_flat=True,
        playlistend=candidate_limit,
    )
    ids: list[str] = []
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(channel_listing_url(channel_url, popular=popular), download=False)
    for entry in (info or {}).get("entries") or []:
        if not entry:
            continue
        video_id = normalize_video_id(str(entry.get("id") or entry.get("url") or ""))
        if video_id and video_id not in ids:
            ids.append(video_id)
    return ids


def fetch_video_metadata(
    yt_dlp: Any,
    video_id: str,
    *,
    sleep_interval: float,
    max_sleep_interval: float,
) -> dict[str, Any]:
    with yt_dlp.YoutubeDL(ydl_opts_with_sleep(sleep_interval=sleep_interval, max_sleep_interval=max_sleep_interval)) as ydl:
        info = ydl.extract_info(video_url(video_id), download=False)
    return sanitize_metadata(info or {})


def sanitize_metadata(info: dict[str, Any]) -> dict[str, Any]:
    metadata = {field: info.get(field) for field in METADATA_FIELDS if field in info}
    metadata["id"] = normalize_video_id(str(metadata.get("id") or info.get("display_id") or ""))
    metadata["webpage_url"] = info.get("webpage_url") or video_url(str(metadata["id"]))
    metadata["subtitle_languages"] = sorted((info.get("subtitles") or {}).keys())
    metadata["automatic_caption_languages"] = sorted((info.get("automatic_captions") or {}).keys())
    metadata["view_count"] = int(metadata.get("view_count") or 0)
    metadata["title"] = clean_text(str(metadata.get("title") or ""))
    return metadata


def write_transcript_text(folder: Path) -> dict[str, Any]:
    files = transcript_files(folder)
    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = strip_vtt_to_text(raw) if path.suffix.lower() != ".txt" else raw.strip()
        if text:
            write_text(folder / "transcript.txt", text)
            return {
                "status": "available",
                "source_file": path.name,
                "text_file": "transcript.txt",
                "char_count": len(text),
            }
    return {"status": "missing", "source_file": None, "text_file": None, "char_count": 0}


def download_transcript(
    yt_dlp: Any,
    metadata: dict[str, Any],
    folder: Path,
    language: str,
    *,
    sleep_interval: float,
    max_sleep_interval: float,
) -> dict[str, Any]:
    outtmpl = str(folder / "%(id)s.%(ext)s")
    opts = ydl_opts_with_sleep(
        sleep_interval=sleep_interval,
        max_sleep_interval=max_sleep_interval,
        outtmpl=outtmpl,
        writesubtitles=True,
        writeautomaticsub=True,
        subtitleslangs=[language],
        subtitlesformat="vtt/best",
        skip_download=False,
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([metadata["webpage_url"]])
    except Exception as exc:
        guard_rate_limit(exc)
        return {"status": "error", "error": str(exc)}
    return write_transcript_text(folder)


def archive_channel_config(corpus_root: Path, channels: list[dict[str, str]]) -> None:
    write_json(
        corpus_root / "channels.json",
        {
            "schema": "dialogue-podcast-youtube-corpus-v1",
            "channels": channels,
            "artifact_policy": "metadata_description_transcripts_only_no_audio_video",
        },
    )


def collect_channel(
    yt_dlp: Any,
    corpus_root: Path,
    channel: dict[str, str],
    top_n: int,
    candidate_limit: int,
    language: str,
    refresh: bool,
    popular: bool,
    *,
    sleep_interval: float,
    max_sleep_interval: float,
    request_pause: float,
) -> dict[str, Any]:
    ensure_dir(videos_dir(corpus_root, channel["slug"]))
    write_json(corpus_root / channel["slug"] / "channel.json", channel)

    candidate_ids = collect_candidate_ids(
        yt_dlp,
        channel["url"],
        candidate_limit=candidate_limit,
        popular=popular,
        sleep_interval=sleep_interval,
        max_sleep_interval=max_sleep_interval,
    )
    pause_between_requests(request_pause, label=f"after listing {channel['slug']}")

    fetched: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for index, video_id in enumerate(candidate_ids):
        if index > 0:
            pause_between_requests(request_pause, label=f"metadata {channel['slug']} {video_id}")
        try:
            fetched.append(
                fetch_video_metadata(
                    yt_dlp,
                    video_id,
                    sleep_interval=sleep_interval,
                    max_sleep_interval=max_sleep_interval,
                )
            )
        except YouTubeRateLimitError:
            raise
        except Exception as exc:
            guard_rate_limit(exc)
            errors.append({"video_id": video_id, "error": str(exc)})

    ranked = sorted(fetched, key=lambda item: int(item.get("view_count") or 0), reverse=True)[:top_n]
    write_json(
        selected_videos_path(corpus_root, channel["slug"]),
        {
            "selection": "top_by_view_count",
            "top_n": top_n,
            "candidate_limit": candidate_limit,
            "video_ids": [str(metadata["id"]) for metadata in ranked],
        },
    )
    archived: list[dict[str, Any]] = []
    for index, metadata in enumerate(ranked):
        folder = video_dir(corpus_root, channel["slug"], str(metadata["id"]))
        ensure_dir(folder)
        metadata_path = folder / "metadata.json"
        if metadata_path.exists() and not refresh:
            archived.append({"video_id": str(metadata["id"]), "status": "skipped_existing", "path": str(metadata_path.as_posix())})
            continue

        if index > 0:
            pause_between_requests(request_pause, label=f"transcript {channel['slug']} {metadata['id']}")

        description = str(metadata.get("description") or "")
        write_json(metadata_path, {**metadata, "collection_channel": channel})
        write_text(folder / "description.txt", description)
        transcript_status = download_transcript(
            yt_dlp,
            metadata,
            folder,
            language=language,
            sleep_interval=sleep_interval,
            max_sleep_interval=max_sleep_interval,
        )
        write_json(
            folder / "collection_status.json",
            {
                "video_id": metadata["id"],
                "title": metadata.get("title"),
                "view_count": metadata.get("view_count"),
                "transcript": transcript_status,
            },
        )
        archived.append({"video_id": str(metadata["id"]), "status": "archived", "transcript": transcript_status})

    return {
        "channel": channel,
        "candidate_count": len(candidate_ids),
        "metadata_count": len(fetched),
        "archived_count": len(archived),
        "errors": errors,
        "videos": archived,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect local YouTube research corpus.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--candidate-limit", type=int, default=40, help="Max listing candidates per channel (lower = safer).")
    parser.add_argument("--language", default="en")
    parser.add_argument("--channel", action="append", choices=[channel["slug"] for channel in DEFAULT_CHANNELS])
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--recent-order", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument(
        "--sleep-interval",
        type=float,
        default=DEFAULT_SLEEP_INTERVAL_SEC,
        help="yt-dlp sleep_interval seconds between internal requests (default: 5).",
    )
    parser.add_argument(
        "--max-sleep-interval",
        type=float,
        default=DEFAULT_MAX_SLEEP_INTERVAL_SEC,
        help="yt-dlp max_sleep_interval seconds (default: 10).",
    )
    parser.add_argument(
        "--request-pause",
        type=float,
        default=DEFAULT_REQUEST_PAUSE_SEC,
        help="Extra pause seconds between each video metadata/transcript step (default: 5).",
    )
    parser.add_argument(
        "--channel-pause",
        type=float,
        default=DEFAULT_CHANNEL_PAUSE_SEC,
        help="Pause seconds between channels (default: 30).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    ensure_dir(analysis_dir(corpus_root))
    yt_dlp = load_yt_dlp()

    channels = [dict(channel) for channel in DEFAULT_CHANNELS if not args.channel or channel["slug"] in args.channel]
    archive_channel_config(corpus_root, channels)

    top_n = 1 if args.smoke else args.top_n
    candidate_limit = min(args.candidate_limit, 6) if args.smoke else args.candidate_limit
    summary = {"top_n": top_n, "candidate_limit": candidate_limit, "language": args.language, "channels": []}
    try:
        for index, channel in enumerate(channels):
            if index > 0:
                pause_between_requests(args.channel_pause, label=f"channel boundary before {channel['slug']}")
            result = collect_channel(
                yt_dlp,
                corpus_root,
                channel,
                top_n=top_n,
                candidate_limit=candidate_limit,
                language=args.language,
                refresh=args.refresh,
                popular=not args.recent_order,
                sleep_interval=args.sleep_interval,
                max_sleep_interval=args.max_sleep_interval,
                request_pause=args.request_pause,
            )
            summary["channels"].append(result)
            print(f"channel={channel['slug']} archived={result['archived_count']} candidates={result['candidate_count']}")

        write_json(corpus_root / "collection_summary.json", summary)
        print(f"summary={corpus_root / 'collection_summary.json'}")
        return 0
    except YouTubeRateLimitError as exc:
        write_json(corpus_root / "collection_summary.json", {**summary, "rate_limit_error": str(exc)})
        print(f"RATE_LIMIT: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
