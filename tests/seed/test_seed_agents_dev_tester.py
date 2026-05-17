"""Unit tests for DeveloperAgent and TesterAgent."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from seed.agents.developer import DeveloperAgent
from seed.agents.tester import TesterAgent


def _make_agent(cls, llm_response: str = ""):
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
        agent = cls()
    # agent.llm and agent.memory are already set by __init__ via patched singletons
    return agent


# ─── DeveloperAgent ─────────────────────────────────────────────────────────


class TestDeveloperAgentExecutePlan:
    def test_returns_list(self, tmp_path):
        dev = _make_agent(DeveloperAgent, '{"text": "task complete"}')
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            result = dev.execute_plan(["step 1"], "do something")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_text_response_returned_as_output(self, tmp_path):
        dev = _make_agent(DeveloperAgent, '{"text": "all done!"}')
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            result = dev.execute_plan(["step 1"], "task")
        assert result[0] == "all done!"

    def test_file_response_saves_file(self, tmp_path):
        dev = _make_agent(
            DeveloperAgent,
            '{"file_path": "hello.html", "content": "<h1>Hello</h1>"}',
        )
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            result = dev.execute_plan(["write file"], "create html")
        assert len(result) == 1
        saved_path = Path(result[0])
        assert saved_path.exists()
        assert "<h1>Hello</h1>" in saved_path.read_text()

    def test_file_save_uses_safe_filename(self, tmp_path):
        dev = _make_agent(
            DeveloperAgent,
            '{"file_path": "../../etc/passwd", "content": "malicious"}',
        )
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            result = dev.execute_plan(["write file"], "task")
        saved_path = Path(result[0])
        # Path().name strips all directory components — file must land in tmp_path only
        assert saved_path.name == "passwd"
        assert saved_path.parent == tmp_path

    def test_plain_response_fallback(self, tmp_path):
        dev = _make_agent(DeveloperAgent, "no json, just plain response")
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            result = dev.execute_plan(["step"], "task")
        assert result[0] == "no json, just plain response"

    def test_multiple_plan_steps_sent_to_llm(self, tmp_path):
        dev = _make_agent(DeveloperAgent, '{"text": "done"}')
        with patch("seed.agents.developer.OUTPUTS_DIR", str(tmp_path)):
            dev.execute_plan(["step A", "step B", "step C"], "multi-step task")
        prompt = " ".join(m["content"] for m in dev.llm.chat.call_args[0][0])
        assert "step A" in prompt
        assert "step B" in prompt


# ─── TesterAgent ─────────────────────────────────────────────────────────────


class TestTesterAgentVerify:
    def test_returns_dict_with_passed_key(self):
        tester = _make_agent(TesterAgent, '{"passed": true, "issues": [], "score": 9}')
        result = tester.verify("task", ["output1"])
        assert "passed" in result
        assert result["passed"] is True

    def test_failed_verdict_propagated(self):
        tester = _make_agent(
            TesterAgent,
            '{"passed": false, "issues": ["missing header"], "score": 4}',
        )
        result = tester.verify("task", ["output"])
        assert result["passed"] is False
        assert "missing header" in result["issues"]

    def test_fallback_when_no_passed_key(self):
        tester = _make_agent(TesterAgent, "Looks good to me.")
        result = tester.verify("task", ["output"])
        assert result["passed"] is True
        assert result["score"] == 7

    def test_score_returned(self):
        tester = _make_agent(TesterAgent, '{"passed": true, "issues": [], "score": 8}')
        result = tester.verify("task", ["output"])
        assert result["score"] == 8

    def test_outputs_included_in_prompt(self):
        tester = _make_agent(TesterAgent, '{"passed": true, "issues": [], "score": 9}')
        tester.verify("build landing page", ["index.html saved", "style.css saved"])
        prompt = " ".join(m["content"] for m in tester.llm.chat.call_args[0][0])
        assert "index.html saved" in prompt
        assert "build landing page" in prompt

    def test_empty_outputs_list(self):
        tester = _make_agent(TesterAgent, '{"passed": false, "issues": ["no output"], "score": 0}')
        result = tester.verify("task", [])
        assert result["passed"] is False

    def test_notes_field_returned(self):
        tester = _make_agent(
            TesterAgent,
            '{"passed": true, "issues": [], "score": 9, "notes": "well done"}',
        )
        result = tester.verify("task", ["output"])
        assert result["notes"] == "well done"
