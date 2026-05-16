from __future__ import annotations

import argparse
from pathlib import Path

from audiobook_workspace import ensure_segment_defaults, load_json, manifest_path, read_mono


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect audiobook chapter segment files.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--warn-sec-per-word", type=float, default=0.7)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    manifest = ensure_segment_defaults(load_json(manifest_path(workspace)))
    print("id\tfile\twords\tduration\tsec_per_word\tstatus")
    for segment in manifest["segments"]:
        path = workspace / segment["filename"]
        if not path.is_file():
            print(f"{segment['id']}\t{segment['filename']}\t{segment['wordCount']}\t-\t-\tMISSING")
            continue
        wav, sr = read_mono(path)
        duration = len(wav) / sr
        sec_per_word = duration / max(1, int(segment["wordCount"]))
        status = "OK"
        if sec_per_word > args.warn_sec_per_word:
            status = "CHECK_LONG"
        print(
            f"{segment['id']}\t{segment['filename']}\t{segment['wordCount']}\t"
            f"{duration:.2f}\t{sec_per_word:.2f}\t{status}"
        )


if __name__ == "__main__":
    main()
