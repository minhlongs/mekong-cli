"""Tests for BaseAgent, CEOAgent, DeveloperAgent, ToolEnabledAgent with fake LLM."""

from __future__ import annotations

from agent_core.agents.ceo import CEOAgent
from agent_core.agents.developer import DeveloperAgent
from agent_core.agents.tool_agent import ToolEnabledAgent
from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def chat(self, messages, system=None, max_tokens=1024):  # noqa: D401
        self.calls.append({"messages": list(messages), "system": system})
        return self._responses.pop(0) if self._responses else ""


def test_base_agent_run_persists_memory(tmp_memory: SeedMemory):
    fake = FakeLLM(["echo response"])
    agent = BaseAgent("Worker", "you are a worker", llm=fake, memory=tmp_memory)
    reply = agent.run("do the thing")

    assert reply == "echo response"
    records = tmp_memory.get_recent("Worker")
    assert len(records) == 1
    assert "do the thing" in records[0].content


def test_base_agent_includes_recent_memory_in_context(tmp_memory: SeedMemory):
    tmp_memory.remember("CEO", "previous insight")
    fake = FakeLLM(["ok"])
    agent = BaseAgent("CEO", "you plan", llm=fake, memory=tmp_memory)
    agent.run("next task")

    call = fake.calls[0]
    assert "previous insight" in call["messages"][0].content


def test_parse_json_extracts_object():
    out = BaseAgent.parse_json('blah {"file_path": "a.txt", "content": "x"} trailing')
    assert out == {"file_path": "a.txt", "content": "x"}


def test_parse_json_falls_back_to_text():
    assert BaseAgent.parse_json("no braces at all") == {"text": "no braces at all"}


def test_ceo_agent_plan_flow(tmp_memory: SeedMemory):
    fake = FakeLLM(["1. Task A\n2. Task B"])
    ceo = CEOAgent(llm=fake, memory=tmp_memory)
    plan = ceo.plan("build a landing page")
    assert "Task A" in plan


def test_developer_agent_execute_flow(tmp_memory: SeedMemory):
    fake = FakeLLM(['{"file_path": "index.html", "content": "<h1>Hi</h1>"}'])
    dev = DeveloperAgent(llm=fake, memory=tmp_memory)
    reply = dev.execute("write html", plan_context="Plan: build landing")
    assert "index.html" in reply


def test_tool_enabled_agent_invokes_tool(tmp_memory: SeedMemory):
    captured = {"called": False}

    def fake_tool(url: str) -> str:
        """Mock tool that captures invocation."""
        captured["called"] = True
        captured["url"] = url
        return "web page body"

    fake = FakeLLM(
        [
            '{"tool": "fake_tool", "arguments": {"url": "https://example.com"}}',
            "final answer using tool output",
        ]
    )
    agent = ToolEnabledAgent(
        name="Scout",
        role_prompt="you browse",
        llm=fake,
        memory=tmp_memory,
        tools={"fake_tool": fake_tool},
    )
    reply = agent.run("fetch example.com")

    assert captured["called"] is True
    assert captured["url"] == "https://example.com"
    assert "final answer" in reply


def test_tool_enabled_agent_falls_through_on_plain_text(tmp_memory: SeedMemory):
    fake = FakeLLM(["just text no tool call"])
    agent = ToolEnabledAgent(
        name="Scout",
        role_prompt="you browse",
        llm=fake,
        memory=tmp_memory,
        tools={},
    )
    reply = agent.run("hello")
    assert reply == "just text no tool call"


def test_default_llm_points_at_mekongd(monkeypatch):
    monkeypatch.delenv("MEKONGD_URL", raising=False)
    client = LLMClient()
    assert client.base_url == "http://127.0.0.1:8765"
