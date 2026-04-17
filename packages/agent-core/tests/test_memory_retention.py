"""Tests for SeedMemory.prune_agent + FeedbackLoop auto-retention + prune CLI."""

from __future__ import annotations

from agent_core import cli
from agent_core.feedback_loop import FeedbackLoop
from agent_core.memory import SeedMemory


class _ScriptedLLM:
    def __init__(self, responses: list[str]):
        self._r = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._r.pop(0) if self._r else ""


def _seed_session(memory: SeedMemory):
    llm = _ScriptedLLM(
        [
            "plan",
            '{"file_path": "out.txt", "content": "hi"}',
            '{"status": "pass", "summary": "ok", "issues": []}',
            '{"score": 9, "verdict": "ship", "notes": []}',
            '{"healthy": true, "severity": "info", "alerts": []}',
            '{"summary": "s", "recommendations": [], "trend": "flat"}',
        ]
    )
    FeedbackLoop(llm=llm, memory=memory).process_goal("g", max_rounds=1)


def test_prune_agent_keeps_newest_n(tmp_memory: SeedMemory):
    for _ in range(5):
        tmp_memory.remember(agent_id="x", content="row", metadata={})
    deleted = tmp_memory.prune_agent("x", keep_last_n=2)
    assert deleted == 3
    rows = tmp_memory.get_recent("x", limit=10)
    assert len(rows) == 2


def test_prune_agent_zero_deletes_all(tmp_memory: SeedMemory):
    for _ in range(3):
        tmp_memory.remember(agent_id="y", content="row", metadata={})
    deleted = tmp_memory.prune_agent("y", keep_last_n=0)
    assert deleted == 3
    assert tmp_memory.get_recent("y", limit=10) == []


def test_prune_agent_noop_when_under_threshold(tmp_memory: SeedMemory):
    tmp_memory.remember(agent_id="z", content="row", metadata={})
    deleted = tmp_memory.prune_agent("z", keep_last_n=5)
    assert deleted == 0


def test_prune_agent_rejects_negative_keep(tmp_memory: SeedMemory):
    import pytest

    with pytest.raises(ValueError):
        tmp_memory.prune_agent("any", keep_last_n=-1)


def test_prune_agent_isolates_other_agents(tmp_memory: SeedMemory):
    tmp_memory.remember(agent_id="a", content="keep", metadata={})
    for _ in range(3):
        tmp_memory.remember(agent_id="b", content="row", metadata={})
    tmp_memory.prune_agent("b", keep_last_n=1)
    assert len(tmp_memory.get_recent("a", limit=10)) == 1
    assert len(tmp_memory.get_recent("b", limit=10)) == 1


def test_feedback_loop_auto_prunes_when_env_set(tmp_memory: SeedMemory, monkeypatch):
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "2")
    for _ in range(4):
        _seed_session(tmp_memory)
    rows = tmp_memory.get_recent("feedback_session", limit=10)
    assert len(rows) == 2


def test_feedback_loop_no_prune_when_env_unset(tmp_memory: SeedMemory, monkeypatch):
    monkeypatch.delenv("AGENT_CORE_SESSION_RETENTION", raising=False)
    for _ in range(3):
        _seed_session(tmp_memory)
    rows = tmp_memory.get_recent("feedback_session", limit=10)
    assert len(rows) == 3


def test_feedback_loop_ignores_invalid_retention(tmp_memory: SeedMemory, monkeypatch):
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "nope")
    for _ in range(3):
        _seed_session(tmp_memory)
    rows = tmp_memory.get_recent("feedback_session", limit=10)
    assert len(rows) == 3


def test_prune_cmd_reports_deleted(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac")
    for _ in range(4):
        _seed_session(mem)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.prune_cmd(keep=1, prune_all=False)
    out = capsys.readouterr().out
    assert "Đã xoá 3 row cũ của feedback_session" in out
    assert len(mem.get_recent("feedback_session", limit=10)) == 1


def test_prune_cmd_rejects_negative(tmp_path, monkeypatch):
    import pytest
    import typer

    monkeypatch.setattr(cli, "SeedMemory", lambda: SeedMemory(root=tmp_path / "ac2"))
    with pytest.raises(typer.Exit):
        cli.prune_cmd(keep=-1, prune_all=False)


def test_prune_cmd_all_flag_prunes_every_agent(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac3")
    # 4 rows each for 3 different agent_ids
    for agent_id in ("feedback_session", "CEO", "Developer"):
        for _ in range(4):
            mem.remember(agent_id=agent_id, content="x", metadata={})
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.prune_cmd(keep=1, prune_all=True)
    out = capsys.readouterr().out
    # 3 rows deleted * 3 agents = 9 total
    assert "Đã xoá 9 row cũ trên 3 agent_id" in out
    for agent_id in ("feedback_session", "CEO", "Developer"):
        assert len(mem.get_recent(agent_id, limit=10)) == 1


def test_prune_cmd_all_flag_empty_memory_reports_nothing_to_do(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac4")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.prune_cmd(keep=1, prune_all=True)
    out = capsys.readouterr().out
    assert "Memory đang trống" in out


def test_prune_cmd_default_leaves_non_feedback_agents_alone(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac5")
    for _ in range(3):
        mem.remember(agent_id="feedback_session", content="f", metadata={})
    for _ in range(3):
        mem.remember(agent_id="CEO", content="c", metadata={})
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    cli.prune_cmd(keep=1, prune_all=False)
    # CEO untouched, only feedback_session pruned
    assert len(mem.get_recent("CEO", limit=10)) == 3
    assert len(mem.get_recent("feedback_session", limit=10)) == 1
