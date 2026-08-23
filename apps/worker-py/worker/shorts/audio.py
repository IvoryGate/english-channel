from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import soundfile as sf
import numpy as np

from .workspace import atomic_write_json, ensure_workspace


def _runtime_root(repo_root: Path) -> Path:
    configured = os.environ.get("ELR_SHORTS_RUNTIME_ROOT")
    if configured:
        return Path(configured).resolve()
    candidates = [repo_root.resolve(), repo_root.resolve().parent.parent]
    for candidate in candidates:
        if (candidate / "pretrained_models" / "VoxCPM2").is_dir():
            return candidate
    return repo_root.resolve()


def _required_runtime_file(runtime_root: Path, relative: str, env_name: str) -> Path:
    configured = os.environ.get(env_name)
    path = Path(configured).resolve() if configured else (runtime_root / relative).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Missing Shorts voice reference: {path}. Set {env_name} to override it.")
    return path


def build_audio_manifest(repo_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    runtime_root = _runtime_root(repo_root)
    model = Path(os.environ.get("VOXCPM_MODEL_ID", runtime_root / "pretrained_models" / "VoxCPM2")).resolve()
    if not model.is_dir():
        raise FileNotFoundError(f"VoxCPM2 model is unavailable: {model}")
    riley = _required_runtime_file(
        runtime_root,
        "assets/voices/series_b/riley_reference_clean.wav",
        "ELR_SHORTS_RILEY_REFERENCE",
    )
    sam = _required_runtime_file(
        runtime_root,
        "assets/voices/series_b/sam_reference_clean.wav",
        "ELR_SHORTS_SAM_REFERENCE",
    )
    source_segments: list[dict[str, Any]] = [
        {"sourceId": "hook", "kind": "hook", "speaker": "Riley", "text": manifest["hook"]}
    ]
    for turn in manifest["turns"]:
        speaker = "Sam" if str(turn["speaker"]).casefold() == "sam" else "Riley"
        source_segments.append(
            {
                "sourceId": turn["id"],
                "kind": "body",
                "speaker": speaker,
                "text": turn["text"],
            }
        )
    source_segments.extend(
        [
            {"sourceId": "prompt", "kind": "prompt", "speaker": "Riley", "text": manifest["prompt"]},
            {"sourceId": "answer", "kind": "answer", "speaker": "Riley", "text": manifest["answer"]},
        ]
    )
    turns = []
    for index, segment in enumerate(source_segments, start=1):
        pause_after = 0.1
        if segment["kind"] == "hook":
            pause_after = 0.08
        elif segment["kind"] == "prompt":
            pause_after = 2.25
        elif segment["kind"] == "answer":
            pause_after = 0.2
        turns.append(
            {
                "id": f"a{index:03d}",
                "sourceId": segment["sourceId"],
                "kind": segment["kind"],
                "order": index,
                "speaker": segment["speaker"],
                "text": segment["text"],
                "wordCount": len(str(segment["text"]).split()),
                "filename": f"voice_{index:03d}.wav",
                "deliveryCue": "clear concise short-form English, immediate start, natural energy",
                "maxLen": 128,
                "pauseAfterSec": pause_after,
            }
        )
    return {
        "schema": "elr-short-audio-manifest-v1",
        "episodeId": manifest["shortId"],
        "shortId": manifest["shortId"],
        "showId": "series_b",
        "hosts": {
            "Riley": {"role": "narrator", "referenceAudioClean": str(riley)},
            "Sam": {"role": "dialogue partner", "referenceAudioClean": str(sam)},
        },
        "renderSettings": {
            "modelId": str(model),
            "device": os.environ.get("ELR_SHORTS_DEVICE", "cuda"),
            "cfgValue": 2.15,
            "inferenceTimesteps": 10,
            "interTurnSilenceSec": float(manifest["renderSettings"]["interTurnSilenceSec"]),
            "renderReport": "short_audio_render_report.json",
        },
        "turns": turns,
    }


def _tempo_factor_for_variant(raw_duration: float, manifest: dict[str, Any]) -> float:
    planned = float(manifest["durationPlannedSec"])
    cutoff = float(manifest.get("renderSettings", {}).get("durationVariantCutoffSec", 50.0))
    planned_is_short = planned <= cutoff
    raw_is_short = raw_duration <= cutoff
    if planned_is_short == raw_is_short:
        return 1.0
    factor = raw_duration / planned
    if not 0.5 <= factor <= 2.0:
        raise ValueError(f"Required tempo factor {factor:.3f} is outside ffmpeg's safe range")
    return factor


def _master_audio(raw_path: Path, master_path: Path, manifest: dict[str, Any]) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to master Shorts audio")
    target = float(manifest["renderSettings"]["loudnessTargetLufs"])
    peak = float(manifest["renderSettings"]["truePeakMaxDb"])
    sample_rate = int(manifest["renderSettings"]["audioSampleRate"])
    raw_duration = float(sf.info(raw_path).duration)
    tempo_factor = _tempo_factor_for_variant(raw_duration, manifest)
    filters = []
    if tempo_factor != 1.0:
        filters.append(f"atempo={tempo_factor:.6f}")
    filters.append(f"loudnorm=I={target}:TP={peak}:LRA=11")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-i",
            str(raw_path),
            "-af",
            ",".join(filters),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(master_path),
        ],
        check=True,
    )


