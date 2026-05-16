from __future__ import annotations

import importlib.util
import json
import platform
import shutil
import subprocess
import sys


def main() -> None:
    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "nvidiaSmi": _nvidia_smi(),
        "packages": {
            "torch": _package_status("torch"),
            "voxcpm": _package_status("voxcpm"),
            "soundfile": _package_status("soundfile"),
        },
    }

    try:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "cudaAvailable": torch.cuda.is_available(),
            "cudaVersion": torch.version.cuda,
            "deviceCount": torch.cuda.device_count(),
            "deviceName": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except Exception as exc:  # pragma: no cover - diagnostic script
        report["torch"] = {"error": str(exc)}

    print(json.dumps(report, indent=2))


def _package_status(package: str) -> str:
    return "installed" if importlib.util.find_spec(package) else "missing"


def _nvidia_smi() -> str:
    if not shutil.which("nvidia-smi"):
        return "missing"
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"],
            text=True,
        )
        return output.strip()
    except Exception as exc:  # pragma: no cover - diagnostic script
        return f"error: {exc}"


if __name__ == "__main__":
    main()
