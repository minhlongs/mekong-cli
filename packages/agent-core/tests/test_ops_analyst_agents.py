"""Unit tests for OpsAgent + AnalystAgent."""

from __future__ import annotations

from agent_core.agents.analyst import AnalystAgent
from agent_core.agents.ops import OpsAgent
from agent_core.memory import SeedMemory


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._responses.pop(0) if self._responses else ""


SAMPLE_REPORT = {
    "goal": "build hello file",
    "test": {"status": "pass", "summary": "ok", "issues": []},
    "review": {"verdict": "ship", "score": 9, "notes": ["clean"]},
}


def test_ops_returns_healthy(tmp_memory: SeedMemory):
    fake = FakeLLM(
        ['{"healthy": true, "severity": "info", "alerts": []}']
    )
    ops = OpsAgent(llm=fake, memory=tmp_memory)
    out = ops.monitor(SAMPLE_REPORT)
    assert out == {"healthy": True, "severity": "info", "alerts": []}


def test_ops_coerces_bad_severity(tmp_memory: SeedMemory):
    fake = FakeLLM(
        ['{"healthy": false, "severity": "meltdown", "alerts": ["x"]}']
    )
    ops = OpsAgent(llm=fake, memory=tmp_memory)
    out = ops.monitor(SAMPLE_REPORT)
    assert out["severity"] == "warn"
    assert out["alerts"] == ["x"]


def test_ops_derives_healthy_from_severity_when_missing(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"severity": "critical", "alerts": ["fail"]}'])
    ops = OpsAgent(llm=fake, memory=tmp_memory)
    out = ops.monitor(SAMPLE_REPORT)
    assert out["healthy"] is False
    assert out["severity"] == "critical"


def test_ops_non_json_falls_back(tmp_memory: SeedMemory):
    fake = FakeLLM(["oops no json"])
    ops = OpsAgent(llm=fake, memory=tmp_memory)
    out = ops.monitor(SAMPLE_REPORT)
    assert out["severity"] == "warn"
    assert out["healthy"] is False
    assert out["alerts"] == []


def test_analyst_returns_recommendations(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            '{"summary": "good run", "recommendations": ["Thêm test"], '
            '"trend": "improving"}'
        ]
    )
    analyst = AnalystAgent(llm=fake, memory=tmp_memory)
    out = analyst.analyze(SAMPLE_REPORT)
    assert out == {
        "summary": "good run",
        "recommendations": ["Thêm test"],
        "trend": "improving",
    }


def test_analyst_defaults_trend_when_invalid(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            '{"summary": "x", "recommendations": [], "trend": "great"}'
        ]
    )
    analyst = AnalystAgent(llm=fake, memory=tmp_memory)
    out = analyst.analyze(SAMPLE_REPORT)
    assert out["trend"] == "flat"


def test_analyst_accepts_history(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            '{"summary": "rebound", "recommendations": ["cải tiến A"], '
            '"trend": "improving"}'
        ]
    )
    analyst = AnalystAgent(llm=fake, memory=tmp_memory)
    history = [
        {
            "test": {"status": "fail"},
            "review": {"verdict": "revise", "score": 4},
        }
    ]
    out = analyst.analyze(SAMPLE_REPORT, history=history)
    assert out["summary"] == "rebound"
    assert out["trend"] == "improving"
