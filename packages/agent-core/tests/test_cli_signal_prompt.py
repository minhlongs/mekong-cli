"""Tests for _maybe_prompt_signal — auto-capture Pillar 3 feedback after `agent-core run`."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent_core.cli import _maybe_prompt_signal


class _FakeLLM:
    def __init__(self):
        self.send_signal = MagicMock()


def test_prompt_noop_when_disabled(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    llm = _FakeLLM()
    _maybe_prompt_signal(llm, enabled=False)
    llm.send_signal.assert_not_called()


def test_prompt_noop_when_no_tty(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    llm = _FakeLLM()
    _maybe_prompt_signal(llm, enabled=True)
    llm.send_signal.assert_not_called()


@pytest.mark.parametrize(
    "answer, expected_kind",
    [("g", "good"), ("good", "good"), ("b", "bad"), ("bad", "bad")],
)
def test_prompt_sends_good_or_bad(monkeypatch, answer, expected_kind):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("typer.prompt", lambda *a, **kw: answer)
    llm = _FakeLLM()
    _maybe_prompt_signal(llm, enabled=True)
    llm.send_signal.assert_called_once_with(expected_kind)


@pytest.mark.parametrize("answer", ["s", "skip", "", "x"])
def test_prompt_skips_on_non_gb_answer(monkeypatch, answer):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("typer.prompt", lambda *a, **kw: answer)
    llm = _FakeLLM()
    _maybe_prompt_signal(llm, enabled=True)
    llm.send_signal.assert_not_called()


def test_prompt_swallows_send_error(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("typer.prompt", lambda *a, **kw: "g")
    llm = _FakeLLM()
    llm.send_signal.side_effect = RuntimeError("network down")
    _maybe_prompt_signal(llm, enabled=True)
    err = capsys.readouterr().err
    assert "Cảnh báo" in err
    assert "network down" in err
