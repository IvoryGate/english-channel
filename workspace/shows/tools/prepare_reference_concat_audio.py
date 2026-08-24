from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


def build_concat_audio(
    clips: list[Path],
    output_wav: Path,
    *,
    gap_sec: float = 0.35,
) -> Path:
    if len(clips) < 1:
        raise ValueError("At least one clip is required")
    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(f"Missing clip: {clip}")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1 and gap_sec <= 0:
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(clips[0]), str(output_wav)], check=True)
        return output_wav

    # Keep clip paths in a concat manifest instead of placing every input on
    # the command line. Large Series C episodes otherwise exceed Windows'
    # CreateProcess command-length limit before ffmpeg can start.
    with tempfile.TemporaryDirectory(prefix="elr_reference_concat_") as tmp:
        tmp_dir = Path(tmp)
        list_file = tmp_dir / "concat.txt"
        silence = tmp_dir / "gap.wav"
        lines: list[str] = []

        if gap_sec > 0 and len(clips) > 1:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=48000:cl=mono",
                    "-t",
                    str(gap_sec),
                    "-c:a",
                    "pcm_s16le",
                    str(silence),
                ],
                check=True,
            )

        for index, clip in enumerate(clips):
            lines.append(f"file '{clip.resolve().as_posix()}'")
            if gap_sec > 0 and index < len(clips) - 1:
                lines.append(f"file '{silence.resolve().as_posix()}'")
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-ar",
                "44100",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                str(output_wav),
            ],
            check=True,
        )
    return output_wav


def main() -> int:
    parser = argparse.ArgumentParser(description="Concatenate reference clips into a pilot raw.wav.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--clips", nargs="+", required=True)
    parser.add_argument("--gap-sec", type=float, default=0.35)
    args = parser.parse_args()
    result = build_concat_audio([Path(path) for path in args.clips], Path(args.output), gap_sec=args.gap_sec)
    print(result.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
