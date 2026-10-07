from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

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

from .audio_render import _atomic_write_wav, _default_model_factory, _mono_float, _resample
from .config import BookConfig, ConfigError, require_approved_voice
from .io import atomic_write_json, sha256_file


class BrandVoiceError(RuntimeError):
    pass


ModelFactory = Callable[[str, str], Any]


def _chapter_word(number: int) -> str:
    words = {
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
        10: "Ten",
        11: "Eleven",
        12: "Twelve",
        13: "Thirteen",
        14: "Fourteen",
        15: "Fifteen",
        16: "Sixteen",
        17: "Seventeen",
        18: "Eighteen",
        19: "Nineteen",
        20: "Twenty",
        21: "Twenty One",
        22: "Twenty Two",
        23: "Twenty Three",
        24: "Twenty Four",
    }
    if number not in words:
        raise BrandVoiceError(f"Unsupported chapter number: {number}")
    return words[number]


def _branding_string(config: BookConfig, key: str) -> str:
    value = config.branding.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BrandVoiceError(f"branding.{key} must be a non-empty string")
    return value.strip()


def _render_provider_brand_jobs(
    repo_root: Path,
    config: BookConfig,
    profile: Any,
    reference_path: Path,
    jobs: list[dict[str, Any]],
    *,
    force: bool,
    trace_path: Path,
    trace_schema: str,
) -> dict[str, Any]:
    provider = resolve_provider_config(repo_root, config.render)
    provider_trace = provider.to_trace(repo_root)
    voice = validate_voice(
        provider.provider_id,
        {
            "kind": "clone",
            "referencePath": str(config.voice["referencePath"]),
            "referenceSha256": str(config.voice["referenceSha256"]),
        },
    )
    target_rate = int(config.render["sampleRate"])
    lead_silence = float(config.branding.get("voiceLeadSilenceSec", 0.16))
    tail_silence = float(config.branding.get("voiceTailSilenceSec", 0.42))
    requests: list[dict[str, Any]] = []
    specs: dict[str, dict[str, Any]] = {}
    for index, job in enumerate(jobs):
        job_id = str(job["id"])
        text = normalized_text(str(job["text"]))
        settings = {**provider.settings, **dict(job.get("providerSettings") or {})}
        identity_provider = {**provider_trace, "providerSettings": settings}
        identity = build_turn_identity(
            provider=identity_provider,
            voice=voice,
            text=text,
            seed=provider.seed_base + index,
        )
        output = Path(job["outputPath"])
        specs[job_id] = {
            "identity": identity,
            "settings": settings,
            "seed": provider.seed_base + index,
            "text": text,
            "output": output,
        }
        if force or not trace_is_reusable(output, str(identity["sha256"])):
            requests.append(
                {
                    "id": job_id,
                    "outputPath": str(output),
                    "text": text,
                    "voice": {**voice, "referencePath": str(reference_path)},
                    "referenceText": profile.prompt_text,
                    "providerSettings": settings,
                    "seed": provider.seed_base + index,
                    "maxLen": None,
                }
            )
    results = (
        run_provider_batch(
            repo_root,
            provider,
            requests,
            label=f"classic-{config.slug}-branding-{provider.provider_id}",
        )
        if requests
        else []
    )
    by_id = {str(row["id"]): row for row in results}
    rendered: list[dict[str, Any]] = []
    for job in jobs:
        job_id = str(job["id"])
        spec = specs[job_id]
        output = Path(spec["output"])
        reused = job_id not in by_id
        audio, sample_rate = sf.read(output, dtype="float32")
        audio = _mono_float(audio)
        if not reused:
            result = by_id[job_id]
            speech = _resample(audio, int(sample_rate), target_rate)
            peak = float(np.max(np.abs(speech)))
            if peak > 0.89:
                speech = speech * (0.89 / peak)
            audio = np.concatenate(
                (
                    np.zeros(round(target_rate * lead_silence), dtype=np.float32),
                    speech,
                    np.zeros(round(target_rate * tail_silence), dtype=np.float32),
                )
            )
            _atomic_write_wav(output, audio, target_rate)
            turn_trace = {
                "schema": TRACE_SCHEMA,
                "turnId": job_id,
                "bookSlug": config.slug,
                "renderedAt": datetime.now(timezone.utc).isoformat(),
                "provider": {
                    **provider_trace,
                    "packageVersion": result["packageVersion"],
                    "modelLoadSec": result["modelLoadSec"],
                },
                "voice": voice,
                "normalizedText": spec["text"],
                "seed": spec["seed"],
                "effectiveSettings": spec["settings"],
                "identitySha256": spec["identity"]["sha256"],
                "sampleRate": target_rate,
                "durationSec": round(float(len(audio) / target_rate), 3),
                "generationSec": result["generationSec"],
                "outputSha256": sha256_file(output),
                "watermark": result["watermark"],
            }
            atomic_write_turn_trace(turn_trace_path(output), turn_trace)
        elif int(sample_rate) != target_rate:
            raise BrandVoiceError(f"Existing brand voice has wrong sample rate: {output}")
        rendered.append(
            {
                **dict(job.get("metadata") or {}),
                "kind": str(job["kind"]),
                "text": str(job["text"]),
                "path": output.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(output),
                "durationSec": round(float(len(audio) / target_rate), 3),
                "peak": round(float(np.max(np.abs(audio))), 6),
                "reused": reused,
                "providerId": provider.provider_id,
                "tracePath": turn_trace_path(output).relative_to(repo_root).as_posix(),
                "generationSettings": spec["settings"],
            }
        )
    trace = {
        "schema": trace_schema,
        "bookSlug": config.slug,
        "renderedAt": datetime.now(timezone.utc).isoformat(),
        "voiceProfile": profile.to_trace(),
        "referencePath": reference_path.relative_to(repo_root).as_posix(),
        "referenceSha256": sha256_file(reference_path),
        "provider": provider_trace,
        "outputSampleRate": target_rate,
        "clips": rendered,
    }
    atomic_write_json(trace_path, trace)
    trace["tracePath"] = trace_path.relative_to(repo_root).as_posix()
    return trace


