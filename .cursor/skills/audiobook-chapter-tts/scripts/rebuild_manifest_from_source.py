from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audiobook_workspace import ensure_segment_defaults, manifest_path, source_text_path, write_json
from segment_chapter import draft_segments


def normalize_text(text: str) -> str:
    normalized = (
        text.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    return re.sub(r"\s+", " ", normalized.strip().lower())


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild segment manifest from chapter source text.")
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    manifest_file = manifest_path(workspace)
    source_file = source_text_path(workspace)
    old = json.loads(manifest_file.read_text(encoding="utf-8"))
    cue_map = {normalize_text(segment["text"]): segment["deliveryCue"] for segment in old["segments"]}
    segments = draft_segments(source_file.read_text(encoding="utf-8"))
    for segment in segments:
        segment["deliveryCue"] = cue_map.get(normalize_text(segment["text"]), segment["deliveryCue"])

    manifest = {key: value for key, value in old.items() if key != "segments"}
    manifest["segments"] = segments
    ensure_segment_defaults(manifest)
    write_json(manifest_file, manifest)
    print(f"manifest={manifest_file}")
    print(f"segments={len(segments)}")


if __name__ == "__main__":
    main()
