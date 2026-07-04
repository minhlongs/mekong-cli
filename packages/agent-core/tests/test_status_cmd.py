"""Tests for SeedMemory.agent_counts + last_created_at + format_status + status_cmd."""

from __future__ import annotations

from agent_core import cli
from agent_core.feedback_loop import FeedbackLoop
from agent_core.formatters import format_status
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


def test_agent_counts_empty(tmp_memory: SeedMemory):
    assert tmp_memory.agent_counts() == {}


def test_agent_counts_aggregates_by_agent_id(tmp_memory: SeedMemory):
    for _ in range(3):
        tmp_memory.remember(agent_id="CEO", content="c", metadata={})
    for _ in range(2):
        tmp_memory.remember(agent_id="Dev", content="d", metadata={})
    counts = tmp_memory.agent_counts()
    assert counts == {"CEO": 3, "Dev": 2} or counts == {"Dev": 2, "CEO": 3}
    assert sum(counts.values()) == 5


def test_last_created_at_returns_none_when_empty(tmp_memory: SeedMemory):
    assert tmp_memory.last_created_at("nonexistent") is None


def test_last_created_at_returns_newest(tmp_memory: SeedMemory):
    tmp_memory.remember(agent_id="x", content="a", metadata={})
    tmp_memory.remember(agent_id="x", content="b", metadata={})
    ts = tmp_memory.last_created_at("x")
    assert ts is not None
    assert ts.startswith("20")  # ISO timestamp


def test_format_status_empty_memory():
    out = format_status(
        agent_rows={}, last_session_at=None, retention_env=None, memory_root="/tmp/ac"
    )
    assert "memory is empty" in out
    assert "unbounded" in out
    assert "(never)" in out


def test_format_status_with_rows_and_retention():
    out = format_status(
        agent_rows={"feedback_session": 5, "CEO": 2},
        last_session_at="2026-04-18T04:30:00.000+00:00",
        retention_env="10",
        memory_root="/tmp/ac",
    )
    assert "feedback_session" in out
    assert "5" in out
    assert "AGENT_CORE_SESSION_RETENTION=10" in out
    assert "auto-prune on" in out
    assert "2026-04-18T04:30:00" in out


def test_format_status_retention_zero_reported_as_unbounded():
    out = format_status(
        agent_rows={"x": 1}, last_session_at=None, retention_env="0", memory_root="/tmp/ac"
    )
    assert "unbounded" in out


def test_format_status_retention_invalid_reported_as_unbounded():
    out = format_status(
        agent_rows={"x": 1}, last_session_at=None, retention_env="nope",
        memory_root="/tmp/ac",
    )
    assert "unbounded" in out


def test_status_cmd_renders_snapshot(tmp_path, monkeypatch, capsys):
    mem = SeedMemory(root=tmp_path / "ac")
    _seed_session(mem)
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "50")
    cli.status_cmd(as_json=False)
    out = capsys.readouterr().out
    assert "agent-core status" in out
    assert "feedback_session" in out
    assert "auto-prune on" in out
    assert str(tmp_path / "ac") in out


def test_status_cmd_json_emits_parseable_payload(tmp_path, monkeypatch, capsys):
    """--json emits dict with memory_root + retention_env + agent_rows + last_session_at."""
    import json as _json

    mem = SeedMemory(root=tmp_path / "ac")
    for _ in range(5):
        mem.remember(agent_id="CEO", content="x", metadata={})
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "100")
    cli.status_cmd(as_json=True)
    payload = _json.loads(capsys.readouterr().out)
    assert set(payload.keys()) == {"memory_root", "retention_env", "last_session_at", "agent_rows"}
    assert payload["retention_env"] == "100"
    assert payload["agent_rows"] == {"CEO": 5}
    assert payload["last_session_at"] is None  # no feedback_session seeded
    assert payload["memory_root"].endswith("/ac")


def test_status_cmd_json_no_text_banner(tmp_path, monkeypatch, capsys):
    """--json pure JSON — no text banner leak."""
    import json as _json

    mem = SeedMemory(root=tmp_path / "ac")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.delenv("AGENT_CORE_SESSION_RETENTION", raising=False)
    cli.status_cmd(as_json=True)
    out = capsys.readouterr().out
    _json.loads(out)  # must parse
    assert "agent-core status" not in out
    assert "auto-prune" not in out
