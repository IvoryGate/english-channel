from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from episode_timeline import validated_gaps


def build_concat_audio(
    clips: list[Path],
    output_wav: Path,
    *,
    gap_sec: float = 0.35,
    gaps_sec: list[float] | None = None,
    sample_rate: int = 44100,
) -> Path:
    if len(clips) < 1:
        raise ValueError("At least one clip is required")
    gaps = validated_gaps(len(clips), gap_sec, gaps_sec)
    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(f"Missing clip: {clip}")

    output_wav.parent.mkdir(parents=True, exist_ok=True)
    # Keep clip paths in a concat manifest instead of placing every input on
    # the command line. Large Series C episodes otherwise exceed Windows'
    # CreateProcess command-length limit before ffmpeg can start.
    with tempfile.TemporaryDirectory(prefix="elr_reference_concat_") as tmp:
        tmp_dir = Path(tmp)
        list_file = tmp_dir / "concat.txt"
        silences: dict[float, Path] = {}
        lines: list[str] = []

        if any(gap > 0 for gap in gaps):
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "a:0",
                    "-show_entries",
                    "stream=codec_name,sample_rate,channels",
                    "-of",
                    "json",
                    str(clips[0]),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            stream = json.loads(probe.stdout)["streams"][0]
            codec = str(stream["codec_name"])
            input_sample_rate = int(stream["sample_rate"])
            channels = int(stream["channels"])
            if codec not in {"pcm_f32le", "pcm_s16le", "pcm_s24le", "pcm_s32le"}:
                raise ValueError(f"Unsupported concat PCM codec: {codec}")
            for gap in sorted(set(gap for gap in gaps if gap > 0)):
                silence = tmp_dir / f"gap_{len(silences)}.wav"
                silences[gap] = silence
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
                        f"anullsrc=r={input_sample_rate}:cl={'mono' if channels == 1 else 'stereo'}",
                        "-t",
                        str(gap),
                        "-c:a",
                        codec,
                        str(silence),
                    ],
                    check=True,
                )

        for index, clip in enumerate(clips):
            lines.append(f"file '{clip.resolve().as_posix()}'")
            if index < len(gaps) and gaps[index] > 0:
                lines.append(f"file '{silences[gaps[index]].resolve().as_posix()}'")
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
                str(sample_rate),
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