def render_brand_voice(
    repo_root: Path,
    config: BookConfig,
    *,
    force: bool = False,
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, Any]:
    try:
        require_approved_voice(config)
    except ConfigError as exc:
        raise BrandVoiceError(str(exc)) from exc
    profile = resolve_voice_profile(str(config.voice["profileId"]))
    if profile.id != config.voice["profileId"]:
        raise BrandVoiceError(f"Voice profile is not registered: {config.voice['profileId']}")

    reference_path = config.repo_path(repo_root, str(config.voice["referencePath"]))
    if not reference_path.is_file():
        raise BrandVoiceError(f"Voice reference does not exist: {reference_path}")
    reference_hash = sha256_file(reference_path)
    if reference_hash != config.voice["referenceSha256"]:
        raise BrandVoiceError("Voice reference SHA-256 does not match the book config")

    device = str(config.render.get("device", "cuda"))
    target_rate = int(config.render["sampleRate"])
    cfg_value = float(config.branding.get("voiceCfgValue", config.voice["cfgValue"]))
    inference_timesteps = int(
        config.branding.get("voiceInferenceTimesteps", config.voice["inferenceTimesteps"])
    )
    lead_silence = float(config.branding.get("voiceLeadSilenceSec", 0.16))
    tail_silence = float(config.branding.get("voiceTailSilenceSec", 0.42))
    jobs = (
        (
            "intro",
            _branding_string(config, "introSpokenText"),
            config.repo_path(repo_root, _branding_string(config, "introVoicePath")),
        ),
        (
            "outro",
            _branding_string(config, "outroSpokenText"),
            config.repo_path(repo_root, _branding_string(config, "outroVoicePath")),
        ),
    )

    if model_factory is _default_model_factory:
        provider_jobs = [
            {
                "id": kind,
                "kind": kind,
                "text": text,
                "outputPath": output_path,
                "providerSettings": (
                    {
                        "cfgValue": float(config.branding.get(f"{kind}VoiceCfgValue", cfg_value)),
                        "inferenceTimesteps": int(
                            config.branding.get(
                                f"{kind}VoiceInferenceTimesteps", inference_timesteps
                            )
                        ),
                    }
                    if resolve_provider_config(repo_root, config.render).provider_id == "voxcpm"
                    else {}
                ),
            }
            for kind, text, output_path in jobs
        ]
        return _render_provider_brand_jobs(
            repo_root,
            config,
            profile,
            reference_path,
            provider_jobs,
            force=force,
            trace_path=repo_root
            / "workspace"
            / "classics"
            / config.slug
            / "branding"
            / "brand-voice-render.json",
            trace_schema="classic-listening-brand-voice-v1",
        )

    model_path = config.runtime_path(repo_root, str(config.render["modelId"]))
    model = model_factory(str(model_path), device)
    model_rate = int(model.tts_model.sample_rate)
    rendered: list[dict[str, Any]] = []
    for kind, text, output_path in jobs:
        clip_cfg_value = float(config.branding.get(f"{kind}VoiceCfgValue", cfg_value))
        clip_inference_timesteps = int(
            config.branding.get(f"{kind}VoiceInferenceTimesteps", inference_timesteps)
        )
        reused = output_path.is_file() and not force
        if reused:
            import soundfile as sf

            audio, existing_rate = sf.read(output_path, dtype="float32")
            audio = _mono_float(audio)
            if int(existing_rate) != target_rate:
                raise BrandVoiceError(f"Existing brand voice has wrong sample rate: {output_path}")
        else:
            generated = model.generate(
                text=text,
                prompt_wav_path=str(reference_path),
                prompt_text=profile.prompt_text,
                reference_wav_path=str(reference_path),
                cfg_value=clip_cfg_value,
                inference_timesteps=clip_inference_timesteps,
                normalize=bool(config.voice.get("normalize", False)),
                denoise=bool(config.voice.get("denoise", False)),
            )
            speech = _resample(_mono_float(generated), model_rate, target_rate)
            peak = float(np.max(np.abs(speech)))
            if peak > 0.89:
                speech = speech * (0.89 / peak)
            audio = np.concatenate(
                (
                    np.zeros(round(target_rate * lead_silence), dtype=np.float32),
                    speech,
                    np.zeros(round(target_rate * tail_silence), dtype=np.float32),
                )
            )
            _atomic_write_wav(output_path, audio, target_rate)
        rendered.append(
            {
                "kind": kind,
                "text": text,
                "path": output_path.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(output_path),
                "durationSec": round(float(len(audio) / target_rate), 3),
                "peak": round(float(np.max(np.abs(audio))), 6),
                "reused": reused,
                "generationSettings": {
                    "cfgValue": clip_cfg_value,
                    "inferenceTimesteps": clip_inference_timesteps,
                },
            }
        )

    trace_path = repo_root / "workspace" / "classics" / config.slug / "branding" / "brand-voice-render.json"
    trace = {
        "schema": "classic-listening-brand-voice-v1",
        "bookSlug": config.slug,
        "renderedAt": datetime.now(timezone.utc).isoformat(),
        "voiceProfile": profile.to_trace(),
        "referencePath": reference_path.relative_to(repo_root).as_posix(),
        "referenceSha256": reference_hash,
        "modelPath": str(model_path),
        "device": device,
        "modelSampleRate": model_rate,
        "outputSampleRate": target_rate,
        "generationSettings": {
            "cfgValue": cfg_value,
            "inferenceTimesteps": inference_timesteps,
            "normalize": bool(config.voice.get("normalize", False)),
            "denoise": bool(config.voice.get("denoise", False)),
        },
        "clips": rendered,
    }
    atomic_write_json(trace_path, trace)
    trace["tracePath"] = trace_path.relative_to(repo_root).as_posix()
    return trace


