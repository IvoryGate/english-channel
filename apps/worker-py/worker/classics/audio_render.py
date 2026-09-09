from __future__ import annotations

import math
import os
import tempfile
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy import signal

from worker.voice_profiles import resolve_voice_profile
from worker.tts.process import run_provider_batch
from worker.tts.schema import resolve_provider_config, validate_voice
from worker.tts.trace import (
    TRACE_SCHEMA,
    atomic_write_json as atomic_write_turn_trace,
    build_turn_identity,
    normalized_text,
    trace_is_reusable,
    turn_trace_path,
)

from .config import BookConfig, ConfigError, require_approved_voice
from .io import atomic_write_json, read_json, sha256_file
from .paths import ClassicPaths
from .preflight import preflight_chapter
from .run_state import RunStateStore
from .voxcpm_memory import patch_voxcpm_low_memory_load


class AudioRenderError(RuntimeError):
    pass


ModelFactory = Callable[[str, str], Any]


def parse_segment_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    ids = {part.strip().zfill(3) for part in value.split(",") if part.strip()}
    if any(not item.isdigit() for item in ids):
        raise AudioRenderError("Segment ids must be comma-separated numbers")
    return ids


def _default_model_factory(model_id: str, device: str) -> Any:
    import torch

    patch_voxcpm_low_memory_load()
    from voxcpm import VoxCPM

    # VoxCPM2 checkpoints are bfloat16, but its loader otherwise constructs a
    # temporary float32 model first. On production laptops that doubles peak
    # host memory and can terminate the process before weights are assigned.
    previous_dtype = torch.get_default_dtype()
    try:
        if device.startswith("cuda"):
            torch.set_default_dtype(torch.bfloat16)
        optimize = os.getenv("CLASSICS_VOXCPM_OPTIMIZE", "1").strip().lower() in {"1", "true", "yes", "on"}
        if optimize:
            cache_root = Path(model_id).resolve().parents[1] / "tmp"
            triton_cache = cache_root / "triton-cache"
            inductor_cache = cache_root / "torchinductor-cache"
            triton_cache.mkdir(parents=True, exist_ok=True)
            inductor_cache.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault("TRITON_CACHE_DIR", str(triton_cache))
            os.environ.setdefault("TORCHINDUCTOR_CACHE_DIR", str(inductor_cache))
            torch.set_float32_matmul_precision("high")
        return VoxCPM.from_pretrained(
            model_id,
            device=device,
            optimize=optimize,
            load_denoiser=False,
            local_files_only=True,
        )
    finally:
        torch.set_default_dtype(previous_dtype)


def _atomic_write_wav(path: Path, audio: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".wav", dir=path.parent)
    os.close(fd)
    try:
        sf.write(temp_name, audio.astype(np.float32, copy=False), sample_rate, subtype="FLOAT")
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def _mono_float(audio: Any) -> np.ndarray:
    value = np.asarray(audio, dtype=np.float32)
    if value.ndim == 2:
        value = value.mean(axis=1)
    if value.ndim != 1 or value.size == 0:
        raise AudioRenderError("Model returned empty or invalid audio")
    if not np.isfinite(value).all():
        raise AudioRenderError("Model returned non-finite audio")
    return value


