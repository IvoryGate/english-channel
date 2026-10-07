from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any


TRACE_SCHEMA = "elr-tts-turn-trace-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_turn_identity(
    *,
    provider: dict[str, Any],
    voice: dict[str, Any],
    text: str,
    seed: int,
) -> dict[str, Any]:
    payload = {
        "providerId": provider["providerId"],
        "modelId": provider["modelId"],
        "modelRevision": provider["modelRevision"],
        "localModelPath": provider["localModelPath"],
        "outputFormat": provider["outputFormat"],
        "voice": voice,
        "normalizedText": normalized_text(text),
        "seed": int(seed),
        "providerSettings": provider["providerSettings"],
    }
    return {"payload": payload, "sha256": canonical_hash(payload)}


def turn_trace_path(output: Path) -> Path:
    return output.with_suffix(".trace.json")


def trace_is_reusable(output: Path, expected_identity_sha256: str) -> bool:
    trace_path = turn_trace_path(output)
    if not output.is_file() or not trace_path.is_file():
        return False
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        return (
            trace.get("schema") == TRACE_SCHEMA
            and trace.get("identitySha256") == expected_identity_sha256
            and trace.get("outputSha256") == sha256_file(output)
        )
    except (OSError, ValueError, TypeError):
        return False


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".json", dir=path.parent)
    os.close(fd)
    try:
        Path(temp_name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
