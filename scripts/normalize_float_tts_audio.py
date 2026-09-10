from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_float_wav_atomic(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".wav", dir=path.parent)
    os.close(fd)
    try:
        sf.write(temp_name, audio, sample_rate, subtype="FLOAT")
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def normalize_directory(segments_dir: Path, target: float) -> int:
    changed = 0
    for wav_path in sorted(segments_dir.glob("*.wav")):
        audio, sample_rate = sf.read(wav_path, dtype="float32", always_2d=False)
        peak = float(np.max(np.abs(audio)))
        if peak <= target:
            continue
        normalized = np.asarray(audio * (target / peak), dtype=np.float32)
        write_float_wav_atomic(wav_path, normalized, int(sample_rate))
        trace_path = wav_path.with_name(f"{wav_path.stem}.trace.json")
        if not trace_path.is_file():
            raise FileNotFoundError(f"Missing trace for normalized audio: {trace_path}")
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        trace["peak"] = round(float(np.max(np.abs(normalized))), 6)
        trace["outputSha256"] = sha256_file(wav_path)
        trace["postProcessing"] = {"peakNormalizedTo": target, "sampleType": "float32"}
        trace_path.write_text(
            json.dumps(trace, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Peak-normalize traced float TTS segments in place.")
    parser.add_argument("--segments-dir", required=True)
    parser.add_argument("--target", type=float, default=0.89)
    args = parser.parse_args()
    segments_dir = Path(args.segments_dir).resolve()
    if not segments_dir.is_dir():
        raise FileNotFoundError(segments_dir)
    if not 0.0 < args.target < 1.0:
        raise ValueError("--target must be between zero and one")
    changed = normalize_directory(segments_dir, args.target)
    print(f"normalized={changed} target={args.target:.2f} directory={segments_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