def _compose_audio(workspace: Path, audio_manifest: dict[str, Any], raw_path: Path) -> None:
    clips: list[np.ndarray] = []
    sample_rate: int | None = None
    turns_dir = workspace / "audio" / "turns"
    for turn in audio_manifest["turns"]:
        audio_path = turns_dir / str(turn["filename"])
        audio, rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        if sample_rate is None:
            sample_rate = int(rate)
        elif int(rate) != sample_rate:
            raise ValueError(f"Short turn sample-rate mismatch: {audio_path} is {rate}, expected {sample_rate}")
        clips.append(audio.astype(np.float32, copy=False))
        pause = float(turn.get("pauseAfterSec", 0.1))
        if pause > 0:
            clips.append(np.zeros(int(round(pause * sample_rate)), dtype=np.float32))
    if sample_rate is None or not clips:
        raise ValueError("No rendered Short audio segments are available to compose")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(raw_path, np.concatenate(clips), sample_rate, subtype="PCM_16")


def _sync_timing(
    workspace: Path,
    manifest: dict[str, Any],
    audio_manifest: dict[str, Any],
    master_path: Path,
) -> None:
    source_duration = 0.0
    turns_dir = workspace / "audio" / "turns"
    for turn in audio_manifest["turns"]:
        source_duration += float(sf.info(turns_dir / str(turn["filename"])).duration)
        source_duration += float(turn.get("pauseAfterSec", 0.1))
    master_duration = float(sf.info(master_path).duration)
    timeline_scale = master_duration / source_duration
    cursor = 0.0
    timings: dict[str, tuple[float, float]] = {}
    for index, turn in enumerate(audio_manifest["turns"]):
        audio_path = turns_dir / str(turn["filename"])
        duration = float(sf.info(audio_path).duration) * timeline_scale
        timings[str(turn["sourceId"])] = (cursor, cursor + duration)
        cursor += duration
        cursor += float(turn.get("pauseAfterSec", 0.1)) * timeline_scale
    for turn in manifest["turns"]:
        start, end = timings[str(turn["id"])]
        turn["startSec"] = round(start, 3)
        turn["endSec"] = round(end, 3)
    manifest["hookEndSec"] = round(timings["hook"][1], 3)
    manifest["promptStartSec"] = round(timings["prompt"][0], 3)
    manifest["answerStartSec"] = round(timings["answer"][0], 3)
    manifest["durationSec"] = round(master_duration, 3)
    manifest["audio"] = {
        "status": "ready",
        "master": str(master_path.relative_to(workspace)),
        "renderer": "voxcpm2-short-form-v1",
        "sourceManifest": "audio_manifest.json",
        "timelineScale": round(timeline_scale, 6),
    }


def render_audio(
    repo_root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    force: bool = False,
) -> Path:
    workspace = ensure_workspace(repo_root, str(manifest["shortId"]))
    audio_manifest = build_audio_manifest(repo_root, manifest)
    audio_manifest_path = workspace / "audio_manifest.json"
    atomic_write_json(audio_manifest_path, audio_manifest)
    command = [
        sys.executable,
        str(repo_root / "workspace" / "shows" / "tools" / "render_episode.py"),
        "--manifest",
        str(audio_manifest_path),
        "--device",
        str(audio_manifest["renderSettings"]["device"]),
        "--skip-existing",
        "--no-self-check",
        "--no-compose",
    ]
    if force:
        command.append("--force")
    try:
        import gpu_production_lock
    except ImportError as exc:
        raise RuntimeError("The shared ELR GPU production lock is unavailable") from exc
    runtime_root = _runtime_root(repo_root)
    gpu_production_lock.LOCK_PATH = runtime_root / "logs" / "gpu_production.lock"
    with gpu_production_lock.GpuProductionLock(f"shorts:{manifest['shortId']}"):
        subprocess.run(command, cwd=repo_root, check=True)
    raw_path = workspace / "audio" / f"000_{manifest['shortId']}.raw.wav"
    master_path = workspace / "audio" / "master.wav"
    _compose_audio(workspace, audio_manifest, raw_path)
    _master_audio(raw_path, master_path, manifest)
    _sync_timing(workspace, manifest, audio_manifest, master_path)
    atomic_write_json(manifest_path, manifest)
    return master_path
