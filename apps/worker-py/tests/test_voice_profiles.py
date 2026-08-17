from worker.voice_profiles import (
    ELR_SERIES_A_ETHAN,
    ELR_SERIES_A_NORA,
    PRIDE_PREJUDICE_REGENCY_NARRATOR,
    resolve_voice_profile,
)


def test_resolves_pride_prejudice_profile() -> None:
    profile = resolve_voice_profile("pride-prejudice-regency-narrator")

    assert profile.id == PRIDE_PREJUDICE_REGENCY_NARRATOR.id
    assert "Jane Austen" in profile.description
    assert profile.cfg_value > 2.0
    assert profile.inference_timesteps >= 10
    assert profile.prompt_text is not None
    assert "truth universally acknowledged" in profile.prompt_text


def test_unknown_profile_falls_back_to_default() -> None:
    profile = resolve_voice_profile("missing-profile")

    assert profile.id == "default-narrator"


def test_series_a_profiles_use_the_matching_host_reference_audio() -> None:
    assert ELR_SERIES_A_ETHAN.prompt_wav_path.endswith("ethan_reference_clean.wav")
    assert ELR_SERIES_A_ETHAN.reference_wav_path.endswith("ethan_reference_clean.wav")
    assert ELR_SERIES_A_NORA.prompt_wav_path.endswith("nora_reference_clean.wav")
    assert ELR_SERIES_A_NORA.reference_wav_path.endswith("nora_reference_clean.wav")
