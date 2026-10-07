from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROVIDER_REVISIONS = {
    "kokoro": "f3ff3571791e39611d31c381e3a41a3af07b4987",
    "chatterbox_500m": "5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18",
}

PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "kokoro": {
        "modelId": "hexgrad/Kokoro-82M",
        "device": "cpu",
        "interpreter": "workspace/runtime/tts-audition/kokoro-env/Scripts/python.exe",
        "localModelPath": "workspace/runtime/tts-audition/cache/huggingface/hub",
        "providerSettings": {"languageCode": "a", "speed": 0.95},
    },
    "chatterbox_500m": {
        "modelId": "resemble-ai/chatterbox",
        "device": "cuda",
        "interpreter": "workspace/runtime/tts-audition/chatterbox-env/Scripts/python.exe",
        "localModelPath": "workspace/runtime/tts-audition/models/chatterbox-500m",
        "providerSettings": {
            "exaggeration": 0.5,
            "cfgWeight": 0.5,
            "temperature": 0.8,
            "topP": 1.0,
            "minP": 0.05,
            "repetitionPenalty": 1.2,
        },
    },
    "voxcpm": {
        "modelId": "pretrained_models/VoxCPM2",
        "device": "cuda",
        "interpreter": ".conda-env/python.exe",
        "localModelPath": "pretrained_models/VoxCPM2",
        "providerSettings": {"cfgValue": 2.35, "inferenceTimesteps": 10},
    },
}


class ProviderConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderConfig:
    provider_id: str
    model_id: str
    model_revision: str
    device: str
    interpreter: Path
    local_model_path: Path
    seed_base: int
    settings: dict[str, Any]

    @property
    def uses_gpu(self) -> bool:
        return self.device.lower().startswith("cuda")

    def to_trace(self, repo_root: Path) -> dict[str, Any]:
        return {
            "providerId": self.provider_id,
            "modelId": self.model_id,
            "modelRevision": self.model_revision,
            "device": self.device,
            "interpreter": self.interpreter.relative_to(repo_root.resolve()).as_posix(),
            "localModelPath": self.local_model_path.relative_to(repo_root.resolve()).as_posix(),
            "seedBase": self.seed_base,
            "outputFormat": {"container": "wav", "sampleType": "float32"},
            "providerSettings": dict(self.settings),
        }


def _project_path(repo_root: Path, value: str, field: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ProviderConfigError(f"{field} must be project-relative: {value}")
    return (repo_root.resolve() / relative).resolve()


def _number(settings: dict[str, Any], key: str, *, minimum: float = 0.0) -> float:
    value = settings.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or float(value) <= minimum:
        raise ProviderConfigError(f"providerSettings.{key} must be greater than {minimum}")
    return float(value)


def _validate_settings(provider_id: str, settings: dict[str, Any]) -> None:
    if provider_id == "kokoro":
        language = settings.get("languageCode")
        if not isinstance(language, str) or not language.strip():
            raise ProviderConfigError("providerSettings.languageCode is required for Kokoro")
        _number(settings, "speed")
    elif provider_id == "chatterbox_500m":
        for key in ("exaggeration", "cfgWeight", "temperature", "topP", "minP", "repetitionPenalty"):
            _number(settings, key, minimum=-1e-12)
    elif provider_id == "chatterbox_turbo":
        unsupported = sorted({"exaggeration", "cfgWeight", "minP"} & set(settings))
        if unsupported:
            raise ProviderConfigError(
                "Chatterbox Turbo does not support these settings: " + ", ".join(unsupported)
            )
        raise ProviderConfigError("Chatterbox Turbo is internal-only during week one")
    elif provider_id == "voxcpm":
        _number(settings, "cfgValue")
        if not isinstance(settings.get("inferenceTimesteps"), int) or settings["inferenceTimesteps"] < 1:
            raise ProviderConfigError("providerSettings.inferenceTimesteps must be a positive integer")


def resolve_provider_config(repo_root: Path, render_settings: dict[str, Any]) -> ProviderConfig:
    provider_id = str(render_settings.get("ttsProvider") or "voxcpm")
    if provider_id not in {*PROVIDER_DEFAULTS, "chatterbox_turbo"}:
        raise ProviderConfigError(f"Unsupported TTS provider: {provider_id}")
    defaults = PROVIDER_DEFAULTS.get(provider_id, {})
    model_id = str(render_settings.get("modelId") or defaults.get("modelId") or "").strip()
    revision = str(render_settings.get("modelRevision") or "legacy-local").strip()
    if provider_id in PROVIDER_REVISIONS and revision != PROVIDER_REVISIONS[provider_id]:
        raise ProviderConfigError(
            f"{provider_id} must use pinned revision {PROVIDER_REVISIONS[provider_id]}"
        )
    device = str(render_settings.get("device") or defaults.get("device") or "cpu").strip()
    interpreter_value = str(render_settings.get("providerPython") or defaults.get("interpreter") or "")
    model_path_value = str(render_settings.get("localModelPath") or defaults.get("localModelPath") or "")
    seed_base = render_settings.get("seedBase", 20260914)
    if not isinstance(seed_base, int) or isinstance(seed_base, bool) or seed_base < 0:
        raise ProviderConfigError("renderSettings.seedBase must be a non-negative integer")
    settings = {**dict(defaults.get("providerSettings") or {}), **dict(render_settings.get("providerSettings") or {})}
    if provider_id == "voxcpm":
        settings["cfgValue"] = float(render_settings.get("cfgValue", settings["cfgValue"]))
        settings["inferenceTimesteps"] = int(
            render_settings.get("inferenceTimesteps", settings["inferenceTimesteps"])
        )
    _validate_settings(provider_id, settings)
    return ProviderConfig(
        provider_id=provider_id,
        model_id=model_id,
        model_revision=revision,
        device=device,
        interpreter=_project_path(repo_root, interpreter_value, "providerPython"),
        local_model_path=_project_path(repo_root, model_path_value, "localModelPath"),
        seed_base=seed_base,
        settings=settings,
    )


def validate_voice(provider_id: str, voice: dict[str, Any]) -> dict[str, Any]:
    kind = str(voice.get("kind") or "")
    if provider_id == "kokoro":
        if kind != "preset" or not str(voice.get("voiceId") or "").strip():
            raise ProviderConfigError("Kokoro hosts require a preset voiceId")
        return {"kind": "preset", "voiceId": str(voice["voiceId"])}
    if provider_id in {"chatterbox_500m", "voxcpm"}:
        path = str(voice.get("referencePath") or "").strip()
        digest = str(voice.get("referenceSha256") or "").lower()
        if kind != "clone" or not path or len(digest) != 64:
            raise ProviderConfigError(f"{provider_id} hosts require clone referencePath and SHA-256")
        return {"kind": "clone", "referencePath": path, "referenceSha256": digest}
    raise ProviderConfigError(f"Unsupported voice provider: {provider_id}")