def _resample(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    if source_rate == target_rate:
        return audio.astype(np.float32, copy=False)
    divisor = math.gcd(source_rate, target_rate)
    return signal.resample_poly(audio, target_rate // divisor, source_rate // divisor).astype(np.float32)


def tts_text(segment: dict[str, Any]) -> str:
    # VoxCPM treats parenthetical style descriptions as words to speak. Style
    # is carried by the narrator reference audio; synthesis input stays
    # source-only. Literal parentheses can also terminate generation early, so
    # preserve every source word while converting the marks to spoken pauses.
    return str(segment["spokenText"]).replace("(", ", ").replace(")", ", ")


def render_audio(
    repo_root: Path,
    config: BookConfig,
    chapter: int,
    selected_ids: set[str] | None = None,
    *,
    preview_name: str | None = None,
    force: bool = False,
    cfg_value: float | None = None,
    inference_timesteps: int | None = None,
    isolated_preview: bool = False,
    seed_offsets: dict[str, int] | None = None,
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, Any]:
    if isolated_preview and not preview_name:
        raise AudioRenderError("isolated_preview requires preview_name")
    try:
        require_approved_voice(config)
    except ConfigError as exc:
        raise AudioRenderError(str(exc)) from exc
    report = preflight_chapter(repo_root, config, chapter)
    if not report.ok:
        errors = "; ".join(check.detail for check in report.checks if check.status == "error")
        raise AudioRenderError(f"Preflight failed: {errors}")
    paths = ClassicPaths(repo_root, config.slug)
    manifest = read_json(paths.segments(chapter))
    segments = manifest.get("segments")
    if not isinstance(segments, list) or not segments:
        raise AudioRenderError("Segment manifest is empty")
    known_ids = {str(item["id"]) for item in segments}
    selected = selected_ids or known_ids
    unknown = selected - known_ids
    if unknown:
        raise AudioRenderError(f"Unknown segment ids: {sorted(unknown)}")
    targets = [item for item in segments if str(item["id"]) in selected]

    profile = resolve_voice_profile(str(config.voice["profileId"]))
    if profile.id != config.voice["profileId"]:
        raise AudioRenderError(f"Voice profile is not registered: {config.voice['profileId']}")
    reference_path = config.repo_path(repo_root, str(config.voice["referencePath"]))
    provider = resolve_provider_config(repo_root, config.render)
    target_rate = int(config.render["sampleRate"])
    silence_seconds = float(config.render["interSegmentSilenceSec"])
    if provider.provider_id != "voxcpm" and (cfg_value is not None or inference_timesteps is not None):
        raise AudioRenderError("VoxCPM generation overrides cannot be used with this provider")
    if provider.provider_id == "voxcpm":
        provider.settings["cfgValue"] = float(
            config.voice["cfgValue"] if cfg_value is None else cfg_value
        )
        provider.settings["inferenceTimesteps"] = int(
            config.voice["inferenceTimesteps"]
            if inference_timesteps is None
            else inference_timesteps
        )
    voice = validate_voice(
        provider.provider_id,
        {
            "kind": "clone",
            "referencePath": str(config.voice["referencePath"]),
            "referenceSha256": str(config.voice["referenceSha256"]),
        },
    )
    if sha256_file(reference_path) != voice["referenceSha256"]:
        raise AudioRenderError("Classic narrator reference SHA-256 mismatch")

    segment_dir = (
        paths.audio_dir(chapter) / "previews" / str(preview_name) / "segments"
        if isolated_preview
        else paths.segment_audio_dir(chapter)
    )
    provider_trace = provider.to_trace(repo_root)
    specs: dict[str, dict[str, Any]] = {}
    requests: list[dict[str, Any]] = []
    for segment in targets:
        segment_id = str(segment["id"])
        output = segment_dir / str(segment["filename"])
        seed_offset = (seed_offsets or {}).get(segment_id, 0)
        if not isinstance(seed_offset, int) or isinstance(seed_offset, bool):
            raise AudioRenderError("seed_offsets values must be integers")
        seed = provider.seed_base + int(segment_id) + seed_offset
        text = normalized_text(tts_text(segment))
        identity = build_turn_identity(
            provider=provider_trace,
            voice=voice,
            text=text,
            seed=seed,
        )
        specs[segment_id] = {"seed": seed, "text": text, "identity": identity}
        if force or not trace_is_reusable(output, str(identity["sha256"])):
            requests.append(
                {
                    "id": segment_id,
                    "outputPath": str(output),
                    "text": text,
                    "voice": {**voice, "referencePath": str(reference_path)},
                    "referenceText": profile.prompt_text,
                    "seed": seed,
                    "maxLen": None,
                }
            )
    if model_factory is not _default_model_factory and requests:
        raise AudioRenderError("Custom in-process model factories are supported only by the legacy VoxCPM renderer")
    results = run_provider_batch(
        repo_root,
        provider,
        requests,
        label=f"classic-{config.slug}-{chapter:03d}-{provider.provider_id}",
    )
    by_id = {str(item["id"]): item for item in results}
    model_rate = int(results[0]["sampleRate"]) if results else target_rate
    rendered: list[dict[str, Any]] = []
    composed_parts: list[np.ndarray] = []
    for index, segment in enumerate(targets):
        segment_id = str(segment["id"])
        output = segment_dir / str(segment["filename"])
        spec = specs[segment_id]
        if segment_id not in by_id:
            audio, existing_rate = sf.read(output, dtype="float32")
            audio = _mono_float(audio)
            if int(existing_rate) != target_rate:
                raise AudioRenderError(f"Existing segment has wrong sample rate: {output}")
            reused = True
        else:
            result = by_id[segment_id]
            audio, generated_rate = sf.read(output, dtype="float32")
            audio = _resample(_mono_float(audio), int(generated_rate), target_rate)
            if int(generated_rate) != target_rate:
                _atomic_write_wav(output, audio, target_rate)
            prior: dict[str, Any] = {}
            prior_path = turn_trace_path(output)
            if prior_path.is_file():
                try:
                    prior = read_json(prior_path)
                except (OSError, ValueError):
                    pass
            trace = {
                "schema": TRACE_SCHEMA,
                "turnId": segment_id,
                "bookSlug": config.slug,
                "chapter": chapter,
                "renderedAt": datetime.now(timezone.utc).isoformat(),
                "provider": {
                    **provider_trace,
                    "packageVersion": result["packageVersion"],
                    "modelLoadSec": result["modelLoadSec"],
                },
                "voice": voice,
                "normalizedText": spec["text"],
                "seed": spec["seed"],
                "effectiveSettings": provider.settings,
                "identitySha256": spec["identity"]["sha256"],
                "sampleRate": target_rate,
                "durationSec": round(float(len(audio) / target_rate), 3),
                "generationSec": result["generationSec"],
                "peak": round(float(np.max(np.abs(audio))), 6),
                "outputSha256": sha256_file(output),
                "watermark": result["watermark"],
                "retryNumber": int(prior.get("retryNumber") or -1) + 1 if prior else 0,
                "priorArtifactSha256": prior.get("outputSha256"),
            }
            atomic_write_turn_trace(prior_path, trace)
            reused = False
        rendered.append(
            {
                "id": segment_id,
                "path": output.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(output),
                "durationSec": round(float(len(audio) / target_rate), 3),
                "reused": reused,
                "providerId": provider.provider_id,
                "tracePath": turn_trace_path(output).relative_to(repo_root).as_posix(),
            }
        )
        composed_parts.append(audio)
        if index < len(targets) - 1:
            composed_parts.append(np.zeros(round(target_rate * silence_seconds), dtype=np.float32))

    if not composed_parts:
        raise AudioRenderError("No segments selected")
    preview_path: Path | None = None
    raw_path: Path | None = None
    if preview_name:
        if not preview_name.replace("-", "").replace("_", "").isalnum():
            raise AudioRenderError("Preview name may contain only letters, numbers, '-' and '_'")
        preview_path = paths.audio_dir(chapter) / "previews" / f"{preview_name}.wav"
        _atomic_write_wav(preview_path, np.concatenate(composed_parts), target_rate)
    elif selected == known_ids:
        raw_path = paths.raw_audio(chapter)
        _atomic_write_wav(raw_path, np.concatenate(composed_parts), target_rate)

    trace = {
        "schema": "classic-listening-audio-render-v1",
        "bookSlug": config.slug,
        "chapter": chapter,
        "renderedAt": datetime.now(timezone.utc).isoformat(),
        "voiceMode": "single",
        "styleControl": manifest["globalControl"],
        "voiceProfile": profile.to_trace(),
        "sourceSha256": manifest["sourceSha256"],
        "segmentManifestSha256": sha256_file(paths.segments(chapter)),
        "referenceSha256": sha256_file(reference_path),
        "provider": provider_trace,
        "modelPath": str(provider.local_model_path),
        "modelSampleRate": model_rate,
        "outputSampleRate": target_rate,
        "generationSettings": {**provider.settings, "isolatedPreview": isolated_preview},
        "segments": rendered,
        "previewPath": preview_path.relative_to(repo_root).as_posix() if preview_path else None,
        "rawPath": raw_path.relative_to(repo_root).as_posix() if raw_path else None,
    }
    trace_path = paths.reports_dir(chapter) / (
        f"audio-preview-{preview_name}.json" if preview_name else "audio-render.json"
    )
    atomic_write_json(trace_path, trace)
    RunStateStore(paths.state).update(
        status="AWAITING_APPROVAL" if preview_name else "RUNNING",
        phase="VOICE_PREVIEW" if preview_name else "AUDIO_RENDER",
        activeChapter=chapter,
        lastTracePath=trace_path.relative_to(repo_root).as_posix(),
    )
    trace["tracePath"] = trace_path.relative_to(repo_root).as_posix()
    return trace
