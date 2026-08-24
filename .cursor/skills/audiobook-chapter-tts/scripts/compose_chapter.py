from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

from audiobook_workspace import (
    DEFAULT_CFG_VALUE,
    DEFAULT_INTER_SEGMENT_SILENCE_SEC,
    DEFAULT_INFERENCE_TIMESTEPS,
    compose_control,
    ensure_segment_defaults,
    final_audio_path,
    load_json,
    manifest_path,
    read_mono,
    run_manifest_path,
    write_json,
)


def compose(workspace: Path, inter_segment_silence_sec: float = DEFAULT_INTER_SEGMENT_SILENCE_SEC) -> dict[str, object]:
    manifest_file = manifest_path(workspace)
    manifest = ensure_segment_defaults(load_json(manifest_file))
    global_control = str(manifest["globalControl"])
    pace_cue = str(manifest["paceCue"]) if "paceCue" in manifest else None
    character_profiles = dict(manifest.get("characterProfiles") or {})
    waves = []
    outputs = []
    sample_rate: int | None = None

    for segment in manifest["segments"]:
        segment_path = workspace / segment["filename"]
        if not segment_path.is_file():
            raise FileNotFoundError(f"Missing segment audio: {segment_path}")
        wav, sr = read_mono(segment_path)
        if sample_rate is None:
            sample_rate = sr
        if sr != sample_rate:
            raise ValueError(f"Sample-rate mismatch: {segment_path} has {sr}, expected {sample_rate}")
        request = compose_control(
            segment,
            global_control,
            pace_cue=pace_cue,
            character_profiles=character_profiles,
        )
        outputs.append(
            {
                "id": segment["id"],
                "order": segment["order"],
                "filename": segment["filename"],
                "speaker": segment["speaker"],
                "deliveryCue": segment["deliveryCue"],
                "durationSec": round(float(len(wav) / sample_rate), 3),
                "wordCount": segment["wordCount"],
                "generationPolicy": request["policy"],
                "maxLen": request["maxLen"],
            }
        )
        waves.append(wav)
        waves.append(np.zeros(int(sample_rate * inter_segment_silence_sec), dtype=np.float32))

    if sample_rate is None:
        raise ValueError("Manifest has no segments to compose")

    audio = np.concatenate(waves[:-1]) if waves else np.array([], dtype=np.float32)
    output = final_audio_path(workspace)
    sf.write(output, audio, sample_rate)
    run = {
        "workspace": str(workspace).replace("\\", "/"),
        "manifest": str(manifest_file).replace("\\", "/"),
        "output": str(output).replace("\\", "/"),
        "sampleRate": sample_rate,
        "durationSec": round(float(len(audio) / sample_rate), 3),
        "modelId": manifest.get("modelId", "pretrained_models/VoxCPM2"),
        "referenceAudio": manifest.get("activeReferenceAudio"),
        "cfgValue": manifest.get("cfgValue", DEFAULT_CFG_VALUE),
        "inferenceTimesteps": manifest.get("inferenceTimesteps", DEFAULT_INFERENCE_TIMESTEPS),
        "interSegmentSilenceSec": inter_segment_silence_sec,
        "segments": outputs,
    }
    write_json(run_manifest_path(workspace), run)
    return run


def main() -> None:
    parser = argparse.ArgumentParser(description="Compose chapter audio from existing segment WAVs.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--silence", type=float, default=DEFAULT_INTER_SEGMENT_SILENCE_SEC)
    args = parser.parse_args()
    run = compose(Path(args.workspace), args.silence)
    print(f"output={run['output']}")
    print(f"duration_sec={run['durationSec']}")


if __name__ == "__main__":
    main()
