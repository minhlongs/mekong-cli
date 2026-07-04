"""Unit tests for FeedbackLoop."""

from __future__ import annotations

import pytest

from agent_core.feedback_loop import FeedbackLoop
from agent_core.memory import SeedMemory


class ScriptedLLM:
    """Drains a scripted list of responses per chat call."""

    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.call_count = 0

    def chat(self, messages, system=None, max_tokens=1024):
        self.call_count += 1
        return self._responses.pop(0) if self._responses else ""


def _pipeline_responses(
    plan: str,
    artifact_json: str,
    tester_json: str,
    reviewer_json: str,
) -> list[str]:
    """4 responses for one orchestrator pass: CEO, Developer, Tester, Reviewer."""
    return [plan, artifact_json, tester_json, reviewer_json]


def _round_responses(
    plan: str,
    artifact_json: str,
    tester_json: str,
    reviewer_json: str,
    ops_json: str,
    analyst_json: str,
) -> list[str]:
    """6 responses for one feedback round: pipeline (4) + Ops + Analyst."""
    return _pipeline_responses(plan, artifact_json, tester_json, reviewer_json) + [
        ops_json,
        analyst_json,
    ]


def test_feedback_loop_early_exit_when_healthy(tmp_memory: SeedMemory):
    """First round passes cleanly → loop stops at round 1 even if max_rounds=3."""
    fake = ScriptedLLM(
        _round_responses(
            plan="plan",
            artifact_json='{"file_path": "out.txt", "content": "hi"}',
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "solid", "recommendations": [], "trend": "flat"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    session = loop.process_goal("demo", max_rounds=3)
    assert len(session.rounds) == 1
    assert session.final.review["verdict"] == "ship"


def test_feedback_loop_retries_on_revise_verdict(tmp_memory: SeedMemory):
    """Round 1 verdict=revise → loop retries round 2 which ships."""
    fake = ScriptedLLM(
        _round_responses(
            plan="p1",
            artifact_json="draft v1",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 6, "verdict": "revise", "notes": ["rename X"]}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "needs polish", '
            '"recommendations": ["Đổi tên biến X"], "trend": "flat"}',
        )
        + _round_responses(
            plan="p2",
            artifact_json="draft v2",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "fixed", "recommendations": [], "trend": "improving"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    session = loop.process_goal("demo", max_rounds=2)
    assert len(session.rounds) == 2
    assert session.rounds[0].report.review["verdict"] == "revise"
    assert session.rounds[1].report.review["verdict"] == "ship"
    assert session.rounds[1].analyst["trend"] == "improving"


def test_feedback_loop_retries_on_ops_warn(tmp_memory: SeedMemory):
    """Review says ship but Ops says warn → still retries."""
    fake = ScriptedLLM(
        _round_responses(
            plan="p1",
            artifact_json="art1",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 8, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": false, "severity": "warn", "alerts": ["slow"]}',
            analyst_json='{"summary": "speed issue", '
            '"recommendations": ["Tối ưu hàm Y"], "trend": "flat"}',
        )
        + _round_responses(
            plan="p2",
            artifact_json="art2",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "all green", "recommendations": [], "trend": "improving"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    session = loop.process_goal("demo", max_rounds=2)
    assert len(session.rounds) == 2
    assert session.rounds[0].ops["severity"] == "warn"
    assert session.rounds[1].ops["severity"] == "info"


def test_feedback_loop_stops_at_max_rounds(tmp_memory: SeedMemory):
    """Even if still failing, loop is bounded by max_rounds=1."""
    fake = ScriptedLLM(
        _round_responses(
            plan="p",
            artifact_json="bad",
            tester_json='{"status": "fail", "summary": "X", "issues": ["X"]}',
            reviewer_json='{"score": 2, "verdict": "block", "notes": []}',
            ops_json='{"healthy": false, "severity": "critical", "alerts": ["boom"]}',
            analyst_json='{"summary": "broken", '
            '"recommendations": ["Sửa X"], "trend": "regressing"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    session = loop.process_goal("demo", max_rounds=1)
    assert len(session.rounds) == 1
    assert session.final.review["verdict"] == "block"


def test_feedback_loop_rejects_invalid_max_rounds(tmp_memory: SeedMemory):
    loop = FeedbackLoop(memory=tmp_memory)
    with pytest.raises(ValueError):
        loop.process_goal("x", max_rounds=0)


def test_feedback_session_persists_rounds_to_memory(tmp_memory: SeedMemory):
    """process_goal should write each round to SeedMemory under feedback_session."""
    fake = ScriptedLLM(
        _round_responses(
            plan="p",
            artifact_json="a",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "ok", "recommendations": [], "trend": "flat"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    loop.process_goal("persist-me", max_rounds=1)
    records = tmp_memory.get_recent("feedback_session", limit=5)
    assert len(records) == 1
    assert records[0].metadata["verdict"] == "ship"
    assert records[0].metadata["round"] == 1


def test_feedback_loop_persist_false_skips_write(tmp_memory: SeedMemory):
    """persist=False should keep memory empty."""
    fake = ScriptedLLM(
        _round_responses(
            plan="p",
            artifact_json="a",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "ok", "recommendations": [], "trend": "flat"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    loop.process_goal("no-persist", max_rounds=1, persist=False)
    assert tmp_memory.get_recent("feedback_session", limit=5) == []


def test_feedback_loop_seeds_analyst_history_from_prior_session(tmp_memory: SeedMemory):
    """Second run should observe first run's rounds via SeedMemory."""
    from agent_core.feedback_loop import load_recent_history

    first = ScriptedLLM(
        _round_responses(
            plan="p1",
            artifact_json="a1",
            tester_json='{"status": "fail", "summary": "broken", "issues": ["x"]}',
            reviewer_json='{"score": 4, "verdict": "revise", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "bad", "recommendations": [], "trend": "regressing"}',
        )
    )
    FeedbackLoop(llm=first, memory=tmp_memory).process_goal("v1", max_rounds=1)

    loaded = load_recent_history(tmp_memory, limit=3)
    assert len(loaded) == 1
    assert loaded[0]["review"]["verdict"] == "revise"
    assert loaded[0]["test"]["status"] == "fail"


def test_feedback_session_as_dict(tmp_memory: SeedMemory):
    fake = ScriptedLLM(
        _round_responses(
            plan="p",
            artifact_json="a",
            tester_json='{"status": "pass", "summary": "ok", "issues": []}',
            reviewer_json='{"score": 9, "verdict": "ship", "notes": []}',
            ops_json='{"healthy": true, "severity": "info", "alerts": []}',
            analyst_json='{"summary": "ok", "recommendations": [], "trend": "flat"}',
        )
    )
    loop = FeedbackLoop(llm=fake, memory=tmp_memory)
    session = loop.process_goal("demo", max_rounds=1)
    d = session.as_dict()
    assert d["goal"] == "demo"
    assert len(d["rounds"]) == 1
    assert d["rounds"][0]["review_verdict"] == "ship"
    assert d["rounds"][0]["ops_severity"] == "info"
    assert d["final"]["review"]["verdict"] == "ship"
