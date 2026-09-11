from __future__ import annotations

import subprocess

import pytest

from worker.shorts.render import _run_quiet


def test_run_quiet_captures_success_output(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="progress", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    _run_quiet(["remotion", "render"])

    assert observed["capture_output"] is True
    assert observed["check"] is False


def test_run_quiet_reports_only_failure_tail(monkeypatch: pytest.MonkeyPatch) -> None:
    stderr = "\n".join(f"line {index}" for index in range(50))
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 1, stdout="", stderr=stderr),
    )

    with pytest.raises(RuntimeError) as error:
        _run_quiet(["remotion", "render"])

    assert "line 10" in str(error.value)
    assert "line 9" not in str(error.value)
    assert "line 49" in str(error.value)
