from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from episode_artifacts import artifact_paths, load_json

YOUTUBE_TITLE_MAX = 100


def _enforce_title_limit(title: str) -> None:
    """Fail if a YouTube title exceeds the 100-character upload limit (safety net
    — the primary guard is in prepare_episode_youtube_packaging.py)."""
    if len(title) > YOUTUBE_TITLE_MAX:
        raise ValueError(
            f"YouTube title is {len(title)} chars (max {YOUTUBE_TITLE_MAX}). "
            f"Fix the `title` field in youtube.json before exporting. Title: {title!r}"
        )


SERIES_EXPORT = {
    "series_a": "DailyTalk",
    "series_b": "FirstSteps",
    "series_c": "PolishedEnglish",
}


def _copy(src: Path, dest: Path) -> None:
    if not src.is_file():
        raise FileNotFoundError(f"Missing required artifact: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def export_episode(
    *,
    show_id: str,
    episode_num: int,
    workspace: Path,
    youtube_root: Path,
) -> dict[str, Any]:
    if show_id not in SERIES_EXPORT:
        raise ValueError(f"Unknown show_id: {show_id}")
    folder = SERIES_EXPORT[show_id]
    stem = f"episode{episode_num:02d}"
    out_dir = youtube_root / folder / stem

    episode_id = f"episode_{episode_num:03d}"
    paths = artifact_paths(workspace, episode_id)
    candidates = {
        "mp4": paths["mp4"],
        "wav": paths["rawWav"],
        "master": paths["masterWav"],
        "srt": paths["srt"],
        "thumb": paths["thumbnailPng"],
        "thumb_jpg": paths["videoDir"] / f"000_{episode_id}.thumbnail_cover.jpg",
        "youtube": paths["youtube"],
        "description": paths["youtubeDescription"],
    }

    youtube = load_json(candidates["youtube"]) if candidates["youtube"].is_file() else {}
    title = str(youtube.get("title") or youtube.get("hookText") or "").strip()
    if not title:
        raise ValueError("youtube.json missing title/hookText")
    _enforce_title_limit(title)

    out_dir.mkdir(parents=True, exist_ok=True)
    _copy(candidates["mp4"], out_dir / f"{stem}.mp4")
    wav_src = candidates.get("master") if candidates.get("master") and candidates["master"].is_file() else candidates["wav"]
    _copy(wav_src, out_dir / f"{stem}.wav")
    _copy(candidates["srt"], out_dir / f"{stem}.srt")

    cover_src = candidates["thumb"] if candidates["thumb"].is_file() else candidates["thumb_jpg"]
    cover_dest = out_dir / f"{stem}-封面.jpg"
    from PIL import Image

    with Image.open(cover_src) as image:
        # Prefer full-res PNG master → high-quality JPEG (~1.5–2.5MB @ 2K)
        image.convert("RGB").save(cover_dest, format="JPEG", quality=97, optimize=True, subsampling=0)

    desc_src = candidates["description"]
    if not desc_src.is_file():
        raise FileNotFoundError(f"Missing description: {desc_src}")
    _copy(desc_src, out_dir / f"{stem}.youtube_description.txt")
    (out_dir / f"{stem}.youtube_title.txt").write_text(title + "\n", encoding="utf-8", newline="\n")
    _copy(candidates["youtube"], out_dir / f"{stem}.youtube.json")

    # Also place the upload-ready title + description beside the mp4 in the
    # workspace video dir, so the YouTube copy/paste texts sit with the final
    # program artifacts (not only in reports/ and the export dir).
    video_dir = paths["videoDir"]
    (video_dir / f"000_{episode_id}.youtube_title.txt").write_text(title + "\n", encoding="utf-8", newline="\n")
    shutil.copy2(desc_src, video_dir / f"000_{episode_id}.youtube_description.txt")

    return {
        "showId": show_id,
        "episode": stem,
        "outputDir": str(out_dir).replace("\\", "/"),
        "title": title,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export ELR episode package to H:/Youtube series folder.")
    parser.add_argument("--show", required=True, choices=sorted(SERIES_EXPORT))
    parser.add_argument("--episode-num", type=int, default=1)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--youtube-root", default=r"H:\Youtube")
    args = parser.parse_args()
    report = export_episode(
        show_id=args.show,
        episode_num=args.episode_num,
        workspace=Path(args.workspace),
        youtube_root=Path(args.youtube_root),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
