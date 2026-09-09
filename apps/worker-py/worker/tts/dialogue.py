from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import ProviderConfig, ProviderConfigError, resolve_provider_config, validate_voice
from .trace import build_turn_identity, normalized_text, sha256_file, trace_is_reusable


def dialogue_voice(
    repo_root: Path,
    manifest: dict[str, Any],
    provider: ProviderConfig,
    speaker: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    host = dict(manifest["hosts"][speaker])
    configured = host.get("voice")
    if configured is None and provider.provider_id in {"chatterbox_500m", "voxcpm"}:
        reference = str(host.get("referenceAudioClean") or "")
        path = (repo_root / reference).resolve()
        if not path.is_file():
            raise ProviderConfigError(f"Reference audio not found for {speaker}: {path}")
        configured = {
            "kind": "clone",
            "referencePath": reference,
            "referenceSha256": sha256_file(path),
        }
    voice = validate_voice(provider.provider_id, dict(configured or {}))
    worker_voice = dict(voice)
    if voice["kind"] == "clone":
        path = (repo_root / str(voice["referencePath"])).resolve()
        if not path.is_file():
            raise ProviderConfigError(f"Reference audio not found for {speaker}: {path}")
        actual = sha256_file(path)
        if actual != voice["referenceSha256"]:
            raise ProviderConfigError(f"Reference SHA-256 mismatch for {speaker}")
        worker_voice["referencePath"] = str(path)
    return voice, worker_voice


def dialogue_turn_spec(
    repo_root: Path,
    manifest: dict[str, Any],
    turn: dict[str, Any],
) -> dict[str, Any]:
    provider = resolve_provider_config(repo_root, dict(manifest["renderSettings"]))
    speaker = str(turn["speaker"])
    voice, worker_voice = dialogue_voice(repo_root, manifest, provider, speaker)
    seed_offset = turn.get("ttsSeedOffset", 0)
    if not isinstance(seed_offset, int) or isinstance(seed_offset, bool):
        raise ProviderConfigError("turn.ttsSeedOffset must be an integer")
    seed = provider.seed_base + int(turn["order"]) + seed_offset
    identity = build_turn_identity(
        provider=provider.to_trace(repo_root),
        voice=voice,
        text=str(turn["text"]),
        seed=seed,
    )
    return {
        "provider": provider,
        "voice": voice,
        "workerVoice": worker_voice,
        "seed": seed,
        "normalizedText": normalized_text(str(turn["text"])),
        "identity": identity,
    }


def dialogue_turn_is_reusable(
    repo_root: Path,
    manifest: dict[str, Any],
    turn: dict[str, Any],
    output: Path,
) -> bool:
    spec = dialogue_turn_spec(repo_root, manifest, turn)
    return trace_is_reusable(output, str(spec["identity"]["sha256"]))
