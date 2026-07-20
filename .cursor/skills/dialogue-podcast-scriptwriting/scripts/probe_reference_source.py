from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def scan_source(source_wav: Path, start: float, end: float, step: float, window: float) -> None:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("faster-whisper required for probe") from exc

    model = WhisperModel("base", device="cpu", compute_type="int8")
    tmpdir = source_wav.parent / "_probe"
    tmpdir.mkdir(exist_ok=True)

    pos = start
    while pos < end:
        clip_end = min(end, pos + window)
        out = tmpdir / f"scan_{int(pos)}.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(pos),
                "-i",
                str(source_wav),
                "-t",
                str(clip_end - pos),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(out),
            ],
            check=True,
        )
        segments, _ = model.transcribe(str(out), language="en")
        text = " ".join(part.text.strip() for part in segments)
        if text.strip():
            print(f"[{pos:6.1f}-{clip_end:6.1f}] {text}")
        pos += step


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a source wav for candidate reference clip windows.")
    parser.add_argument("--source", required=True, help="Path to source .wav")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float, default=180.0)
    parser.add_argument("--step", type=float, default=8.0)
    parser.add_argument("--window", type=float, default=10.0)
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_file():
        raise SystemExit(f"Missing source: {source}")

    scan_source(source, args.start, args.end, args.step, args.window)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
