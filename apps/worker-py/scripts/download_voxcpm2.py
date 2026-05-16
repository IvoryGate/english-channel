from __future__ import annotations

import argparse
import os

from huggingface_hub import snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser(description="Download VoxCPM2 weights for local inference.")
    parser.add_argument("--model-id", default=os.getenv("VOXCPM_MODEL_ID", "openbmb/VoxCPM2"))
    parser.add_argument("--local-dir", default=os.getenv("VOXCPM_LOCAL_DIR", "pretrained_models/VoxCPM2"))
    args = parser.parse_args()

    path = snapshot_download(
        repo_id=args.model_id,
        local_dir=args.local_dir,
        local_dir_use_symlinks=False,
    )
    print(f"VoxCPM2 downloaded to: {path}")


if __name__ == "__main__":
    main()
