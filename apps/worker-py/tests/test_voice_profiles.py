from worker.voice_profiles import (
    CLASSIC_LISTENING_RILEY_NARRATOR,
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


def test_resolves_classic_listening_riley_as_single_narrator() -> None:
    profile = resolve_voice_profile("classic-listening-riley-narrator")

    assert profile.id == CLASSIC_LISTENING_RILEY_NARRATOR.id
    assert profile.prompt_wav_path == "assets/voices/series_b/riley_reference_clean.wav"
    assert "one poised female narrator" in profile.description
    assert profile.normalize is False
    assert profile.denoise is False
