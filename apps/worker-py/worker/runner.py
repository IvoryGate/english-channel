from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from voxcpm import VoxCPM

from worker.chunking import chunk_text
from worker.artifact import write_chapter_artifact


@dataclass
class TtsRequest:
    job_id: str
    chapter_id: str
    text: str
    voice_profile: str = "default-narrator"
    cfg_value: float = 2.0
    inference_timesteps: int = 10


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
        segments = chunk_text(request.text)
        waves = []
        for segment in segments:
            wav = self.model.generate(
                text=segment,
                cfg_value=request.cfg_value,
                inference_timesteps=request.inference_timesteps,
            )
            waves.append(wav)
        trace = {
            "jobId": request.job_id,
            "chapterId": request.chapter_id,
            "modelId": self.model_id,
            "device": self.device,
            "optimize": self.optimize,
            "voiceProfile": request.voice_profile,
            "segmentCount": len(segments),
            "cfgValue": request.cfg_value,
            "inferenceTimesteps": request.inference_timesteps,
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
