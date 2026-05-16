from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    display_name: str
    description: str
    prompt_text: str | None = None
    prompt_wav_path: str | None = None
    reference_wav_path: str | None = None
    cfg_value: float = 2.0
    inference_timesteps: int = 10
    normalize: bool = True
    denoise: bool = False

    def usable_prompt_wav_path(self) -> str | None:
        return _existing_file(self.prompt_wav_path)

    def usable_reference_wav_path(self) -> str | None:
        return _existing_file(self.reference_wav_path)

    def to_trace(self) -> dict[str, object]:
        return {
            "id": self.id,
            "displayName": self.display_name,
            "description": self.description,
            "promptText": self.prompt_text,
            "promptWavPath": self.prompt_wav_path,
            "promptWavAvailable": self.usable_prompt_wav_path() is not None,
            "referenceWavPath": self.reference_wav_path,
            "referenceWavAvailable": self.usable_reference_wav_path() is not None,
            "cfgValue": self.cfg_value,
            "inferenceTimesteps": self.inference_timesteps,
            "normalize": self.normalize,
            "denoise": self.denoise,
        }


PRIDE_PREJUDICE_REGENCY_NARRATOR = VoiceProfile(
    id="pride-prejudice-regency-narrator",
    display_name="Regency Drawing-Room Narrator",
    description=(
        "A poised adult British narrator for Jane Austen: warm, articulate, lightly ironic, "
        "and restrained enough for long-form listening. The voice should suggest a cultivated "
        "drawing-room reader rather than a theatrical character performance."
    ),
    prompt_text=(
        "It is a truth universally acknowledged, that a single man in possession of a good "
        "fortune, must be in want of a wife. However little known the feelings or views of such "
        "a man may be on his first entering a neighbourhood, this truth is so well fixed in the "
        "minds of the surrounding families, that he is considered the rightful property of some "
        "one or other of their daughters."
    ),
    prompt_wav_path="assets/voices/pride-prejudice-regency-narrator/prompt.wav",
    reference_wav_path="assets/voices/pride-prejudice-regency-narrator/reference.wav",
    cfg_value=2.15,
    inference_timesteps=12,
    normalize=False,
    denoise=False,
)

DEFAULT_VOICE_PROFILE = VoiceProfile(
    id="default-narrator",
    display_name="Default Narrator",
    description="The model default voice with repository baseline generation settings.",
)

VOICE_PROFILES = {
    DEFAULT_VOICE_PROFILE.id: DEFAULT_VOICE_PROFILE,
    "default-english-narrator": DEFAULT_VOICE_PROFILE,
    PRIDE_PREJUDICE_REGENCY_NARRATOR.id: PRIDE_PREJUDICE_REGENCY_NARRATOR,
}


def resolve_voice_profile(profile_id: str | None) -> VoiceProfile:
    if not profile_id:
        return DEFAULT_VOICE_PROFILE
    return VOICE_PROFILES.get(profile_id, DEFAULT_VOICE_PROFILE)


def _existing_file(path: str | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    return str(candidate) if candidate.is_file() else None
