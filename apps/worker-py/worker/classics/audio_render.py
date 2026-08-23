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

from .config import BookConfig
from .io import atomic_write_json, read_json, sha256_file
from .paths import ClassicPaths
from .preflight import preflight_chapter
from .run_state import RunStateStore


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
        sf.write(temp_name, audio.astype(np.float32, copy=False), sample_rate, subtype="PCM_24")
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
    # is carried by the Riley reference audio; synthesis input stays source-only.
    return str(segment["spokenText"])


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
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, Any]:
    if isolated_preview and not preview_name:
        raise AudioRenderError("isolated_preview requires preview_name")
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
    model_path = config.runtime_path(repo_root, str(config.render["modelId"]))
    device = str(config.render.get("device", "cuda"))
    target_rate = int(config.render["sampleRate"])
    silence_seconds = float(config.render["interSegmentSilenceSec"])
    effective_cfg_value = float(config.voice["cfgValue"] if cfg_value is None else cfg_value)
    effective_timesteps = int(
        config.voice["inferenceTimesteps"] if inference_timesteps is None else inference_timesteps
    )
    if effective_cfg_value <= 0 or effective_timesteps <= 0:
        raise AudioRenderError("Generation overrides must be positive")

    segment_dir = (
        paths.audio_dir(chapter) / "previews" / str(preview_name) / "segments"
        if isolated_preview
        else paths.segment_audio_dir(chapter)
    )
    needs_generation = force or any(not (segment_dir / str(segment["filename"])).is_file() for segment in targets)
    model = model_factory(str(model_path), device) if needs_generation else None
    model_rate = int(model.tts_model.sample_rate) if model is not None else None
    rendered: list[dict[str, Any]] = []
    composed_parts: list[np.ndarray] = []
    for index, segment in enumerate(targets):
        output = segment_dir / str(segment["filename"])
        if output.is_file() and not force:
            audio, existing_rate = sf.read(output, dtype="float32")
            audio = _mono_float(audio)
            if int(existing_rate) != target_rate:
                raise AudioRenderError(f"Existing segment has wrong sample rate: {output}")
            reused = True
        else:
            if model is None or model_rate is None:
                raise AudioRenderError("Narration model was not initialized for a missing segment")
            generated = model.generate(
                text=tts_text(segment),
                prompt_wav_path=str(reference_path),
                prompt_text=profile.prompt_text,
                reference_wav_path=str(reference_path),
                cfg_value=effective_cfg_value,
                inference_timesteps=effective_timesteps,
                normalize=bool(config.voice["normalize"]),
                denoise=bool(config.voice["denoise"]),
            )
            audio = _resample(_mono_float(generated), model_rate, target_rate)
            _atomic_write_wav(output, audio, target_rate)
            reused = False
        rendered.append(
            {
                "id": str(segment["id"]),
                "path": output.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(output),
                "durationSec": round(float(len(audio) / target_rate), 3),
                "reused": reused,
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
        "modelPath": str(model_path),
        "modelSampleRate": model_rate,
        "outputSampleRate": target_rate,
        "generationSettings": {
            "cfgValue": effective_cfg_value,
            "inferenceTimesteps": effective_timesteps,
            "normalize": bool(config.voice["normalize"]),
            "denoise": bool(config.voice["denoise"]),
            "isolatedPreview": isolated_preview,
        },
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
