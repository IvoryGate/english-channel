"""Adapt existing TTS identity contracts without loading a synthesis model."""
from __future__ import annotations

from pathlib import Path

from worker.tts.dialogue import dialogue_turn_spec


def voice_identity(provider: dict, voice: dict) -> dict:
    return {**{key: provider[key] for key in
        ("providerId", "modelId", "modelRevision", "localModelPath", "providerSettings")},
        "runtimeMode": provider.get("runtimeMode", "default"), "voice": voice}


def manifest_voice_identities(root: Path, manifest: dict) -> dict[str, dict]:
    result = {}
    for turn in manifest["turns"]:
        spec = dialogue_turn_spec(root, manifest, turn)
        identity = voice_identity({**spec["provider"].to_trace(root),
            "providerSettings": spec["effectiveSettings"]}, spec["voice"])
        speaker = turn["speaker"]
        if speaker in result and result[speaker] != identity:
            raise ValueError("Per-speaker voice settings vary; accept each variant before expanding this handoff")
        result[speaker] = identity
    if not result:
        raise ValueError("Production manifest has no spoken turns")
    return result
