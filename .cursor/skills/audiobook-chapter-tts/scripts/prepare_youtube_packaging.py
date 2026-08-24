from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from audiobook_workspace import (
    DEFAULT_VIDEO_INTRO_OFFSET_SEC,
    assemble_youtube_description,
    chapter_timeline,
    chapter_youtube_path,
    ensure_segment_defaults,
    format_youtube_timestamps_block,
    load_json,
    manifest_path,
    resolve_youtube_markers,
    write_json,
)


def prepare_youtube_packaging(
    workspace: Path,
    *,
    intro_offset_sec: float = DEFAULT_VIDEO_INTRO_OFFSET_SEC,
    write_description_file: bool = True,
) -> dict[str, Any]:
    manifest = ensure_segment_defaults(load_json(manifest_path(workspace)))
    timeline = chapter_timeline(workspace, manifest)
    packaging_path = chapter_youtube_path(workspace)
    packaging = load_json(packaging_path) if packaging_path.is_file() else {}

    markers = packaging.get("chapterMarkers") or []
    if not markers:
        raise ValueError(
            f"No chapterMarkers found in {packaging_path.as_posix()}. "
            "Add 4-8 plot markers with segmentId and label first."
        )

    resolved = resolve_youtube_markers(
        timeline,
        markers,
        intro_offset_sec=intro_offset_sec,
    )
    timestamps_block = format_youtube_timestamps_block(resolved)

    packaging["videoIntroOffsetSec"] = intro_offset_sec
    packaging["chapterMarkers"] = resolved
    packaging["descriptionTimestampsBlock"] = timestamps_block
    packaging["description"] = assemble_youtube_description({**packaging, "descriptionTimestampsBlock": timestamps_block})
    write_json(packaging_path, packaging)

    if write_description_file:
        description_path = workspace / f"000_{workspace.name}.youtube_description.txt"
        description_path.write_text(packaging["description"] + "\n", encoding="utf-8", newline="\n")

    return packaging


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Resolve YouTube chapter timestamps from segment markers and assemble the upload description."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument(
        "--intro-offset",
        type=float,
        default=DEFAULT_VIDEO_INTRO_OFFSET_SEC,
        help=f"Seconds added to every timestamp for the final video intro (default {DEFAULT_VIDEO_INTRO_OFFSET_SEC}).",
    )
    parser.add_argument(
        "--no-description-file",
        action="store_true",
        help="Do not write 000_chapter_XXX.youtube_description.txt.",
    )
    args = parser.parse_args()

    packaging = prepare_youtube_packaging(
        Path(args.workspace),
        intro_offset_sec=args.intro_offset,
        write_description_file=not args.no_description_file,
    )
    print(f"output={chapter_youtube_path(Path(args.workspace)).as_posix()}", flush=True)
    print(f"markers={len(packaging.get('chapterMarkers') or [])}", flush=True)
    print("\n" + packaging["description"], flush=True)


if __name__ == "__main__":
    main()
