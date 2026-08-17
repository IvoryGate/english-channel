from __future__ import annotations

import argparse
import subprocess
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

    filter_parts: list[str] = []
    concat_inputs: list[str] = []
    for index, clip in enumerate(clips):
        filter_parts.append(f"[{index}:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=mono[a{index}]")
        concat_inputs.append(f"[a{index}]")
        if index < len(clips) - 1 and gap_sec > 0:
            silence_label = f"s{index}"
            filter_parts.append(
                f"anullsrc=r=44100:cl=mono,atrim=0:{gap_sec},asetpts=N/SR/TB[{silence_label}]"
            )
            concat_inputs.append(f"[{silence_label}]")

    n = len(concat_inputs)
    filter_complex = ";".join(filter_parts) + f";{''.join(concat_inputs)}concat=n={n}:v=0:a=1[out]"
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for clip in clips:
        command.extend(["-i", str(clip)])
    command.extend(["-filter_complex", filter_complex, "-map", "[out]", str(output_wav)])
    subprocess.run(command, check=True)
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
