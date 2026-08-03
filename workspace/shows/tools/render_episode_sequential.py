"""Sequential one-turn VoxCPM render for dialogue episodes (hardware-friendly)."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_reference_concat_audio import build_concat_audio  # noqa: E402
from render_chapter import load_voxcpm  # noqa: E402
from render_episode import control_text, normalize_quiet_segment  # noqa: E402

SHOW_CONFIG_PATH = Path(__file__).resolve().parent / "show_config.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--start-from", default="", help="Turn id to resume from, e.g. p005")
    parser.add_argument("--only", default="", help="Single turn id, e.g. p001")
    parser.add_argument("--pause-sec", type=float, default=1.5)
    parser.add_argument("--concat", action="store_true")
    args = parser.parse_args()

    # Match audiobook: no expandable_segments; no KV max_length hacks.
    if "expandable_segments" in os.environ.get("PYTORCH_CUDA_ALLOC_CONF", ""):
        os.environ.pop("PYTORCH_CUDA_ALLOC_CONF", None)
    manifest_path = Path(args.manifest)
    workspace = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    show_id = str(manifest["showId"])
    settings = manifest["renderSettings"]
    turns = list(manifest["turns"])

    if args.only:
        turns = [t for t in turns if t["id"] == args.only]
    elif args.start_from:
        started = False
        filtered = []
        for t in turns:
            if t["id"] == args.start_from:
                started = True
            if started:
                filtered.append(t)
        turns = filtered

    print(f"loading VoxCPM on {args.device} ...", flush=True)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()
    model = load_voxcpm(str(settings.get("modelId", "pretrained_models/VoxCPM2")), args.device)
    sample_rate = int(model.tts_model.sample_rate)
    print(f"loaded sample_rate={sample_rate} turns={len(turns)}", flush=True)

    for turn in turns:
        speaker = str(turn["speaker"])
        host = manifest["hosts"][speaker]
        output = workspace / str(turn["filename"])
        print(f"render {turn['id']} {speaker} -> {output.name}", flush=True)
        reference_audio = str(REPO_ROOT / host["referenceAudioClean"])
        # Same generate() kwargs as audiobook render_chapter.py.
        kwargs = {
            "text": control_text(show_id, speaker, str(turn["text"]), str(turn.get("deliveryCue", ""))),
            "reference_wav_path": reference_audio,
            "cfg_value": float(settings.get("cfgValue", 2.35)),
            "inference_timesteps": int(settings.get("inferenceTimesteps", 10)),
            "normalize": False,
            "denoise": False,
        }
        words = int(turn.get("wordCount") or len(str(turn["text"]).split()))
        # Prefer audiobook short-segment caps; ignore inflated episode maxLen (>128).
        max_len = turn.get("maxLen")
        if max_len is not None and int(max_len) <= 128:
            kwargs["max_len"] = int(max_len)
        elif words <= 4:
            kwargs["max_len"] = 56
        elif words <= 12:
            kwargs["max_len"] = 128
        wav = model.generate(**kwargs).astype(np.float32, copy=False)
        wav = normalize_quiet_segment(wav)
        sf.write(output, wav, sample_rate)
        peak = float(np.max(np.abs(wav))) if len(wav) else 0.0
        print(f"  ok duration={len(wav)/sample_rate:.2f}s peak={peak:.3f}", flush=True)
        time.sleep(args.pause_sec)

    if args.concat:
        clips = [workspace / str(t["filename"]) for t in manifest["turns"]]
        raw = workspace / f"000_{manifest['episodeId']}.raw.wav"
        gap = float(settings.get("interTurnSilenceSec", 0.3))
        build_concat_audio(clips, raw, gap_sec=gap)
        print(f"raw={raw.as_posix()}", flush=True)
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
