from __future__ import annotations

import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from .schema import ProviderConfig
from .trace import atomic_write_json


class ProviderProcessError(RuntimeError):
    pass


def _runtime_env(repo_root: Path) -> dict[str, str]:
    runtime = repo_root / "workspace" / "runtime" / "tts-audition"
    temp = runtime / "tmp" / "provider"
    temp.mkdir(parents=True, exist_ok=True)
    cache = runtime / "cache"
    return {
        **os.environ,
        "TEMP": str(temp),
        "TMP": str(temp),
        "TMPDIR": str(temp),
        "HF_HOME": str(cache / "huggingface"),
        "HF_HUB_CACHE": str(cache / "huggingface" / "hub"),
        "HF_XET_CACHE": str(cache / "huggingface" / "xet"),
        "HF_HUB_DISABLE_XET": "1",
        "TORCH_HOME": str(cache / "torch"),
        "XDG_CACHE_HOME": str(cache),
        "TRITON_CACHE_DIR": str(cache / "triton"),
        "TORCHINDUCTOR_CACHE_DIR": str(cache / "torchinductor"),
        "NUMBA_CACHE_DIR": str(cache / "numba"),
        "MPLCONFIGDIR": str(cache / "matplotlib"),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONNOUSERSITE": "1",
        "KMP_DUPLICATE_LIB_OK": "TRUE",
    }


def run_provider_batch(
    repo_root: Path,
    provider: ProviderConfig,
    turns: list[dict[str, Any]],
    *,
    label: str,
) -> list[dict[str, Any]]:
    if not turns:
        return []
    if not provider.interpreter.is_file():
        raise ProviderProcessError(f"Provider interpreter not found: {provider.interpreter}")
    if provider.provider_id != "kokoro" and not provider.local_model_path.exists():
        raise ProviderProcessError(f"Provider model path not found: {provider.local_model_path}")
    runtime = repo_root / "workspace" / "runtime" / "tmp" / "tts-provider"
    runtime.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    request_path = runtime / f"{token}.request.json"
    response_path = runtime / f"{token}.response.json"
    request = {
        "schema": "elr-tts-provider-batch-v1",
        "repoRoot": str(repo_root.resolve()),
        "label": label,
        "provider": provider.to_trace(repo_root),
        "turns": turns,
    }
    atomic_write_json(request_path, request)
    worker = repo_root / "apps" / "worker-py" / "worker" / "tts" / "isolated_worker.py"
    command = [str(provider.interpreter), "-u", str(worker), "--request", str(request_path), "--response", str(response_path)]
    try:
        result = subprocess.run(
            command,
            cwd=str(repo_root),
            env=_runtime_env(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0 or not response_path.is_file():
            tail = (result.stdout or "")[-4000:]
            raise ProviderProcessError(
                f"{provider.provider_id} batch failed with exit {result.returncode}: {tail}"
            )
        response = json.loads(response_path.read_text(encoding="utf-8"))
        if response.get("status") != "ok":
            raise ProviderProcessError(str(response.get("error") or "Provider batch failed"))
        rows = response.get("turns")
        if not isinstance(rows, list) or len(rows) != len(turns):
            raise ProviderProcessError("Provider returned an incomplete batch response")
        return rows
    finally:
        request_path.unlink(missing_ok=True)
        response_path.unlink(missing_ok=True)
