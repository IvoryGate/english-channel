from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS = REPO_ROOT / "workspace" / "shows" / "tools"
sys.path.insert(0, str(TOOLS))

from master_episode_audio import per_turn_filter  # noqa: E402
from episode_artifacts import artifact_paths, resolve_episode_audio  # noqa: E402


def test_per_turn_filter_includes_speech_chain() -> None:
    filt = per_turn_filter(denoise_nr=6.0, denoise_nf=-25.0)
    assert "highpass=f=80" in filt
    assert "afftdn=nr=6.0" in filt
    assert "acompressor=" in filt
    assert "alimiter=" in filt
    assert "channel_layouts=mono" in filt


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
