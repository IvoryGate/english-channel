from __future__ import annotations

import subprocess

import pytest

from worker.shorts.render import _run_quiet


def test_caption_pages_preserve_text_and_avoid_orphan_last_page():
    from worker.shorts.render import _caption_pages
    text = 'I am not sure when finance will confirm the number.'
    pages = _caption_pages(text)
    assert ' '.join(pages) == text
    assert len(pages[-1].split()) >= 3
    assert all(len(page) <= 42 for page in pages)


def test_caption_timing_uses_word_weight_and_keeps_turn_endpoints():
    from worker.shorts.render import build_render_props
    # Use a controller manifest shape rather than a runtime workspace.
    manifest = {'format': 'dialogue', 'cefr': 'B1', 'durationSec': 15,
        'hook': 'Listen', 'prompt': 'Which?', 'answer': 'This.',
        'promptStartSec': 11, 'answerStartSec': 13, 'cta': 'Subscribe',
        'visual': {'backgroundImage': 'test.png', 'brandLogo': 'logo.png'},
        'turns': [{'speaker': 'riley', 'text': 'I am not sure when finance will confirm the number.', 'startSec': 2., 'endSec': 10.}]}
    scenes = build_render_props(manifest)['scenes']
    assert scenes[0]['startSec'] == 2 and scenes[-1]['endSec'] == 10
    for left, right in zip(scenes, scenes[1:]):
        assert left['endSec'] == right['startSec']
    assert scenes[0]['endSec']-scenes[0]['startSec'] > scenes[1]['endSec']-scenes[1]['startSec']


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
