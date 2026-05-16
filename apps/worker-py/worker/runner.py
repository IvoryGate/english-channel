from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from voxcpm import VoxCPM

from worker.chunking import chunk_text
from worker.artifact import write_chapter_artifact
from worker.voice_profiles import resolve_voice_profile


@dataclass
class TtsRequest:
    job_id: str
    chapter_id: str
    text: str
    voice_profile: str = "default-narrator"
    cfg_value: float | None = None
    inference_timesteps: int | None = None


class VoxRunner:
    def __init__(
        self,
        model_id: str | None = None,
        output_dir: str = "artifacts",
        device: str | None = None,
        optimize: bool | None = None,
        load_denoiser: bool | None = None,
    ):
        model_id = model_id or os.getenv("VOXCPM_MODEL_ID", "pretrained_models/VoxCPM2")
        device = device or os.getenv("VOXCPM_DEVICE", "auto")
        optimize = optimize if optimize is not None else _env_bool("VOXCPM_OPTIMIZE", True)
        load_denoiser = load_denoiser if load_denoiser is not None else _env_bool("VOXCPM_LOAD_DENOISER", False)
        self.model_id = model_id
        self.output_dir = output_dir
        self.device = device
        self.optimize = optimize
        self.model = VoxCPM.from_pretrained(
            model_id,
            device=device,
            optimize=optimize,
            load_denoiser=load_denoiser,
        )

    def generate_chapter(self, request: TtsRequest) -> dict[str, Any]:
        started_at = datetime.now(timezone.utc).isoformat()
        voice_profile = resolve_voice_profile(request.voice_profile)
        cfg_value = request.cfg_value if request.cfg_value is not None else voice_profile.cfg_value
        inference_timesteps = request.inference_timesteps or voice_profile.inference_timesteps
        prompt_wav_path = voice_profile.usable_prompt_wav_path()
        prompt_text = voice_profile.prompt_text if prompt_wav_path else None
        reference_wav_path = voice_profile.usable_reference_wav_path()
        segments = chunk_text(request.text)
        waves = []
        for segment in segments:
            wav = self.model.generate(
                text=segment,
                prompt_wav_path=prompt_wav_path,
                prompt_text=prompt_text,
                reference_wav_path=reference_wav_path,
                cfg_value=cfg_value,
                inference_timesteps=inference_timesteps,
                normalize=voice_profile.normalize,
                denoise=voice_profile.denoise,
            )
            waves.append(wav)
        trace = {
            "jobId": request.job_id,
            "chapterId": request.chapter_id,
            "modelId": self.model_id,
            "device": self.device,
            "optimize": self.optimize,
            "voiceProfile": voice_profile.id,
            "requestedVoiceProfile": request.voice_profile,
            "voiceProfileSettings": voice_profile.to_trace(),
            "segmentCount": len(segments),
            "cfgValue": cfg_value,
            "inferenceTimesteps": inference_timesteps,
            "startedAt": started_at,
            "finishedAt": datetime.now(timezone.utc).isoformat(),
        }
        audio_path, trace_path = write_chapter_artifact(
            output_dir=self.output_dir,
            job_id=request.job_id,
            chapter_id=request.chapter_id,
            sample_rate=self.model.tts_model.sample_rate,
            chunks=waves,
            trace=trace,
        )
        trace["audioPath"] = audio_path
        trace["tracePath"] = trace_path
        return trace


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
