from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS = REPO_ROOT / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from master_episode_audio import per_turn_filter, resolve_playback_tempo  # noqa: E402
from episode_artifacts import artifact_paths, resolve_episode_audio  # noqa: E402


def test_per_turn_filter_includes_speech_chain() -> None:
    filt = per_turn_filter(denoise_nr=6.0, denoise_nf=-25.0)
    assert "highpass=f=80" in filt
    assert "afftdn=nr=6.0" in filt
    assert "acompressor=" in filt
    assert "alimiter=" in filt
    assert "channel_layouts=mono" in filt


def test_per_turn_filter_applies_flagship_tempo() -> None:
    filt = per_turn_filter(denoise_nr=6.0, denoise_nf=-25.0, playback_tempo=0.9)
    assert "atempo=0.900000" in filt


def test_flagship_tempo_reaches_lower_target_without_changing_standard() -> None:
    flagship = {
        "format": "flagship_40",
        "formatContract": {"targetMinutes": [38, 42]},
    }
    tempo = resolve_playback_tempo(
        flagship,
        clip_durations_sec=[1000.0, 1000.0],
        gap_sec=0.3,
    )
    assert 0.87 < tempo < 0.89
    assert resolve_playback_tempo(
        {"format": "standard_10"},
        clip_durations_sec=[1000.0, 1000.0],
        gap_sec=0.3,
    ) == 1.0


def test_resolve_episode_audio_prefers_master(tmp_path: Path) -> None:
    ep = "episode_001"
    paths = artifact_paths(tmp_path, ep)
    paths["rawWav"].parent.mkdir(parents=True, exist_ok=True)
    paths["rawWav"].write_bytes(b"RIFF")
    assert resolve_episode_audio(tmp_path, ep) == paths["rawWav"]
    paths["masterWav"].parent.mkdir(parents=True, exist_ok=True)
    paths["masterWav"].write_bytes(b"RIFF")
    assert resolve_episode_audio(tmp_path, ep) == paths["masterWav"]
    override = tmp_path / "custom.wav"
    override.write_bytes(b"RIFF")
    assert resolve_episode_audio(tmp_path, ep, override) == override
