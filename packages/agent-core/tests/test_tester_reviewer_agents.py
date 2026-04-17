"""Unit tests for TesterAgent + ReviewerAgent."""

from __future__ import annotations

from agent_core.agents.reviewer import ReviewerAgent
from agent_core.agents.tester import TesterAgent
from agent_core.memory import SeedMemory


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._responses.pop(0) if self._responses else ""


def test_tester_returns_pass(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"status": "pass", "summary": "all good", "issues": []}'])
    tester = TesterAgent(llm=fake, memory=tmp_memory)
    out = tester.evaluate(goal="build X", artifact="def foo(): return 1")
    assert out == {"status": "pass", "summary": "all good", "issues": []}


def test_tester_coerces_invalid_status(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"status": "maybe", "summary": "meh"}'])
    tester = TesterAgent(llm=fake, memory=tmp_memory)
    out = tester.evaluate(goal="x", artifact="y")
    assert out["status"] == "fail"


def test_tester_non_json_falls_back_to_fail(tmp_memory: SeedMemory):
    fake = FakeLLM(["just plain text no json"])
    tester = TesterAgent(llm=fake, memory=tmp_memory)
    out = tester.evaluate(goal="x", artifact="y")
    assert out["status"] == "fail"
    assert "just plain text" in out["summary"]


def test_reviewer_ship_verdict(tmp_memory: SeedMemory):
    fake = FakeLLM(
        ['{"score": 9, "verdict": "ship", "notes": ["clear naming", "good tests"]}']
    )
    reviewer = ReviewerAgent(llm=fake, memory=tmp_memory)
    out = reviewer.review(goal="g", artifact="a")
    assert out["verdict"] == "ship"
    assert out["score"] == 9
    assert out["notes"] == ["clear naming", "good tests"]


def test_reviewer_defaults_verdict_from_score(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"score": 6, "verdict": "maybe", "notes": []}'])
    reviewer = ReviewerAgent(llm=fake, memory=tmp_memory)
    out = reviewer.review(goal="g", artifact="a")
    assert out["verdict"] == "revise"
    assert out["score"] == 6


def test_reviewer_clamps_negative_score(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"score": -5, "verdict": "block", "notes": ["bad"]}'])
    reviewer = ReviewerAgent(llm=fake, memory=tmp_memory)
    out = reviewer.review(goal="g", artifact="a")
    assert out["score"] == 0
    assert out["verdict"] == "block"


def test_reviewer_non_integer_score_falls_back(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"score": "high", "verdict": "ship", "notes": []}'])
    reviewer = ReviewerAgent(llm=fake, memory=tmp_memory)
    out = reviewer.review(goal="g", artifact="a")
    assert out["score"] == 0
    assert out["verdict"] == "block"
