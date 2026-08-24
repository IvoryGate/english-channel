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

ELR_SERIES_A_ETHAN = VoiceProfile(
    id="elr-series-a-ethan",
    display_name="ELR Series A — Ethan",
    description="Warm male daily-talk host for ELR Series A (B1-B2).",
    prompt_text=(
        "There's something really beautiful about knowing that people from different places, "
        "different lives, and different stories are all meeting here through English."
    ),
    prompt_wav_path="assets/voices/series_a/ethan_reference_clean.wav",
    reference_wav_path="assets/voices/series_a/ethan_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

ELR_SERIES_A_NORA = VoiceProfile(
    id="elr-series-a-nora",
    display_name="ELR Series A — Nora",
    description="Warm female daily-talk host for ELR Series A (B1-B2).",
    prompt_text=(
        "It really does, because every time you listen, every time you leave a comment, "
        "every time you share your thoughts with us, it makes this space feel more real, "
        "more alive, and more special."
    ),
    prompt_wav_path="assets/voices/series_a/nora_reference_clean.wav",
    reference_wav_path="assets/voices/series_a/nora_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

ELR_SERIES_B_SAM = VoiceProfile(
    id="elr-series-b-sam",
    display_name="ELR Series B — Sam",
    description="Male co-learner friend host for ELR Series B (A2-B1).",
    prompt_text=(
        "Okay, I need this, I seriously need this because every time I open a grammar book "
        "I see things like future perfect continuous and I just close the book."
    ),
    prompt_wav_path="assets/voices/series_b/sam_reference_clean.wav",
    reference_wav_path="assets/voices/series_b/sam_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

ELR_SERIES_B_RILEY = VoiceProfile(
    id="elr-series-b-riley",
    display_name="ELR Series B — Riley",
    description="Female teacher host for ELR Series B (A2-B1).",
    prompt_text=(
        "Today, I want to show you exactly how to use just 15 minutes a day "
        "to practice your English, alone, at home, anywhere you are."
    ),
    prompt_wav_path="assets/voices/series_b/riley_reference_clean.wav",
    reference_wav_path="assets/voices/series_b/riley_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

CLASSIC_LISTENING_RILEY_NARRATOR = VoiceProfile(
    id="classic-listening-riley-narrator",
    display_name="Classic Listening — Riley Narrator",
    description=(
        "The established ELR Series B Riley timbre adapted for long-form public-domain "
        "literature: one poised female narrator, reflective and intimate, with restrained "
        "Regency-era emotion and no character-voice imitation."
    ),
    prompt_text=(
        "Today, I want to show you exactly how to use just 15 minutes a day "
        "to practice your English, alone, at home, anywhere you are."
    ),
    prompt_wav_path="assets/voices/series_b/riley_reference_clean.wav",
    reference_wav_path="assets/voices/series_b/riley_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

ELR_SERIES_C_LEO = VoiceProfile(
    id="elr-series-c-leo",
    display_name="ELR Series C — Leo",
    description="Male facilitator host for ELR Series C / Polished English (B2-C1).",
    prompt_text=(
        "Neither did I. I found myself lying prone upon a bed of yellowish moss-like "
        "vegetation, which stretched around me in all directions for interminable miles. "
        "I seemed to be lying in a deep"
    ),
    prompt_wav_path="workspace/dialogue_podcast_research/voices/leo/leo_reference_clean.wav",
    reference_wav_path="workspace/dialogue_podcast_research/voices/leo/leo_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

ELR_SERIES_C_MIA = VoiceProfile(
    id="elr-series-c-mia",
    display_name="ELR Series C — Mia",
    description="Female listener-voice host for ELR Series C / Polished English (B2-C1).",
    prompt_text=(
        "Being because it is no business of mine to look gruff and fight battles, Emily "
        "endeavoured to correct the superstitious weakness of Annette, though she could "
        "not entirely subdue her own, to which the latter only replied"
    ),
    prompt_wav_path="workspace/dialogue_podcast_research/voices/mia/mia_reference_clean.wav",
    reference_wav_path="workspace/dialogue_podcast_research/voices/mia/mia_reference_clean.wav",
    cfg_value=2.35,
    inference_timesteps=10,
    normalize=False,
    denoise=False,
)

VOICE_PROFILES = {
    DEFAULT_VOICE_PROFILE.id: DEFAULT_VOICE_PROFILE,
    "default-english-narrator": DEFAULT_VOICE_PROFILE,
    PRIDE_PREJUDICE_REGENCY_NARRATOR.id: PRIDE_PREJUDICE_REGENCY_NARRATOR,
    ELR_SERIES_A_ETHAN.id: ELR_SERIES_A_ETHAN,
    ELR_SERIES_A_NORA.id: ELR_SERIES_A_NORA,
    ELR_SERIES_B_SAM.id: ELR_SERIES_B_SAM,
    ELR_SERIES_B_RILEY.id: ELR_SERIES_B_RILEY,
    CLASSIC_LISTENING_RILEY_NARRATOR.id: CLASSIC_LISTENING_RILEY_NARRATOR,
    ELR_SERIES_C_LEO.id: ELR_SERIES_C_LEO,
    ELR_SERIES_C_MIA.id: ELR_SERIES_C_MIA,
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
