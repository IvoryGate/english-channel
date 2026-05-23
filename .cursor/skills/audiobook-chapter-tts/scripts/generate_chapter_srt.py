from __future__ import annotations

import argparse
from pathlib import Path

from audiobook_workspace import (
    chapter_srt_path,
    chapter_timeline,
    ensure_segment_defaults,
    format_srt_timestamp,
    inter_segment_silence_sec,
    load_json,
    manifest_path,
    write_json,
)


def render_srt(entries: list[dict[str, object]]) -> str:
    blocks: list[str] = []
    for index, entry in enumerate(entries, start=1):
        start = format_srt_timestamp(float(entry["startSec"]))
        end = format_srt_timestamp(float(entry["endSec"]))
        text = str(entry["text"]).strip()
        blocks.append(f"{index}\n{start} --> {end}\n{text}\n")
    return "\n".join(blocks)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate chapter SRT subtitles from finalized segment WAV timings."
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument(
        "--silence",
        type=float,
        help="Inter-segment silence seconds; default from run manifest or 0.34",
    )
    parser.add_argument(
        "--timeline-json",
        action="store_true",
        help="Also write 000_chapter_XXX.timeline.json beside the SRT",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace)
    manifest = ensure_segment_defaults(load_json(manifest_path(workspace)))
    silence = float(args.silence) if args.silence is not None else inter_segment_silence_sec(manifest, workspace)
    timeline = chapter_timeline(workspace, manifest, silence_sec=silence)
    srt_path = chapter_srt_path(workspace)
    srt_path.write_text(render_srt(timeline), encoding="utf-8", newline="\n")

    if args.timeline_json:
        chapter = workspace.name
        timeline_path = workspace / f"000_{chapter}.timeline.json"
        write_json(
            timeline_path,
            {
                "workspace": str(workspace).replace("\\", "/"),
                "interSegmentSilenceSec": silence,
                "segments": timeline,
            },
        )
        print(f"timeline={timeline_path.as_posix()}")

    print(f"output={srt_path.as_posix()}")
    print(f"cues={len(timeline)}")


if __name__ == "__main__":
    main()
