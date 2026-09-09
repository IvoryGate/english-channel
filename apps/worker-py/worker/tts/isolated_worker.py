from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.metadata
import json
import os
import sys
import tempfile
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
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


def atomic_wav(path: Path, audio: Any, sample_rate: int) -> None:
    import numpy as np
    import soundfile as sf

    value = np.asarray(audio, dtype=np.float32).reshape(-1)
    if value.size == 0 or not np.isfinite(value).all():
        raise RuntimeError("Provider returned empty or non-finite audio")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".wav", dir=path.parent)
    os.close(fd)
    try:
        # Keep provider output as float audio. Downstream mastering owns the
        # delivery encoding and can then resample/quantize exactly once.
        sf.write(temp_name, value, sample_rate, subtype="FLOAT")
        os.replace(temp_name, path)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


class Engine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.provider_id = str(config["providerId"])
        self.device = str(config["device"])
        self.settings = dict(config["providerSettings"])
        self.model_path = Path(str(config["localModelPath"]))
        self.model: Any = None
        self.sample_rate = 0
        self.package_version = "unknown"

    def load(self) -> None:
        if self.provider_id == "kokoro":
            from kokoro import KPipeline

            self.model = KPipeline(
                lang_code=str(self.settings["languageCode"]),
                device=self.device,
                repo_id=str(self.config["modelId"]),
            )
            self.sample_rate = 24_000
            self.package_version = importlib.metadata.version("kokoro")
        elif self.provider_id == "chatterbox_500m":
            from chatterbox.tts import ChatterboxTTS

            self.model = ChatterboxTTS.from_local(self.model_path, device=self.device)
            self.sample_rate = int(self.model.sr)
            self.package_version = importlib.metadata.version("chatterbox-tts")
        elif self.provider_id == "voxcpm":
            repo_root = Path(str(self.config["repoRoot"]))
            sys.path.insert(0, str(repo_root / "apps" / "worker-py"))
            from worker.classics.voxcpm_memory import patch_voxcpm_low_memory_load

            patch_voxcpm_low_memory_load()
            from voxcpm import VoxCPM

            self.model = VoxCPM.from_pretrained(
                str(self.model_path),
                device=self.device,
                optimize=True,
                load_denoiser=False,
                local_files_only=True,
            )
            self.sample_rate = int(self.model.tts_model.sample_rate)
            self.package_version = importlib.metadata.version("voxcpm")
        else:
            raise RuntimeError(f"Unsupported provider: {self.provider_id}")

    def generate(self, turn: dict[str, Any]) -> Any:
        import numpy as np
        import torch

        seed = int(turn["seed"])
        np.random.seed(seed % (2**32))
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        text = str(turn["text"])
        voice = dict(turn["voice"])
        settings = {**self.settings, **dict(turn.get("providerSettings") or {})}
        if self.provider_id == "kokoro":
            chunks = [
                row.audio.detach().cpu().numpy()
                for row in self.model(
                    text,
                    voice=str(voice["voiceId"]),
                    speed=float(settings["speed"]),
                )
            ]
            if not chunks:
                raise RuntimeError("Kokoro returned no audio chunks")
            return np.concatenate(chunks)
        if self.provider_id == "chatterbox_500m":
            return self.model.generate(
                text,
                audio_prompt_path=str(voice["referencePath"]),
                exaggeration=float(settings["exaggeration"]),
                cfg_weight=float(settings["cfgWeight"]),
                temperature=float(settings["temperature"]),
                top_p=float(settings["topP"]),
                min_p=float(settings["minP"]),
                repetition_penalty=float(settings["repetitionPenalty"]),
            ).detach().cpu().numpy().reshape(-1)
        kwargs: dict[str, Any] = {
            "text": text,
            "prompt_wav_path": str(voice["referencePath"]),
            "prompt_text": str(turn.get("referenceText") or ""),
            "reference_wav_path": str(voice["referencePath"]),
            "cfg_value": float(settings["cfgValue"]),
            "inference_timesteps": int(settings["inferenceTimesteps"]),
            "normalize": False,
            "denoise": False,
        }
        if turn.get("maxLen") is not None:
            kwargs["max_len"] = int(turn["maxLen"])
        return self.model.generate(**kwargs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    args = parser.parse_args()
    request_path = Path(args.request)
    response_path = Path(args.response)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    repo_root = Path(request["repoRoot"])
    provider = dict(request["provider"])
    provider["repoRoot"] = str(repo_root)
    uses_gpu = str(provider["device"]).lower().startswith("cuda")
    sys.path.insert(0, str(repo_root / "scripts"))
    from gpu_production_lock import GpuProductionLock

    context = GpuProductionLock(str(request["label"])) if uses_gpu else nullcontext()
    response: dict[str, Any] = {"status": "error", "turns": []}
    try:
        with context:
            engine = Engine(provider)
            load_started = time.perf_counter()
            engine.load()
            load_seconds = time.perf_counter() - load_started
            for turn in request["turns"]:
                started = time.perf_counter()
                audio = engine.generate(turn)
                generation_seconds = time.perf_counter() - started
                import numpy as np

                value = np.asarray(audio, dtype=np.float32).reshape(-1)
                output = Path(turn["outputPath"])
                atomic_wav(output, value, engine.sample_rate)
                response["turns"].append(
                    {
                        "id": str(turn["id"]),
                        "sampleRate": engine.sample_rate,
                        "durationSec": round(float(value.size / engine.sample_rate), 3),
                        "generationSec": round(generation_seconds, 3),
                        "peak": round(float(np.max(np.abs(value))), 6),
                        "outputSha256": sha256_file(output),
                        "packageVersion": engine.package_version,
                        "modelLoadSec": round(load_seconds, 3),
                        "watermark": (
                            {"provider": "PerTh", "status": "implicit-enabled"}
                            if provider["providerId"] == "chatterbox_500m"
                            else {"status": "not-applicable"}
                        ),
                    }
                )
                del audio, value
                gc.collect()
                try:
                    import torch

                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
            response["status"] = "ok"
    except BaseException as exc:
        response["error"] = f"{type(exc).__name__}: {exc}"
        atomic_json(response_path, response)
        raise
    atomic_json(response_path, response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
