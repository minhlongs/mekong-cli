"""Tests for `agent-core history` CLI + format_history + list_recent_sessions."""

from __future__ import annotations

import json as _json

from agent_core import cli
from agent_core.feedback_loop import FeedbackLoop, list_recent_sessions
from agent_core.formatters import format_history
from agent_core.memory import SeedMemory


class _ScriptedLLM:
    def __init__(self, responses: list[str]):
        self._r = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._r.pop(0) if self._r else ""


def _seed_one_session(memory: SeedMemory, verdict: str = "ship", trend: str = "flat"):
    llm = _ScriptedLLM(
        [
            "plan",
            '{"file_path": "out.txt", "content": "hi"}',
            '{"status": "pass", "summary": "ok", "issues": []}',
            f'{{"score": 9, "verdict": "{verdict}", "notes": []}}',
            '{"healthy": true, "severity": "info", "alerts": []}',
            f'{{"summary": "s", "recommendations": [], "trend": "{trend}"}}',
        ]
    )
    FeedbackLoop(llm=llm, memory=memory).process_goal("làm landing page", max_rounds=1)


def test_format_history_empty_message():
    out = format_history([])
    assert "Chưa có phiên feedback" in out


def test_format_history_renders_rows():
    rows = [
        {
            "created_at": "2026-04-18T03:30:00Z",
            "round": 1,
            "verdict": "ship",
            "score": 9,
            "trend": "flat",
            "goal": "làm landing page",
        }
    ]
    out = format_history(rows)
    lines = out.splitlines()
    assert "When" in lines[0] and "Verdict" in lines[0]
    assert "ship" in out and "flat" in out and "landing" in out


def test_list_recent_sessions_returns_newest_first(tmp_memory: SeedMemory):
    _seed_one_session(tmp_memory, verdict="revise", trend="regressing")
    _seed_one_session(tmp_memory, verdict="ship", trend="improving")
    rows = list_recent_sessions(tmp_memory, limit=5)
    # get_recent returns newest first → ship (last written) before revise
    assert [r["verdict"] for r in rows] == ["ship", "revise"]
    assert rows[0]["trend"] == "improving"


def test_list_recent_sessions_skips_malformed(tmp_memory: SeedMemory):
    tmp_memory.remember(
        agent_id="feedback_session", content="not-json", metadata={"round": 1}
    )
    _seed_one_session(tmp_memory)
    rows = list_recent_sessions(tmp_memory, limit=5)
    # Malformed row silently dropped
    assert len(rows) == 1
    assert rows[0]["verdict"] == "ship"


def test_history_cmd_empty_table(tmp_path, monkeypatch, capsys):
    """CLI on a clean memory shows friendly empty message."""
    monkeypatch.setattr(cli, "SeedMemory", lambda: SeedMemory(root=tmp_path / "ac"))
    cli.history_cmd(limit=10, as_json=False)
    out = capsys.readouterr().out
    assert "Chưa có phiên feedback" in out


def test_history_cmd_renders_table(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac2")
    _seed_one_session(mem, verdict="ship", trend="flat")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.history_cmd(limit=5, as_json=False)
    out = capsys.readouterr().out
    assert "ship" in out and "landing" in out


def test_history_cmd_json_output(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac3")
    _seed_one_session(mem, verdict="ship", trend="flat")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.history_cmd(limit=10, as_json=True)
    out = capsys.readouterr().out
    parsed = _json.loads(out)
    assert len(parsed) == 1
    assert parsed[0]["verdict"] == "ship"
    assert parsed[0]["trend"] == "flat"
