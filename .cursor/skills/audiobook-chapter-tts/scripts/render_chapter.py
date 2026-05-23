from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from voxcpm import VoxCPM

from audiobook_workspace import (
    DEFAULT_CFG_VALUE,
    DEFAULT_INFERENCE_TIMESTEPS,
    DEFAULT_MODEL_ID,
    clean_reference_path,
    compose_control,
    ensure_segment_defaults,
    load_json,
    manifest_path,
    normalize_segment_peak,
    parse_segment_ids,
    write_json,
)
from compose_chapter import compose


def active_reference(manifest: dict[str, Any], workspace: Path, no_clean_reference: bool) -> str:
    original = manifest.get("referenceAudioOriginal")
    clean = manifest.get("referenceAudioClean") or str(clean_reference_path(workspace)).replace("\\", "/")
    if no_clean_reference:
        if not original:
            raise ValueError("--no-clean-reference was set but referenceAudioOriginal is empty")
        return str(original)
    if Path(clean).is_file():
        return str(clean)
    if original:
        return str(original)
    raise ValueError("No usable reference audio. Run clean_reference_audio.py or set referenceAudioOriginal.")


def render_segments(
    workspace: Path,
    selected_ids: set[str],
    no_clean_reference: bool,
    compose_after: bool,
) -> dict[str, object]:
    manifest_file = manifest_path(workspace)
    manifest = ensure_segment_defaults(load_json(manifest_file))
    segments = manifest["segments"]
    global_control = str(manifest["globalControl"])
    pace_cue = str(manifest["paceCue"]) if "paceCue" in manifest else None
    character_profiles = dict(manifest.get("characterProfiles") or {})
    reference_audio = active_reference(manifest, workspace, no_clean_reference)
    manifest["activeReferenceAudio"] = reference_audio
    write_json(manifest_file, manifest)

    if not selected_ids:
        selected_ids = {str(segment["id"]) for segment in segments}
    known_ids = {str(segment["id"]) for segment in segments}
    unknown = selected_ids - known_ids
    if unknown:
        raise ValueError(f"Unknown segment ids: {sorted(unknown)}")

    print("Loading VoxCPM2...")
    model = VoxCPM.from_pretrained(
        str(manifest.get("modelId", DEFAULT_MODEL_ID)),
        load_denoiser=False,
        optimize=False,
        device=str(manifest.get("device", "cuda")),
        local_files_only=True,
    )
    sample_rate = model.tts_model.sample_rate
    rendered = []

    for segment in segments:
        if str(segment["id"]) not in selected_ids:
            continue
        request = compose_control(
            segment,
            global_control,
            pace_cue=pace_cue,
            character_profiles=character_profiles,
        )
        print(
            f"Rendering {segment['id']} -> {segment['filename']}: {segment['speaker']} | "
            f"{request['policy']} max_len={request['maxLen']}"
        )
        kwargs = {
            "text": request["ttsText"],
            "reference_wav_path": reference_audio,
            "cfg_value": float(manifest.get("cfgValue", DEFAULT_CFG_VALUE)),
            "inference_timesteps": int(manifest.get("inferenceTimesteps", DEFAULT_INFERENCE_TIMESTEPS)),
            "normalize": False,
            "denoise": False,
        }
        if request["maxLen"] is not None:
            kwargs["max_len"] = request["maxLen"]
        wav = model.generate(**kwargs).astype(np.float32, copy=False)
        wav = normalize_segment_peak(wav)
        output = workspace / str(segment["filename"])
        sf.write(output, wav, sample_rate)
        rendered.append(
            {
                "id": segment["id"],
                "filename": segment["filename"],
                "durationSec": round(float(len(wav) / sample_rate), 3),
                "policy": request["policy"],
                "maxLen": request["maxLen"],
            }
        )

    run: dict[str, object] | None = None
    if compose_after:
        run = compose(workspace)
    return {"rendered": rendered, "composed": run}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render all or selected audiobook chapter segments.")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--segments", help="Comma-separated ids, e.g. 003,009,010")
    parser.add_argument("--no-compose", action="store_true")
    parser.add_argument("--no-clean-reference", action="store_true")
    args = parser.parse_args()
    result = render_segments(
        Path(args.workspace),
        parse_segment_ids(args.segments),
        no_clean_reference=args.no_clean_reference,
        compose_after=not args.no_compose,
    )
    print(f"rendered={len(result['rendered'])}")
    if result["composed"]:
        print(f"output={result['composed']['output']}")


if __name__ == "__main__":
    main()
