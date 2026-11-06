import errno
import sys

from worker.channel.providers import process


def test_denied_windows_probe_does_not_reclaim_owner(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(process, "_windows_process_state", lambda pid: "unknown")
    assert process.process_state(1234) == "unknown"
    assert process.pid_alive(1234) is True


def test_failed_windows_probe_fails_closed(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    def fail(pid):
        raise PermissionError("process hidden by sandbox")
    monkeypatch.setattr(process, "_windows_process_state", fail)
    assert process.process_state(1234) == "unknown"
    assert process.pid_alive(1234) is True


def test_confirmed_dead_and_invalid_pid(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(process, "_windows_process_state", lambda pid: "dead")
    assert process.pid_alive(1234) is False
    assert process.process_state(-1) == "dead"


def test_posix_permission_and_missing_are_distinct(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    def deny(pid, signal):
        raise PermissionError(errno.EPERM, "denied")
    monkeypatch.setattr(process.os, "kill", deny)
    assert process.process_state(1234) == "unknown"
    def missing(pid, signal):
        raise ProcessLookupError(errno.ESRCH, "missing")
    monkeypatch.setattr(process.os, "kill", missing)
    assert process.process_state(1234) == "dead"
