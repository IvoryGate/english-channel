from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "workspace" / "shows" / "tools"))

import elr  # noqa: E402
import elr_run_state  # noqa: E402
import monitor_episode_render  # noqa: E402
from elr import audio_render_command, command_status, monitor_command  # noqa: E402
from elr_production import build_context  # noqa: E402
from elr_run_state import RunStateStore  # noqa: E402


def test_monitor_command_uses_only_canonical_workspace_and_batch_20(tmp_path: Path) -> None:
    context = build_context(tmp_path, "series_c", 17, tmp_path / "youtube")
    cmd = monitor_command(
        context,
        Path("python.exe"),
        batch_size=20,
        force=False,
        log_path=tmp_path / "run.log",
    )
    assert str(context.workspace) in cmd
    assert cmd[cmd.index("--batch-size") + 1] == "20"
    assert cmd[cmd.index("--episode-num") + 1] == "17"
    assert "--force" not in cmd


def test_monitor_command_can_skip_external_export(tmp_path: Path) -> None:
    context = build_context(tmp_path, "series_b", 20, tmp_path / "youtube")
    cmd = monitor_command(
        context,
        Path("python.exe"),
        batch_size=20,
        force=False,
        log_path=tmp_path / "run.log",
        skip_export=True,
    )

    assert "--skip-export" in cmd
    assert "--youtube-root" in cmd


def test_audio_render_command_defers_compose_and_visual_pack(tmp_path: Path) -> None:
    context = build_context(tmp_path, "series_a", 17, tmp_path / "youtube")
    cmd = audio_render_command(
        context,
        Path("python.exe"),
        batch_size=20,
        force=False,
        log_path=tmp_path / "audio.log",
    )

    assert str(context.workspace / "000_episode_017.episode_manifest.json") in cmd
    assert cmd[cmd.index("--batch-size") + 1] == "20"
    assert "--turns-only" in cmd
    assert "--force" not in cmd


def test_turns_only_monitor_skips_compose_and_qc(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "000_episode_017.episode_manifest.json"
    manifest.write_text('{"renderSettings": {}, "turns": []}\n', encoding="utf-8")
    messages: list[str] = []

    class Logger:
        def log(self, message: str) -> None:
            messages.append(message)

    def unexpected_compose(**_kwargs: object) -> int:
        raise AssertionError("compose_and_qc must be deferred in turns-only mode")

    monkeypatch.setattr(monitor_episode_render, "compose_and_qc", unexpected_compose)
    result = monitor_episode_render.monitor_render(
        manifest_path=manifest,
        python=Path("python.exe"),
        device="cuda",
        logger=Logger(),
        batch_size=20,
        force=False,
        retry_on_failure=0,
        cfg=2.35,
        no_self_check=True,
        turns_only=True,
    )

    assert result == 0
    assert any("deferred to formal production" in message for message in messages)


def test_run_state_write_and_update_are_atomic(tmp_path: Path) -> None:
    path = tmp_path / "episode_017.json"
    store = RunStateStore(path)
    store.write({"episodeId": "episode_017", "status": "RUNNING", "phase": "PREPARE"})
    store.update(phase="PREFLIGHT", detail="checking assets")

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["schema"] == "elr-production-run-v1"
    assert saved["phase"] == "PREFLIGHT"
    assert saved["detail"] == "checking assets"
    assert saved["heartbeatAt"]
    assert list(tmp_path.glob("*.tmp")) == []


def test_run_state_retries_transient_windows_replace_lock(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "episode_017.json"
    store = RunStateStore(path)
    real_replace = elr_run_state.os.replace
    attempts = 0

    def flaky_replace(source: Path, destination: Path) -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise PermissionError("destination temporarily locked")
        real_replace(source, destination)

    monkeypatch.setattr(elr_run_state.os, "replace", flaky_replace)
    monkeypatch.setattr(elr_run_state.time, "sleep", lambda _seconds: None)

    store.write({"episodeId": "episode_017", "status": "RUNNING"})

    assert attempts == 3
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "RUNNING"


def test_status_reads_durable_state_without_process_scan(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(elr, "REPO", tmp_path)
    store = RunStateStore(tmp_path / "logs" / "elr_runs" / "episode_017.json")
    store.write(
        {
            "episodeId": "episode_017",
            "status": "DONE",
            "phase": "DONE",
            "pid": -1,
            "logPath": str(tmp_path / "run.log"),
            "seriesState": {"series_a": {"status": "DONE", "phase": "DONE"}},
        }
    )

    code = command_status(Namespace(episode="17", json=False))

    assert code == 0
    output = capsys.readouterr().out
    assert "status=DONE" in output
    assert "series_a: status=DONE phase=DONE" in output
