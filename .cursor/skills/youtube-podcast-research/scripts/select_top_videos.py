from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from worker.youtube_podcast_research.workspace import (
    DEFAULT_CHANNELS,
    DEFAULT_CORPUS_ROOT,
    read_json,
    selected_videos_path,
    videos_dir,
    write_json,
)


def select_channel(corpus_root: Path, channel: dict[str, str], top_n: int) -> dict[str, Any]:
    root = videos_dir(corpus_root, channel["slug"])
    records: list[dict[str, Any]] = []
    if root.exists():
        for folder in sorted(path for path in root.iterdir() if path.is_dir()):
            metadata_path = folder / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = read_json(metadata_path)
            records.append(
                {
                    "id": str(metadata.get("id") or folder.name),
                    "title": str(metadata.get("title") or ""),
                    "view_count": int(metadata.get("view_count") or 0),
                }
            )
    ranked = sorted(records, key=lambda item: item["view_count"], reverse=True)[:top_n]
    write_json(
        selected_videos_path(corpus_root, channel["slug"]),
        {
            "selection": "top_by_view_count_from_local_metadata",
            "top_n": top_n,
            "video_ids": [record["id"] for record in ranked],
            "videos": ranked,
        },
    )
    return {"channel": channel["slug"], "selected": len(ranked)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select top archived videos per channel from local metadata.")
    parser.add_argument("--workspace-root", default=str(DEFAULT_CORPUS_ROOT))
    parser.add_argument("--top-n", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus_root = Path(args.workspace_root)
    for channel in DEFAULT_CHANNELS:
        result = select_channel(corpus_root, channel, top_n=args.top_n)
        print(f"channel={result['channel']} selected={result['selected']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
