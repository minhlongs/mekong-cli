"""Unit tests for seed/agents/base.py — pure logic + mocked LLM/memory."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from seed.agents.base import BaseAgent


def _make_agent(llm_response: str = "hello") -> tuple[BaseAgent, MagicMock, MagicMock]:
    """Create BaseAgent with mocked llm + memory."""
    mock_llm = MagicMock()
    mock_llm.chat.return_value = llm_response
    mock_llm.embed.return_value = []
    mock_llm.model = "test-model"

    mock_mem = MagicMock()
    mock_mem.recall.return_value = []
    mock_mem.get_recent.return_value = []

    with (
        patch("seed.agents.base.get_llm_client", return_value=mock_llm),
        patch("seed.agents.base.get_memory", return_value=mock_mem),
    ):
        agent = BaseAgent(name="test", role_prompt="You are a test agent.")

    agent.llm = mock_llm
    agent.memory = mock_mem
    return agent, mock_llm, mock_mem


class TestParseResponse:
    """_parse_response is pure logic — test without mocks."""

    def setup_method(self):
        mock_llm = MagicMock()
        mock_mem = MagicMock()
        mock_mem.recall.return_value = []
        mock_mem.get_recent.return_value = []
        with (
            patch("seed.agents.base.get_llm_client", return_value=mock_llm),
            patch("seed.agents.base.get_memory", return_value=mock_mem),
        ):
            self.agent = BaseAgent(name="test", role_prompt="test")

    def test_plain_json_string(self):
        result = self.agent._parse_response('{"action": "write", "file": "a.py"}')
        assert result["action"] == "write"

    def test_json_embedded_in_markdown(self):
        response = 'Here is the plan:\n```json\n{"plan": ["step1", "step2"]}\n```\nDone.'
        result = self.agent._parse_response(response)
        assert "plan" in result
        assert result["plan"] == ["step1", "step2"]

    def test_multiple_json_blocks_returns_last(self):
        response = '{"first": true}\nSome text\n{"last": true, "step": 2}'
        result = self.agent._parse_response(response)
        assert result.get("last") is True

    def test_no_json_returns_text_key(self):
        result = self.agent._parse_response("Just plain text, no JSON here.")
        assert "text" in result
        assert result["text"] == "Just plain text, no JSON here."

    def test_invalid_json_returns_text_key(self):
        result = self.agent._parse_response("{broken json!!}")
        assert "text" in result

    def test_nested_json_parsed_correctly(self):
        nested = '{"outer": {"inner": [1, 2, 3]}, "done": true}'
        result = self.agent._parse_response(nested)
        assert result["done"] is True
        assert result["outer"]["inner"] == [1, 2, 3]

    def test_empty_string_returns_text_key(self):
        result = self.agent._parse_response("")
        assert "text" in result


class TestBaseAgentRun:
    def test_run_calls_llm_chat(self):
        agent, mock_llm, mock_mem = _make_agent("result text")
        agent.run("do something")
        assert mock_llm.chat.called

    def test_run_returns_string(self):
        agent, _, _ = _make_agent("response content")
        result = agent.run("task")
        assert isinstance(result, str)
        assert result == "response content"

    def test_run_stores_memory(self):
        agent, _, mock_mem = _make_agent("stored")
        agent.run("task for memory")
        assert mock_mem.remember.called

    def test_run_queries_context_first(self):
        agent, _, mock_mem = _make_agent("ctx result")
        agent.run("context query task")
        assert mock_mem.recall.called
        assert mock_mem.get_recent.called

    def test_run_with_extra_context_included_in_prompt(self):
        agent, mock_llm, _ = _make_agent("ok")
        agent.run("task", extra_context="EXTRA INFO")
        call_args = mock_llm.chat.call_args[0][0]
        full_prompt = " ".join(m["content"] for m in call_args)
        assert "EXTRA INFO" in full_prompt
