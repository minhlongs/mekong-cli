"""Tests for WorkspaceAgent — covers init, plan, execute (json/text output, errors), verify."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.core.agent_base import Task, Result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id: str, description: str = "gws drive list", **input_kwargs) -> Task:
    return Task(id=task_id, description=description, input=dict(**input_kwargs))


def make_completed_process(stdout: str = "", stderr: str = "", returncode: int = 0):
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.stdout = stdout
    cp.stderr = stderr
    cp.returncode = returncode
    return cp


def build_agent():
    """Build WorkspaceAgent with gws CLI mocked out."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = make_completed_process(stdout="gws 1.0.0")
        from src.agents.workspace_agent import WorkspaceAgent
        agent = WorkspaceAgent(name="workspace", max_retries=3)
    return agent


# ---------------------------------------------------------------------------
# __init__ / _check_gws_installed
# ---------------------------------------------------------------------------

class TestInit:
    def test_init_succeeds_when_gws_found(self):
        agent = build_agent()
        assert agent.name == "workspace"
        assert agent.max_retries == 3

    def test_init_raises_when_gws_not_found(self):
        from src.agents.workspace_agent import WorkspaceAgent

        with patch("subprocess.run", side_effect=FileNotFoundError("gws not found")):
            with pytest.raises(Exception, match="gws"):
                WorkspaceAgent()

    def test_init_raises_when_gws_exits_nonzero(self):
        from src.agents.workspace_agent import WorkspaceAgent

        with patch(
            "subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "gws"),
        ):
            with pytest.raises(Exception, match="gws"):
                WorkspaceAgent()


# ---------------------------------------------------------------------------
# plan()
# ---------------------------------------------------------------------------

class TestPlan:
    def setup_method(self):
        self.agent = build_agent()

    def test_plan_returns_empty_list(self):
        tasks = self.agent.plan("list all files in Drive")
        assert tasks == []

    def test_plan_any_input_returns_empty(self):
        for input_data in ["", "gws drive list", "complex multi-step task"]:
            assert self.agent.plan(input_data) == []


# ---------------------------------------------------------------------------
# execute() — happy path
# ---------------------------------------------------------------------------

class TestExecuteHappyPath:
    def setup_method(self):
        self.agent = build_agent()

    def test_execute_json_output_parsed(self):
        payload = {"files": [{"id": "1", "name": "doc.pdf"}]}
        with patch("subprocess.run", return_value=make_completed_process(stdout=json.dumps(payload))):
            task = make_task("t1", description="gws drive list")
            result = self.agent.execute(task)
        assert result.success is True
        assert result.output == payload

    def test_execute_plain_text_output(self):
        with patch("subprocess.run", return_value=make_completed_process(stdout="ok")):
            task = make_task("t1", description="gws drive list")
            result = self.agent.execute(task)
        assert result.success is True
        assert result.output == "ok"

    def test_execute_empty_output(self):
        with patch("subprocess.run", return_value=make_completed_process(stdout="")):
            task = make_task("t1", description="gws calendar list")
            result = self.agent.execute(task)
        assert result.success is True
        assert result.output == ""

    def test_execute_prepends_gws_prefix_if_missing(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout="ok")
            task = make_task("t1", description="drive list")  # no "gws " prefix
            self.agent.execute(task)
        called_cmd = mock_run.call_args[0][0]
        assert called_cmd[0] == "gws"
        assert "drive" in called_cmd

    def test_execute_does_not_double_prefix(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout="ok")
            task = make_task("t1", description="gws drive list")
            self.agent.execute(task)
        called_cmd = mock_run.call_args[0][0]
        # First token should be 'gws', second 'drive' — not 'gws gws ...'
        assert called_cmd[0] == "gws"
        assert called_cmd[1] != "gws"


# ---------------------------------------------------------------------------
# execute() — error paths
# ---------------------------------------------------------------------------

class TestExecuteErrors:
    def setup_method(self):
        self.agent = build_agent()

    def test_execute_called_process_error_returns_failure(self):
        err = subprocess.CalledProcessError(1, "gws")
        err.stderr = "API error"
        err.stdout = ""
        with patch("subprocess.run", side_effect=err):
            task = make_task("t1", description="gws drive list")
            result = self.agent.execute(task)
        assert result.success is False
        assert "API error" in result.error

    def test_execute_access_not_configured_adds_hint(self):
        err = subprocess.CalledProcessError(1, "gws")
        err.stderr = "accessNotConfigured"
        err.stdout = ""
        with patch("subprocess.run", side_effect=err):
            task = make_task("t1", description="gws drive list")
            result = self.agent.execute(task)
        assert result.success is False
        assert "gws auth setup" in result.error

    def test_execute_invalid_grant_adds_hint(self):
        err = subprocess.CalledProcessError(1, "gws")
        err.stderr = "invalid_grant detected"
        err.stdout = ""
        with patch("subprocess.run", side_effect=err):
            task = make_task("t1", description="gws mail list")
            result = self.agent.execute(task)
        assert result.success is False
        assert "gws auth setup" in result.error

    def test_execute_error_falls_back_to_stdout_when_stderr_empty(self):
        err = subprocess.CalledProcessError(1, "gws")
        err.stderr = ""
        err.stdout = "stdout fallback error"
        with patch("subprocess.run", side_effect=err):
            task = make_task("t1", description="gws drive list")
            result = self.agent.execute(task)
        assert result.success is False
        assert "stdout fallback error" in result.error


# ---------------------------------------------------------------------------
# verify()
# ---------------------------------------------------------------------------

class TestVerify:
    def setup_method(self):
        self.agent = build_agent()

    def test_verify_true_on_success(self):
        result = Result(task_id="t1", success=True, output="data")
        assert self.agent.verify(result) is True

    def test_verify_false_on_failure(self):
        result = Result(task_id="t1", success=False, output=None, error="oops")
        assert self.agent.verify(result) is False
