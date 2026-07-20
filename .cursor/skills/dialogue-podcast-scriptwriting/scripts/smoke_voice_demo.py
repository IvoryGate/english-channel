from __future__ import annotations

import argparse
import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / ".cursor" / "skills" / "audiobook-chapter-tts" / "scripts"))
from render_chapter import load_voxcpm  # noqa: E402


DEMO_LINES: dict[str, list[str]] = {
    "Ethan": [
        "Welcome back. Today we are talking about calm, real calm.",
        "It really does mean a lot when you listen and share your thoughts with us.",
    ],
    "Nora": [
        "There is something beautiful about people from different places meeting through English.",
        "Stay with us, because we will slow down a few useful phrases at the end.",
    ],
    "Sam": [
        "Can I ask you something? Do you ever want to practice English but have no one to talk to?",
        "That feeling is more common than people admit.",
    ],
    "Riley": [
        "You do not need a speaking partner to practice every day.",
        "Today I want to show you a simple fifteen minute plan that actually works.",
    ],
    "Leo": [
        "If you understand everything you listen to, your practice might be too comfortable.",
        "One useful sentence is enough to start.",
    ],
    "Mia": [
        "I love easy English walks, but my speaking still panics in meetings.",
        "Give me the tiny version, not the spreadsheet week.",
    ],
}


def load_profiles() -> dict[str, Any]:
    path = REPO_ROOT / "workspace" / "dialogue_podcast_research" / "voices" / "voice_profiles.json"
    return json.loads(path.read_text(encoding="utf-8"))["profiles"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-render short lines for dialogue host voice profiles.")
    parser.add_argument("--hosts", default="Ethan,Nora,Riley,Sam,Leo,Mia")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--output-dir", default="workspace/shows/voice_smoke")
    args = parser.parse_args()

    hosts = [part.strip() for part in args.hosts.split(",") if part.strip()]
    profiles = load_profiles()
    output_dir = REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading VoxCPM2...")
    model = load_voxcpm("pretrained_models/VoxCPM2", args.device)
    sample_rate = int(model.tts_model.sample_rate)
    report: list[dict[str, Any]] = []

    for host in hosts:
        profile = profiles.get(host)
        if not profile:
            raise KeyError(f"Unknown host profile: {host}")
        reference = profile["referenceAudioClean"]
        for index, line in enumerate(DEMO_LINES.get(host, [f"This is a smoke test for {host}."]), start=1):
            output = output_dir / f"{host.lower()}_{index:02d}.wav"
            print(f"Rendering {host} line {index} -> {output.name}")
            reference_text = str(profile.get("referenceText") or "").strip() or None
            kwargs = {
                "text": line,
                "reference_wav_path": reference,
                "cfg_value": float(profile.get("cfgValue", 2.35)),
                "inference_timesteps": int(profile.get("inferenceTimesteps", 10)),
                "normalize": False,
                "denoise": False,
            }
            if reference_text:
                kwargs["prompt_wav_path"] = reference
                kwargs["prompt_text"] = reference_text
            wav = model.generate(**kwargs).astype(np.float32, copy=False)
            sf.write(output, wav, sample_rate)
            report.append(
                {
                    "host": host,
                    "line": line,
                    "output": str(output.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "durationSec": round(float(len(wav) / sample_rate), 3),
                    "referenceAudioClean": reference,
                }
            )
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

    report_path = output_dir / "smoke_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    raise SystemExit(main())
