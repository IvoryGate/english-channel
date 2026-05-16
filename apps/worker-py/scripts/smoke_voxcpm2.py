from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker.runner import TtsRequest, VoxRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a short local VoxCPM2 sample.")
    parser.add_argument(
        "--text",
        default="Chapter one. The rain had not stopped for three days, and London sounded hollow in the dark.",
    )
    parser.add_argument("--model-id", default=os.getenv("VOXCPM_MODEL_ID", "openbmb/VoxCPM2"))
    parser.add_argument("--device", default=os.getenv("VOXCPM_DEVICE", "auto"))
    parser.add_argument("--output-dir", default=os.getenv("ARTIFACT_DIR", "artifacts"))
    parser.add_argument("--no-optimize", action="store_true")
    args = parser.parse_args()

    runner = VoxRunner(
        model_id=args.model_id,
        output_dir=args.output_dir,
        device=args.device,
        optimize=not args.no_optimize,
    )
    trace = runner.generate_chapter(
        TtsRequest(
            job_id="smoke-voxcpm2",
            chapter_id="smoke",
            text=args.text,
            voice_profile="default-english-narrator",
        )
    )
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
