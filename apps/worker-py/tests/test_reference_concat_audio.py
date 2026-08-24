from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "workspace" / "shows" / "tools"))

from prepare_reference_concat_audio import build_concat_audio  # noqa: E402


def test_large_concat_uses_manifest_instead_of_clip_command_arguments(tmp_path: Path, monkeypatch) -> None:
    clips: list[Path] = []
    for index in range(150):
        clip = tmp_path / f"turn_{index:03d}_with_a_deliberately_long_filename_for_windows.wav"
        clip.write_bytes(b"wav")
        clips.append(clip)

    commands: list[list[str]] = []
    concat_manifest = ""

    def capture(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        nonlocal concat_manifest
        assert check is True
        commands.append(command)
        if "concat" in command:
            concat_manifest = Path(command[command.index("-i") + 1]).read_text(encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", capture)

    output = build_concat_audio(clips, tmp_path / "episode.raw.wav", gap_sec=0.3)

    assert output == tmp_path / "episode.raw.wav"
    assert len(commands) == 2
    assert len(subprocess.list2cmdline(commands[-1])) < 2048
    assert concat_manifest.count("file '") == 299
    assert clips[-1].resolve().as_posix() in concat_manifest
