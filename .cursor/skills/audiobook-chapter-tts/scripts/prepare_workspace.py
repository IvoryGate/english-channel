from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from audiobook_workspace import (
    DEFAULT_GLOBAL_CONTROL,
    chapter_id,
    clean_reference_path,
    manifest_path,
    source_text_path,
    workspace_path,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an audiobook chapter workspace.")
    parser.add_argument("--book", required=True)
    parser.add_argument("--chapter", required=True, type=int)
    parser.add_argument("--workspace-root", default="workspace")
    parser.add_argument("--source", help="Optional text file to copy into the workspace.")
    parser.add_argument("--reference", help="Optional reference audio path to record in the manifest.")
    args = parser.parse_args()

    workspace = workspace_path(args.book, args.chapter, args.workspace_root)
    workspace.mkdir(parents=True, exist_ok=True)

    source_path = source_text_path(workspace)
    if args.source and not source_path.exists():
        shutil.copyfile(args.source, source_path)
    elif not source_path.exists():
        source_path.write_text("", encoding="utf-8", newline="\n")

    manifest_file = manifest_path(workspace)
    if not manifest_file.exists():
        manifest = {
            "bookTitle": args.book,
            "bookSlug": workspace.parent.name,
            "chapterNumber": args.chapter,
            "chapterId": chapter_id(args.chapter),
            "workspace": str(workspace).replace("\\", "/"),
            "sourceTextPath": str(source_path).replace("\\", "/"),
            "referenceAudioOriginal": args.reference,
            "referenceAudioClean": str(clean_reference_path(workspace)).replace("\\", "/"),
            "cleanReference": True,
            "globalControl": DEFAULT_GLOBAL_CONTROL,
            "segments": [],
        }
        write_json(manifest_file, manifest)

    print(f"workspace={workspace}")
    print(f"source={source_path}")
    print(f"manifest={manifest_file}")


if __name__ == "__main__":
    main()
