"""
A missing ffmpeg/ffprobe binary must fail clearly, not with a bare
FileNotFoundError three frames removed from which command was even running.

Reported bug: a deploy image never installed ffmpeg, so the first voiceover
node to run hit `subprocess.run(["ffmpeg", ...])` -> FileNotFoundError:
[Errno 2] No such file or directory: 'ffmpeg', with no indication in the
message of which ffmpeg/ffprobe call was involved. The graph executor still
catches it and fails just that one node (graph.py's `_execute_node`), so the
fix here is only about the error being self-explanatory.
"""
from __future__ import annotations

import pytest

from app.services.studio import assemble


def test_missing_binary_raises_clear_assemble_error(monkeypatch):
    def fake_run(args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", args[0])

    monkeypatch.setattr(assemble.subprocess, "run", fake_run)

    with pytest.raises(assemble.AssembleError) as exc:
        assemble._run(["ffmpeg", "-i", "in.mp4", "out.mp4"], "ffmpeg concat")

    message = str(exc.value)
    assert "ffmpeg concat" in message
    assert "ffmpeg" in message
    assert "binary missing" in message


def test_non_zero_exit_still_raises_assemble_error_with_stderr(monkeypatch):
    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "Unknown encoder 'libx264'"

    monkeypatch.setattr(assemble.subprocess, "run", lambda *a, **k: FakeProc())

    with pytest.raises(assemble.AssembleError) as exc:
        assemble._run(["ffmpeg", "-i", "in.mp4", "out.mp4"], "ffmpeg concat")

    assert "exit 1" in str(exc.value)
    assert "libx264" in str(exc.value)


def test_successful_run_returns_stdout(monkeypatch):
    class FakeProc:
        returncode = 0
        stdout = "42.0\n"
        stderr = ""

    monkeypatch.setattr(assemble.subprocess, "run", lambda *a, **k: FakeProc())

    assert assemble._run(["ffprobe", "in.mp4"], "ffprobe duration") == "42.0\n"
