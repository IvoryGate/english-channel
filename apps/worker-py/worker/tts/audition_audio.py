"""CPU-only listening-copy assembly; external audio tools stay on this boundary."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path


def measure(path: Path) -> dict[str, float]:
    result = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-af", "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=True)
    start = result.stderr.rfind("{")
    payload, _ = json.JSONDecoder().raw_decode(result.stderr[start:])
    metrics = {"integratedLufs": float(payload["input_i"]), "truePeakDbtp": float(payload["input_tp"])}
    if not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError("Audition audio must have measurable finite loudness")
    return metrics


def concatenate(paths: list[Path], destination: Path, gap_sec: float) -> None:
    import numpy as np
    import soundfile as sf

    chunks = []
    sample_rate = None
    for path in paths:
        audio, rate = sf.read(path, dtype="float32", always_2d=True)
        if audio.shape[1] != 1 or not audio.size or not np.isfinite(audio).all():
            raise ValueError("Audition requires finite nonempty mono WAVs")
        if sample_rate is not None and rate != sample_rate:
            raise ValueError("Audition turn sample rates differ")
        if chunks:
            chunks.append(np.zeros((round(gap_sec * rate), 1), dtype=np.float32))
        chunks.append(audio)
        sample_rate = rate
    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(destination, np.concatenate(chunks), sample_rate, subtype="FLOAT")


def match_pair(paths: list[Path], destinations: list[Path], *, target: float, peak: float,
               maximum_difference: float) -> list[dict]:
    import soundfile as sf

    before = [measure(path) for path in paths]
    common = min(target, *(row["integratedLufs"] + peak - row["truePeakDbtp"] - 0.05 for row in before))
    reports = []
    for source, destination, initial in zip(paths, destinations, before):
        value, rate = sf.read(source, dtype="float32")
        gain = common - initial["integratedLufs"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        sf.write(destination, value * (10 ** (gain / 20)), rate, subtype="PCM_24")
        after = measure(destination)
        if after["truePeakDbtp"] > peak:
            raise ValueError("Listening copy exceeds true-peak ceiling")
        reports.append({"gainDb": gain, "commonTargetLufs": common, "before": initial, "after": after})
    if abs(reports[0]["after"]["integratedLufs"] - reports[1]["after"]["integratedLufs"]) > maximum_difference:
        raise ValueError("Listening pair is not sufficiently loudness matched")
    return reports
