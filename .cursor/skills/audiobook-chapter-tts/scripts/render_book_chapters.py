from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from audiobook_workspace import final_audio_path, workspace_path

SCRIPT_DIR = Path(__file__).resolve().parent
PYTHON = Path(sys.executable)
BOOK = "Pride and Prejudice"
EPUB = "books/Pride  Prejudice (Jane Austen).epub"
REFERENCE = "reference/40-121026/40-121026-0001.flac"

PRIDE_CHARACTER_PROFILES = {
    "Mr. Bennet": "Mr Bennet, dry ironical calm, steady understated, consistent manner",
    "Mrs. Bennet": "Mrs Bennet, anxious sharp fluttering, consistent manner",
    "Elizabeth": "Elizabeth, poised witty calm, consistent manner",
    "Jane": "Jane, warm gentle modest, consistent manner",
    "Mary": "Mary, solemn pedantic calm, consistent manner",
    "Lydia": "Lydia, bold spirited, consistent manner",
    "Kitty": "Kitty, peevish fretful, consistent manner",
    "Charlotte": "Charlotte Lucas, sensible dry calm, consistent manner",
    "Lucas": "young Lucas, boyish eager, consistent manner",
    "Mr. Bingley": "Mr Bingley, warm eager sociable, consistent manner",
    "Mr. Darcy": "Mr Darcy, proud reserved cold, consistent manner",
    "Miss Bingley": "Miss Bingley, polished condescending, consistent manner",
    "Mrs. Hurst": "Mrs Hurst, languid superior, consistent manner",
    "Sir William": "Sir William Lucas, courteous eager, consistent manner",
    "Lady Lucas": "Lady Lucas, pleasant neighbourly, consistent manner",
    "Mr. Collins": "Mr Collins, obsequious pompous, consistent manner",
    "Mr. Wickham": "Mr Wickham, charming smooth, consistent manner",
    "Colonel Fitzwilliam": "Colonel Fitzwilliam, open friendly, consistent manner",
    "Lady Catherine": "Lady Catherine, imperious commanding, consistent manner",
}


def run_script(name: str, *args: str) -> None:
    cmd = [str(PYTHON), str(SCRIPT_DIR / name), *args]
    print(f"\n>>> {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)


def chapter_done(workspace: Path) -> bool:
    return final_audio_path(workspace).is_file()


def prepare_chapter(chapter: int, root: str) -> Path:
    workspace = workspace_path(BOOK, chapter, root)
    run_script(
        "prepare_workspace.py",
        "--book",
        BOOK,
        "--chapter",
        str(chapter),
        "--workspace-root",
        root,
        "--reference",
        REFERENCE,
    )
    run_script(
        "segment_chapter.py",
        "--book",
        BOOK,
        "--chapter",
        str(chapter),
        "--source",
        EPUB,
        "--reference",
        REFERENCE,
        "--workspace-root",
        root,
        "--overwrite",
    )
    apply_manifest_defaults(workspace)
    ref_src = workspace_path(BOOK, 1, root) / "000_reference_clean.wav"
    ref_dst = workspace / "000_reference_clean.wav"
    if ref_src.is_file() and not ref_dst.is_file():
        shutil.copyfile(ref_src, ref_dst)
    elif not ref_dst.is_file():
        run_script(
            "clean_reference_audio.py",
            "--workspace",
            str(workspace).replace("\\", "/"),
            "--reference",
            REFERENCE,
        )
    return workspace


def apply_manifest_defaults(workspace: Path) -> None:
    import json

    from audiobook_workspace import load_json, manifest_path, write_json

    manifest_file = manifest_path(workspace)
    manifest = load_json(manifest_file)
    speakers = {seg["speaker"] for seg in manifest["segments"] if seg.get("kind") == "dialogue"}
    profiles = {name: PRIDE_CHARACTER_PROFILES[name] for name in speakers if name in PRIDE_CHARACTER_PROFILES}
    if profiles:
        manifest["characterProfiles"] = profiles
    manifest["cfgValue"] = 2.35
    for seg in manifest["segments"]:
        if seg.get("kind") == "dialogue" and seg.get("deliveryCue") == "restrained dialogue delivery":
            seg["deliveryCue"] = "natural dialogue delivery"
    write_json(manifest_file, manifest)


def render_chapter(chapter: int, root: str) -> None:
    workspace = workspace_path(BOOK, chapter, root)
    run_script(
        "render_chapter.py",
        "--workspace",
        str(workspace).replace("\\", "/"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and render a range of audiobook chapters.")
    parser.add_argument("--start", type=int, default=6)
    parser.add_argument("--end", type=int, default=61)
    parser.add_argument("--workspace-root", default="workspace")
    parser.add_argument("--force", action="store_true", help="Re-render even if chapter raw wav exists.")
    args = parser.parse_args()

    for chapter in range(args.start, args.end + 1):
        workspace = workspace_path(BOOK, chapter, args.workspace_root)
        if not args.force and chapter_done(workspace):
            print(f"skip chapter {chapter:03d} (already rendered)", flush=True)
            continue
        print(f"\n========== chapter {chapter:03d} ==========", flush=True)
        prepare_chapter(chapter, args.workspace_root)
        render_chapter(chapter, args.workspace_root)
        print(f"finished chapter {chapter:03d}: {final_audio_path(workspace)}", flush=True)

    print("\nAll requested chapters complete.", flush=True)


if __name__ == "__main__":
    main()