def render_chapter_brand_voice(
    repo_root: Path,
    config: BookConfig,
    chapters: list[int],
    *,
    force: bool = False,
    model_factory: ModelFactory = _default_model_factory,
) -> dict[str, Any]:
    try:
        require_approved_voice(config)
    except ConfigError as exc:
        raise BrandVoiceError(str(exc)) from exc
    if not chapters or any(chapter < 1 or chapter > config.chapter_count for chapter in chapters):
        raise BrandVoiceError("Chapter selection is empty or outside the configured book")
    profile = resolve_voice_profile(str(config.voice["profileId"]))
    reference_path = config.repo_path(repo_root, str(config.voice["referencePath"]))
    if sha256_file(reference_path) != config.voice["referenceSha256"]:
        raise BrandVoiceError("Voice reference SHA-256 does not match the book config")

    device = str(config.render.get("device", "cuda"))
    target_rate = int(config.render["sampleRate"])
    lead_silence = float(config.branding.get("voiceLeadSilenceSec", 0.16))
    tail_silence = float(config.branding.get("voiceTailSilenceSec", 0.42))
    settings = {
        "intro": (
            float(config.branding.get("voiceCfgValue", config.voice["cfgValue"])),
            int(config.branding.get("voiceInferenceTimesteps", config.voice["inferenceTimesteps"])),
        ),
        "outro": (
            float(config.branding.get("outroVoiceCfgValue", config.branding.get("voiceCfgValue", config.voice["cfgValue"]))),
            int(config.branding.get("outroVoiceInferenceTimesteps", config.branding.get("voiceInferenceTimesteps", config.voice["inferenceTimesteps"]))),
        ),
    }
    jobs: list[tuple[int, str, str, Path]] = []
    for chapter in chapters:
        current = _chapter_word(chapter)
        following = _chapter_word(chapter + 1) if chapter < config.chapter_count else "the final chapter"
        jobs.extend(
            [
                (
                    chapter,
                    "intro",
                    f"Welcome to Classic Listening, from the English Listening Room. {config.title}, by {config.author}. Chapter {current}.",
                    repo_root / "public" / "classics" / config.slug / "branding" / f"chapter-{chapter:02d}-intro.wav",
                ),
                (
                    chapter,
                    "outro",
                    f"Thank you for listening. Subscribe to the English Listening Room, and continue with Chapter {following} of {config.title}.",
                    repo_root / "public" / "classics" / config.slug / "branding" / f"chapter-{chapter:02d}-outro.wav",
                ),
            ]
        )

    if model_factory is _default_model_factory:
        provider_id = resolve_provider_config(repo_root, config.render).provider_id
        provider_jobs = []
        for chapter, kind, text, output_path in jobs:
            cfg_value, timesteps = settings[kind]
            provider_jobs.append(
                {
                    "id": f"chapter-{chapter:02d}-{kind}",
                    "kind": kind,
                    "text": text,
                    "outputPath": output_path,
                    "metadata": {"chapter": chapter},
                    "providerSettings": (
                        {"cfgValue": cfg_value, "inferenceTimesteps": timesteps}
                        if provider_id == "voxcpm"
                        else {}
                    ),
                }
            )
        return _render_provider_brand_jobs(
            repo_root,
            config,
            profile,
            reference_path,
            provider_jobs,
            force=force,
            trace_path=repo_root
            / "workspace"
            / "classics"
            / config.slug
            / "branding"
            / "chapter-brand-voice-render.json",
            trace_schema="classic-listening-chapter-brand-voice-v1",
        )

    model_path = config.runtime_path(repo_root, str(config.render["modelId"]))
    model = model_factory(str(model_path), device)
    model_rate = int(model.tts_model.sample_rate)
    rendered: list[dict[str, Any]] = []
    for chapter, kind, text, output_path in jobs:
        cfg_value, timesteps = settings[kind]
        reused = output_path.is_file() and not force
        if reused:
            import soundfile as sf

            audio, existing_rate = sf.read(output_path, dtype="float32")
            audio = _mono_float(audio)
            if int(existing_rate) != target_rate:
                raise BrandVoiceError(f"Existing chapter brand voice has wrong sample rate: {output_path}")
        else:
            generated = model.generate(
                text=text,
                prompt_wav_path=str(reference_path),
                prompt_text=profile.prompt_text,
                reference_wav_path=str(reference_path),
                cfg_value=cfg_value,
                inference_timesteps=timesteps,
                normalize=bool(config.voice.get("normalize", False)),
                denoise=bool(config.voice.get("denoise", False)),
            )
            speech = _resample(_mono_float(generated), model_rate, target_rate)
            peak = float(np.max(np.abs(speech)))
            if peak > 0.89:
                speech = speech * (0.89 / peak)
            audio = np.concatenate(
                (
                    np.zeros(round(target_rate * lead_silence), dtype=np.float32),
                    speech,
                    np.zeros(round(target_rate * tail_silence), dtype=np.float32),
                )
            )
            _atomic_write_wav(output_path, audio, target_rate)
        rendered.append(
            {
                "chapter": chapter,
                "kind": kind,
                "text": text,
                "path": output_path.relative_to(repo_root).as_posix(),
                "sha256": sha256_file(output_path),
                "durationSec": round(float(len(audio) / target_rate), 3),
                "reused": reused,
                "generationSettings": {"cfgValue": cfg_value, "inferenceTimesteps": timesteps},
            }
        )

    trace_path = repo_root / "workspace" / "classics" / config.slug / "branding" / "chapter-brand-voice-render.json"
    trace = {
        "schema": "classic-listening-chapter-brand-voice-v1",
        "bookSlug": config.slug,
        "renderedAt": datetime.now(timezone.utc).isoformat(),
        "voiceProfile": profile.to_trace(),
        "referenceSha256": sha256_file(reference_path),
        "modelPath": str(model_path),
        "clips": rendered,
    }
    atomic_write_json(trace_path, trace)
    trace["tracePath"] = trace_path.relative_to(repo_root).as_posix()
    return trace
