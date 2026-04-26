"""Integration tests for seed/main.py — CEO→Developer→Tester pipeline.

All LLM calls are mocked. No Ollama required.
"""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

import seed.main as main_module


def _mock_llm(available: bool = True):
    llm = MagicMock()
    llm.is_available.return_value = available
    llm.embed.return_value = []
    llm.model = "test"
    return llm


def _mock_mem():
    mem = MagicMock()
    mem.recall.return_value = []
    mem.get_recent.return_value = []
    return mem


def _run_with_mocks(task: str, llm_responses: list[str] | None = None):
    """Run seed.main.run() with patched LLM returning sequential responses."""
    responses = llm_responses or [
        '{"plan": ["step 1", "step 2"], "assigned_to": "developer"}',
        '{"text": "task complete"}',
        '{"passed": true, "issues": [], "score": 9, "notes": "ok"}',
    ]
    call_count = [0]

    def chat_side_effect(messages):
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        return responses[idx]

    mock_llm = _mock_llm()
    mock_llm.chat.side_effect = chat_side_effect
    mock_mem = _mock_mem()

    with tempfile.TemporaryDirectory() as tmp_outputs:
        with (
            patch("seed.main.get_llm_client", return_value=mock_llm),
            patch("seed.agents.base.get_llm_client", return_value=mock_llm),
            patch("seed.agents.base.get_memory", return_value=mock_mem),
            patch("seed.agents.developer.OUTPUTS_DIR", tmp_outputs),
        ):
            return main_module.run(task)


class TestSeedMainRun:
    def test_returns_dict_with_expected_keys(self):
        result = _run_with_mocks("write hello world")
        assert "task" in result
        assert "plan" in result
        assert "outputs" in result
        assert "test_result" in result

    def test_task_preserved_in_result(self):
        result = _run_with_mocks("build landing page")
        assert result["task"] == "build landing page"

    def test_plan_is_list(self):
        result = _run_with_mocks("task")
        assert isinstance(result["plan"], list)

    def test_outputs_is_list(self):
        result = _run_with_mocks("task")
        assert isinstance(result["outputs"], list)

    def test_test_result_has_passed_key(self):
        result = _run_with_mocks("task")
        assert "passed" in result["test_result"]

    def test_passed_true_exits_loop_on_first_attempt(self):
        """When tester passes, no retry loop triggered."""
        result = _run_with_mocks("task", llm_responses=[
            '{"plan": ["step 1"], "assigned_to": "developer"}',
            '{"text": "first output"}',
            '{"passed": true, "issues": [], "score": 10}',
        ])
        assert result["test_result"]["passed"] is True
        assert result["outputs"] == ["first output"]

    def test_retry_loop_on_failed_test(self):
        """When tester fails once, plan is updated and second attempt passes."""
        result = _run_with_mocks("task", llm_responses=[
            '{"plan": ["step 1"], "assigned_to": "developer"}',
            '{"text": "bad output"}',
            '{"passed": false, "issues": ["missing error handling"], "score": 3}',
            '{"text": "fixed output"}',
            '{"passed": true, "issues": [], "score": 9}',
        ])
        assert result["test_result"]["passed"] is True

    def test_all_retries_exhausted_returns_last_failed_result(self):
        """When tester always fails, run() exits loop and returns the last result."""
        fail_response = '{"passed": false, "issues": ["always fails"], "score": 1}'
        result = _run_with_mocks("task", llm_responses=[
            '{"plan": ["step 1"], "assigned_to": "developer"}',
            '{"text": "output 1"}',
            fail_response,
            '{"text": "output 2"}',
            fail_response,
        ])
        assert result["test_result"]["passed"] is False

    def test_ollama_unavailable_raises_system_exit(self):
        mock_llm = _mock_llm(available=False)
        with (
            patch("seed.main.get_llm_client", return_value=mock_llm),
            pytest.raises(SystemExit),
        ):
            main_module.run("task")


class TestSeedMainModule:
    def test_max_retries_constant_defined(self):
        assert hasattr(main_module, "MAX_RETRIES")
        assert main_module.MAX_RETRIES >= 1

    def test_run_function_exists(self):
        assert callable(main_module.run)

    def test_main_function_exists(self):
        assert callable(main_module.main)
