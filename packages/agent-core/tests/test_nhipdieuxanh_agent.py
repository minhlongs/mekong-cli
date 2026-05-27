"""Unit tests for NhipDieuAnhAgent."""

from __future__ import annotations

from agent_core.agents.nhipdieuxanh_agent import NhipDieuAnhAgent
from agent_core.memory import SeedMemory


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)

    def chat(self, messages, system=None, max_tokens=1024):
        return self._responses.pop(0) if self._responses else ""


def test_nhipdieuxanh_instantiates(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"summary": "tốt", "actions": ["trồng cây"], "impact": "cao"}'])
    agent = NhipDieuAnhAgent(llm=fake, memory=tmp_memory)
    assert agent.name == "nhipdieuxanh"


def test_plan_green_returns_dict(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"summary": "tốt", "actions": ["trồng cây"], "impact": "cao"}'])
    agent = NhipDieuAnhAgent(llm=fake, memory=tmp_memory)
    out = agent.plan_green("công ty sản xuất bao bì")
    assert out["summary"] == "tốt"
    assert out["actions"] == ["trồng cây"]
    assert out["impact"] == "cao"


def test_plan_green_coerces_bad_impact(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"summary": "ok", "actions": [], "impact": "xanh"}'])
    agent = NhipDieuAnhAgent(llm=fake, memory=tmp_memory)
    out = agent.plan_green("test")
    assert out["impact"] == "trung bình"


def test_plan_green_fallback_on_non_json(tmp_memory: SeedMemory):
    fake = FakeLLM(["không có json"])
    agent = NhipDieuAnhAgent(llm=fake, memory=tmp_memory)
    out = agent.plan_green("test")
    assert "summary" in out
    assert out["actions"] == []
    assert out["impact"] == "trung bình"
