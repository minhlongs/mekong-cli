"""Unit tests for seed/agents/ceo.py — CEOAgent.create_plan()."""

import json
from unittest.mock import MagicMock, patch

import pytest

from seed.agents.ceo import CEOAgent


def _make_ceo(llm_response: str = ""):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = llm_response
    mock_llm.embed.return_value = []
    mock_llm.model = "test"

    mock_mem = MagicMock()
    mock_mem.recall.return_value = []
    mock_mem.get_recent.return_value = []

    with (
        patch("seed.agents.base.get_llm_client", return_value=mock_llm),
        patch("seed.agents.base.get_memory", return_value=mock_mem),
    ):
        agent = CEOAgent()
    # agent.llm and agent.memory are already set by __init__ via patched singletons
    return agent


class TestCEOAgentCreatePlan:
    def test_returns_plan_key_when_llm_returns_json(self):
        ceo = _make_ceo('{"plan": ["step1", "step2"], "assigned_to": "developer"}')
        result = ceo.create_plan("build a landing page")
        assert "plan" in result
        assert result["plan"] == ["step1", "step2"]
        assert result["assigned_to"] == "developer"

    def test_fallback_when_llm_returns_plain_text(self):
        ceo = _make_ceo("Sure, I will build the app step by step.")
        result = ceo.create_plan("build app")
        assert "plan" in result
        assert isinstance(result["plan"], list)
        assert len(result["plan"]) >= 1

    def test_fallback_includes_original_response_as_first_step(self):
        raw = "Here is my plan: do X, do Y, done."
        ceo = _make_ceo(raw)
        result = ceo.create_plan("task")
        assert result["plan"][0] == raw

    def test_fallback_assigned_to_developer(self):
        ceo = _make_ceo("no json here")
        result = ceo.create_plan("task")
        assert result["assigned_to"] == "developer"

    def test_plan_with_single_step(self):
        ceo = _make_ceo('{"plan": ["only step"], "assigned_to": "analyst"}')
        result = ceo.create_plan("analyze data")
        assert len(result["plan"]) == 1

    def test_plan_with_five_steps(self):
        steps = [f"step {i}" for i in range(5)]
        steps_json = json.dumps(steps)
        ceo = _make_ceo(f'{{"plan": {steps_json}, "assigned_to": "developer"}}')
        result = ceo.create_plan("complex task")
        assert len(result["plan"]) == 5

    def test_calls_llm_with_task_in_prompt(self):
        ceo = _make_ceo('{"plan": ["x"], "assigned_to": "developer"}')
        ceo.create_plan("build a REST API")
        call_args = ceo.llm.chat.call_args[0][0]
        full_prompt = " ".join(m["content"] for m in call_args)
        assert "build a REST API" in full_prompt
