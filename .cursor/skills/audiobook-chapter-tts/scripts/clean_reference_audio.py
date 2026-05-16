from __future__ import annotations

import argparse
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy import signal

from audiobook_workspace import clean_reference_path, load_json, manifest_path, write_json


def rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(values))) + 1e-12)


def spectral_subtract(y: np.ndarray, sr: int) -> np.ndarray:
    n_fft = 1024
    hop_length = 256
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    magnitude, phase = np.abs(stft), np.exp(1j * np.angle(stft))
    frame_energy = np.mean(np.square(magnitude), axis=0)
    quiet_count = max(3, int(len(frame_energy) * 0.12))
    quiet_indices = np.argsort(frame_energy)[:quiet_count]
    noise_profile = np.median(magnitude[:, quiet_indices], axis=1, keepdims=True)
    cleaned_magnitude = np.maximum(magnitude - noise_profile * 0.75, magnitude * 0.18)
    return librosa.istft(cleaned_magnitude * phase, hop_length=hop_length, length=len(y)).astype(np.float32)


def clean_reference(input_path: Path, output_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    y, sr = sf.read(input_path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    original = y.astype(np.float32, copy=False)
    y = original - float(np.mean(original))
    sos = signal.butter(4, 80, btype="highpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos, y).astype(np.float32)
    y = spectral_subtract(y, sr)
    y, _ = librosa.effects.trim(y, top_db=32)
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    if peak > 0:
        y = (y / peak * 0.88).astype(np.float32)
    sf.write(output_path, y, sr, subtype="PCM_16")
    return {
        "input": str(input_path).replace("\\", "/"),
        "output": str(output_path).replace("\\", "/"),
        "sampleRate": sr,
        "inputDurationSec": round(float(len(original) / sr), 3),
        "outputDurationSec": round(float(len(y) / sr), 3),
        "inputRms": round(rms(original), 6),
        "outputRms": round(rms(y), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean reference audio for VoxCPM2 cloning.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--reference", help="Reference audio. Defaults to manifest referenceAudioOriginal.")
    args = parser.parse_args()

    workspace = Path(args.workspace)
    manifest_file = manifest_path(workspace)
    manifest = load_json(manifest_file)
    reference = args.reference or manifest.get("referenceAudioOriginal")
    if not reference:
        raise ValueError("No reference audio provided and manifest referenceAudioOriginal is empty.")

    output = clean_reference_path(workspace)
    report = clean_reference(Path(reference), output)
    manifest["referenceAudioOriginal"] = str(reference).replace("\\", "/")
    manifest["referenceAudioClean"] = str(output).replace("\\", "/")
    manifest["cleanReference"] = True
    write_json(manifest_file, manifest)
    report_path = workspace / "000_reference_clean.report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
