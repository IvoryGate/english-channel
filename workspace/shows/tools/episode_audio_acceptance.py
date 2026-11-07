"""Measured final-media gates, separate from raw-turn and listening review."""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from episode_artifacts import artifact_paths, load_json, turn_wav_path
from episode_timeline import file_sha256, resolve_episode_timeline

SCHEMA = "elr-final-audio-acceptance-v1"
POLICY = {"integratedLufs": -16.0, "integratedToleranceLu": 1.0, "truePeakDb": -1.5}


def resolve_ffmpeg() -> str:
    binary = shutil.which("ffmpeg")
    if binary:
        return binary
    bundled = Path(__file__).resolve().parents[3] / "node_modules" / "@remotion" / "compositor-win32-x64-msvc" / "ffmpeg.exe"
    if bundled.is_file():
        return str(bundled)
    raise FileNotFoundError("FFmpeg is required for final audio acceptance")


@lru_cache(maxsize=1)
def ffmpeg_version() -> str:
    result = subprocess.run([resolve_ffmpeg(), "-version"], check=True, capture_output=True,
                            text=True, timeout=30)
    return result.stdout.splitlines()[0]


def measure_loudness(path: Path) -> dict[str, float | None]:
    """Decode the delivered first audio stream; measure input, never predicted output."""
    result = subprocess.run(
        [resolve_ffmpeg(), "-hide_banner", "-nostdin", "-i", str(path), "-map", "0:a:0", "-vn",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
        check=True, capture_output=True, text=True, timeout=600,
    )
    matches = list(re.finditer(r'\{[^{}]*"input_i"[^{}]*\}', result.stderr, flags=re.S))
    if not matches:
        raise RuntimeError(f"Final audio measurement missing for {path}")
    payload = json.loads(matches[-1].group(0))
    measurements = {}
    for name, field in (("integratedLufs", "input_i"), ("truePeakDb", "input_tp"),
                        ("lra", "input_lra"), ("threshold", "input_thresh")):
        value = float(payload[field])
        measurements[name] = value if math.isfinite(value) else None
    return measurements


def acceptance_errors(measurements: dict[str, Any]) -> list[str]:
    errors = []
    for key in ("integratedLufs", "truePeakDb", "lra", "threshold"):
        value = measurements.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            errors.append(f"Missing finite measured {key}")
    if errors:
        return errors
    if abs(measurements["integratedLufs"] - POLICY["integratedLufs"]) > POLICY["integratedToleranceLu"]:
        errors.append("Integrated loudness must be -16 LUFS +/- 1 LU")
    if measurements["truePeakDb"] > POLICY["truePeakDb"]:
        errors.append("Measured true peak must be <= -1.5 dBTP")
    return errors


def measure_audio_acceptance(path: Path, *, stage: str, sources: dict[str, str]) -> dict[str, Any]:
    if stage not in {"master", "encoded"}:
        raise ValueError("Unknown final audio stage")
    before = file_sha256(path)
    measurements = measure_loudness(path)
    if before != file_sha256(path):
        raise ValueError("Audio changed during loudness measurement")
    errors = acceptance_errors(measurements)
    return {
        "schema": SCHEMA, "stage": stage,
        "measuredAt": datetime.now(timezone.utc).isoformat(),
        "method": "ffmpeg-loudnorm-input", "toolVersion": ffmpeg_version(), "audioStream": "0:a:0",
        "artifact": {"sha256": before, "sizeBytes": path.stat().st_size},
        "sources": sources, "policy": dict(POLICY), "measurements": measurements,
        "status": "failed" if errors else "passed", "errors": errors,
    }


def validate_audio_acceptance(record: Any, path: Path, *, stage: str,
                              sources: dict[str, str] | None = None) -> dict[str, Any]:
    if not isinstance(record, dict) or record.get("schema") != SCHEMA or record.get("stage") != stage:
        raise ValueError(f"Missing current {stage} audio acceptance evidence")
    if record.get("policy") != POLICY:
        raise ValueError(f"Stale {stage} audio acceptance policy")
    if record.get("method") != "ffmpeg-loudnorm-input" or not record.get("toolVersion") or not record.get("measuredAt"):
        raise ValueError(f"Missing {stage} measurement provenance")
    if record.get("audioStream") != "0:a:0":
        raise ValueError("Unsupported measured audio stream")
    source_names = {"manifest", "rawTurns"} if stage == "master" else {"manifest", "master"}
    recorded_sources = record.get("sources")
    if (not isinstance(recorded_sources, dict) or set(recorded_sources) != source_names
            or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
                   for value in recorded_sources.values())):
        raise ValueError(f"Missing {stage} source fingerprints")
    fingerprint = {"sha256": file_sha256(path), "sizeBytes": path.stat().st_size}
    if record.get("artifact") != fingerprint:
        raise ValueError(f"Stale {stage} audio acceptance: artifact changed")
    if sources is not None and record.get("sources") != sources:
        raise ValueError(f"Stale {stage} audio acceptance: source changed")
    measurements = record.get("measurements")
    errors = acceptance_errors(measurements if isinstance(measurements, dict) else {})
    if errors or record.get("status") != "passed" or record.get("errors") != []:
        raise ValueError(f"{stage} audio acceptance failed: " + "; ".join(errors or ["record is not passed"]))
    return record


def master_sources(workspace: Path, episode_id: str) -> dict[str, str]:
    manifest_path = workspace / f"000_{episode_id}.episode_manifest.json"
    manifest = load_json(manifest_path)
    raw_hashes = [file_sha256(turn_wav_path(workspace, str(turn["filename"]))) for turn in manifest["turns"]]
    return {"manifest": file_sha256(manifest_path),
            "rawTurns": hashlib.sha256(json.dumps(raw_hashes).encode("utf-8")).hexdigest()}


def encoded_sources(workspace: Path, episode_id: str) -> dict[str, str]:
    return {"manifest": file_sha256(workspace / f"000_{episode_id}.episode_manifest.json"),
            "master": file_sha256(artifact_paths(workspace, episode_id)["masterWav"])}


def require_episode_audio_acceptance(workspace: Path, episode_id: str, *, encoded: bool = True) -> dict[str, Any]:
    """Read-only gate; reuse measured evidence only when its exact media/inputs match."""
    paths = artifact_paths(workspace, episode_id)
    manifest = load_json(workspace / f"000_{episode_id}.episode_manifest.json")
    report = load_json(paths["masterReport"])
    master = validate_audio_acceptance(report.get("audioAcceptance"), paths["masterWav"],
                                       stage="master", sources=master_sources(workspace, episode_id))
    timeline, _ = resolve_episode_timeline(workspace, manifest)
    if timeline["source"] != "mastered-turns-hash-verified":
        raise ValueError("Final audio acceptance requires a fingerprinted master timeline")
    result = {"master": master}
    if encoded:
        video_report = load_json(paths["videoReport"])
        result["encoded"] = validate_audio_acceptance(
            video_report.get("audioAcceptance"), paths["mp4"], stage="encoded",
            sources=encoded_sources(workspace, episode_id),
        )
    return result
