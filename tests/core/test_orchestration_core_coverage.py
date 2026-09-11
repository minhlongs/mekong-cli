"""Tests for Agent & Execution Orchestration Engine Subsystem.

Covers:
- src.core.agent_schema (ALL_TOOLS, OUTPUT_MODES, STEP_HOOKS, validate_agent_definition, merge_definition_defaults)
- src.core.agent_base (TaskStatus, Task, Result, AgentBase)
- src.core.context_flow (AgentContribution, ContextFlow)
- src.core.workflow_state (WorkflowStatus, StepStatus, InvalidTransitionError, StepState, WorkflowState)
- src.core.rate_limit_client (RateLimitStatus, RateLimitClient)
- src.core.rate_limit (RateLimiter shim)
- src.core.sentry_init (init_sentry)
- src.core.rollback (RollbackHandler, handle_failure shim)
- src.core.orchestrator.rollback (RollbackHandler, handle_failure)
"""
from __future__ import annotations

import json
import subprocess
import time
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from rich.console import Console

from src.core.agent_base import AgentBase, Result, Task, TaskStatus
from src.core.agent_schema import (
    ALL_TOOLS,
    OUTPUT_MODES,
    STEP_HOOKS,
    merge_definition_defaults,
    validate_agent_definition,
)
from src.core.context_flow import AgentContribution, ContextFlow
from src.core.orchestrator.models import (
    OrchestrationResult,
    OrchestrationStatus,
    StepResult,
)
from src.core.parser import Recipe, RecipeStep
from src.core.rate_limit import RateLimiter
from src.core.rate_limit_client import RateLimitClient, RateLimitStatus
from src.core.rollback import RollbackHandler, handle_failure
from src.core.sentry_init import init_sentry
from src.core.verifier import ExecutionResult, VerificationReport
from src.core.workflow_state import (
    InvalidTransitionError,
    StepState,
    StepStatus,
    WorkflowState,
    WorkflowStatus,
)


# ---------------------------------------------------------------------------
# src.core.agent_schema
# ---------------------------------------------------------------------------
class TestAgentSchema:
    def test_constants(self):
        assert ALL_TOOLS == "*"
        assert "last_message" in OUTPUT_MODES
        assert "on_step_start" in STEP_HOOKS

    def test_validate_id(self):
        # Missing id
        errs = validate_agent_definition({"displayName": "Agent"})
        assert any("Missing required field: 'id'" in e for e in errs)

        # Non-string id
        errs = validate_agent_definition({"id": 123, "displayName": "Agent"})
        assert any("'id' must be a non-empty string" in e for e in errs)

        # Empty string id
        errs = validate_agent_definition({"id": "   ", "displayName": "Agent"})
        assert any("'id' must be a non-empty string" in e for e in errs)

    def test_validate_display_name(self):
        # Missing displayName
        errs = validate_agent_definition({"id": "agent-1"})
        assert any("Missing required field: 'displayName'" in e for e in errs)

        # Non-string displayName
        errs = validate_agent_definition({"id": "agent-1", "displayName": 123})
        assert any("'displayName' must be a string" in e for e in errs)

    def test_validate_allowed_tools(self):
        base = {"id": "a", "displayName": "A"}
        # Not a list
        errs = validate_agent_definition({**base, "allowedTools": "all"})
        assert any("'allowedTools' must be a list of strings" in e for e in errs)

        # List with non-strings
        errs = validate_agent_definition({**base, "allowedTools": ["tool1", 123]})
        assert any("'allowedTools' must contain only strings" in e for e in errs)

        # Valid list
        errs = validate_agent_definition({**base, "allowedTools": ["tool1", "tool2"]})
        assert errs == []

    def test_validate_spawnable_agents(self):
        base = {"id": "a", "displayName": "A"}
        # Not a list
        errs = validate_agent_definition({**base, "spawnableAgents": "coder"})
        assert any("'spawnableAgents' must be a list of strings" in e for e in errs)

        # List with non-strings
        errs = validate_agent_definition({**base, "spawnableAgents": ["coder", None]})
        assert any("'spawnableAgents' must contain only strings" in e for e in errs)

        # Valid list
        errs = validate_agent_definition({**base, "spawnableAgents": ["coder", "tester"]})
        assert errs == []

    def test_validate_input_schema(self):
        base = {"id": "a", "displayName": "A"}
        # Not a dict
        errs = validate_agent_definition({**base, "inputSchema": "not-a-dict"})
        assert any("'inputSchema' must be a dict" in e for e in errs)

        # Valid dict
        errs = validate_agent_definition({**base, "inputSchema": {"type": "object"}})
        assert errs == []

    def test_validate_output_mode(self):
        base = {"id": "a", "displayName": "A"}
        # Invalid output mode
        errs = validate_agent_definition({**base, "outputMode": "invalid_mode"})
        assert any("'outputMode' must be one of" in e for e in errs)

        # Valid modes
        for mode in OUTPUT_MODES:
            errs = validate_agent_definition({**base, "outputMode": mode})
            assert errs == []

    def test_validate_step_hooks(self):
        base = {"id": "a", "displayName": "A"}
        # Not a dict
        errs = validate_agent_definition({**base, "stepHooks": ["hook1"]})
        assert any("'stepHooks' must be a dict" in e for e in errs)

        # Unknown hook key
        errs = validate_agent_definition({**base, "stepHooks": {"unknown_hook": None}})
        assert any("Unknown stepHook: 'unknown_hook'" in e for e in errs)

        # Valid hook keys
        valid_hooks = {h: None for h in STEP_HOOKS}
        errs = validate_agent_definition({**base, "stepHooks": valid_hooks})
        assert errs == []

    def test_merge_definition_defaults(self):
        minimal = {"id": "a", "displayName": "A"}
        merged = merge_definition_defaults(minimal)
        assert merged["allowedTools"] == [ALL_TOOLS]
        assert merged["spawnableAgents"] == []
        assert merged["outputMode"] == "last_message"
        assert merged["stepHooks"] == {}
        assert merged["id"] == "a"
        assert merged["displayName"] == "A"

        # Preserves custom attributes
        custom = {
            "id": "b",
            "displayName": "B",
            "allowedTools": ["custom_tool"],
            "outputMode": "structured",
        }
        merged_custom = merge_definition_defaults(custom)
        assert merged_custom["allowedTools"] == ["custom_tool"]
        assert merged_custom["outputMode"] == "structured"


# ---------------------------------------------------------------------------
# src.core.agent_base
# ---------------------------------------------------------------------------
class ConcreteDummyAgent(AgentBase):
    def plan(self, input_data: str) -> list[Task]:
        return [
            Task(id="t1", description="task 1", input={"raw": input_data}),
        ]

    def execute(self, task: Task) -> Result:
        if task.input.get("fail_first") and getattr(self, "_attempts", 0) == 0:
            self._attempts = 1
            return Result(task_id=task.id, success=False, error="first attempt fail")
        return Result(task_id=task.id, success=True, output="dummy_success")


class TestAgentBase:
    def test_task_and_result_dataclasses(self):
        task = Task(id="1", description="desc", input={"k": "v"})
        assert task.status == TaskStatus.PENDING
        assert task.output is None
        assert task.error is None

        res = Result(task_id="1", success=True, output="out")
        assert res.success is True
        assert res.output == "out"

    def test_subclass_warning_on_missing_methods(self):
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            type(
                "WarnAgent",
                (AgentBase,),
                {"plan": lambda s, x: [], "__abstractmethods__": frozenset({"execute", "other"})},
            )
            assert any("does not implement" in str(w.message) for w in recorded)

    def test_agent_init_and_repr(self):
        agent = ConcreteDummyAgent(
            name="tester_agent",
            max_retries=2,
            allowed_tools=["toolA"],
            spawnable_agents=["subAgent"],
            output_mode="structured",
            step_hooks={"on_step_start": None},
        )
        assert agent.name == "tester_agent"
        assert agent.max_retries == 2
        assert agent.allowed_tools == ["toolA"]
        assert agent.spawnable_agents == ["subAgent"]
        assert agent.output_mode == "structured"
        assert "<Agent:tester_agent tasks=0>" in repr(agent)

    def test_verify_default(self):
        agent = ConcreteDummyAgent(name="tester")
        assert agent.verify(Result(task_id="1", success=True)) is True
        assert agent.verify(Result(task_id="1", success=False)) is False

    @pytest.mark.asyncio
    async def test_fire_hook(self):
        sync_called = False
        async_called = False

        def sync_hook(**kwargs):
            nonlocal sync_called
            sync_called = True

        async def async_hook(**kwargs):
            nonlocal async_called
            async_called = True

        def failing_hook(**kwargs):
            raise RuntimeError("Hook crash")

        agent = ConcreteDummyAgent(
            name="tester",
            step_hooks={
                "on_step_start": sync_hook,
                "on_step_end": async_hook,
                "on_error": failing_hook,
            },
        )

        # Hook None
        await agent._fire_hook("non_existent_hook")

        # Sync hook
        await agent._fire_hook("on_step_start")
        assert sync_called is True

        # Async hook
        await agent._fire_hook("on_step_end")
        assert async_called is True

        # Failing hook (ignored without raising)
        await agent._fire_hook("on_error")

    def test_run_success(self):
        agent = ConcreteDummyAgent(name="test")
        results = agent.run("some input")
        assert len(results) == 1
        assert results[0].success is True
        assert results[0].output == "dummy_success"
        assert agent.tasks[0].status == TaskStatus.SUCCESS

    def test_run_retry_success(self):
        agent = ConcreteDummyAgent(name="test", max_retries=3)
        agent._attempts = 0
        results = agent.run("fail_first")
        # Second attempt succeeds
        assert len(results) == 1
        assert results[0].success is True
        assert agent.tasks[0].status == TaskStatus.SUCCESS

    def test_run_max_retries_exceeded(self):
        class AlwaysFailAgent(AgentBase):
            def plan(self, input_data: str) -> list[Task]:
                return [Task(id="fail_t", description="fail", input={})]

            def execute(self, task: Task) -> Result:
                return Result(task_id=task.id, success=False, error="permanent fail")

        agent = AlwaysFailAgent(name="failer", max_retries=2)
        results = agent.run("input")
        assert len(results) == 1
        assert results[0].success is False
        assert agent.tasks[0].status == TaskStatus.FAILED
        assert agent.tasks[0].error == "permanent fail"


# ---------------------------------------------------------------------------
# src.core.context_flow
# ---------------------------------------------------------------------------
class TestContextFlow:
    def test_agent_contribution_dataclass(self):
        c = AgentContribution(agent_role="cfo", output="Out", status="DONE")
        assert c.agent_role == "cfo"
        assert c.concerns == ""
        assert len(c.timestamp) > 0

    def test_get_context_empty(self, tmp_path):
        flow = ContextFlow(task_id="empty", mekong_dir=str(tmp_path))
        assert flow.get_context_for("cfo") == ""

    def test_get_context_with_concerns(self, tmp_path):
        flow = ContextFlow(task_id="t1", mekong_dir=str(tmp_path))
        flow.add("cfo", "Financial check ready", status="DONE_WITH_CONCERNS", concerns="High burn rate")
        context = flow.get_context_for("ceo")
        assert "### CFO reported:" in context
        assert "Financial check ready" in context
        assert "⚠️ Concerns: High burn rate" in context
        assert "[YOUR ROLE: CEO" in context

    def test_get_summary_with_blocker(self, tmp_path):
        flow = ContextFlow(task_id="t2", mekong_dir=str(tmp_path))
        flow.add("dev", "API broken", status="BLOCKED", concerns="Database unreachable")
        summary = flow.get_summary()
        assert "⛔ BLOCKED at: dev" in summary
        assert flow.has_blocker() is True

    def test_get_summary_all_done(self, tmp_path):
        flow = ContextFlow(task_id="t_done", mekong_dir=str(tmp_path))
        flow.add("dev", "Feature coded", status="DONE")
        flow.add("qa", "Tests passed", status="DONE")
        summary = flow.get_summary()
        assert "✅ All DONE" in summary
        assert flow.has_blocker() is False

    def test_get_summary_mixed_statuses(self, tmp_path):
        flow = ContextFlow(task_id="t3", mekong_dir=str(tmp_path))
        flow.add("dev", "Review done", status="DONE_WITH_CONCERNS")
        flow.add("ops", "Deploying", status="NEEDS_CONTEXT")
        summary = flow.get_summary()
        assert "Statuses: dev=DONE_WITH_CONCERNS, ops=NEEDS_CONTEXT" in summary
        assert flow.has_blocker() is False

    def test_save_oserror_handled(self, tmp_path):
        flow = ContextFlow(task_id="t4", mekong_dir=str(tmp_path))
        with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
            # Should not raise exception
            flow.add("cfo", "Done")

    def test_load_handles_corrupt_or_error_files(self, tmp_path):
        flow_file = tmp_path / "flows" / "corrupt.json"
        flow_file.parent.mkdir(parents=True, exist_ok=True)

        # Corrupt JSON
        flow_file.write_text("invalid json{{")
        flow = ContextFlow.load("corrupt", mekong_dir=str(tmp_path))
        assert flow.contributions == []

        # Schema/type error
        flow_file.write_text(json.dumps([{"unexpected": 123}]))
        flow2 = ContextFlow.load("corrupt", mekong_dir=str(tmp_path))
        assert flow2.contributions == []

        # Non-existent file
        flow3 = ContextFlow.load("non_existent", mekong_dir=str(tmp_path))
        assert flow3.contributions == []

        # OSError on read
        with patch.object(Path, "read_text", side_effect=OSError("Read failure")):
            flow4 = ContextFlow.load("corrupt", mekong_dir=str(tmp_path))
            assert flow4.contributions == []


# ---------------------------------------------------------------------------
# src.core.workflow_state
# ---------------------------------------------------------------------------
class TestWorkflowState:
    def test_enums(self):
        assert WorkflowStatus.PENDING == "pending"
        assert StepStatus.SCHEDULED == "scheduled"

    def test_step_state_valid_and_invalid_transitions(self):
        step = StepState(order=1)
        assert step.status == StepStatus.SCHEDULED

        step.transition(StepStatus.STARTED)
        assert step.status == StepStatus.STARTED

        step.transition(StepStatus.COMPLETED)
        assert step.status == StepStatus.COMPLETED

        # COMPLETED cannot transition directly to STARTED
        with pytest.raises(InvalidTransitionError) as exc_info:
            step.transition(StepStatus.STARTED)
        assert "not allowed" in str(exc_info.value)

    def test_workflow_state_valid_and_invalid_transitions(self):
        wf = WorkflowState(workflow_id="wf-1")
        assert wf.status == WorkflowStatus.PENDING

        wf.transition(WorkflowStatus.RUNNING)
        assert wf.status == WorkflowStatus.RUNNING

        wf.transition(WorkflowStatus.COMPLETED)
        assert wf.status == WorkflowStatus.COMPLETED

        # COMPLETED is terminal, cannot transition to RUNNING
        with pytest.raises(InvalidTransitionError) as exc_info:
            wf.transition(WorkflowStatus.RUNNING)
        assert "not allowed" in str(exc_info.value)

    def test_step_transition_updates_current_step_and_attempts(self):
        wf = WorkflowState(workflow_id="wf-2")
        wf.register_steps(3)
        assert len(wf.steps) == 3

        # Step 2 STARTED updates current_step
        wf.step_transition(2, StepStatus.STARTED)
        assert wf.current_step == 2

        # Step 2 FAILED
        wf.step_transition(2, StepStatus.FAILED)

        # Step 2 RETRYING increments attempt
        assert wf.steps[2].attempt == 0
        wf.step_transition(2, StepStatus.RETRYING)
        assert wf.steps[2].attempt == 1

        # Key error on unknown step
        with pytest.raises(KeyError):
            wf.step_transition(99, StepStatus.STARTED)

    def test_get_completed_and_failed_steps(self):
        wf = WorkflowState(workflow_id="wf-3")
        wf.register_steps(3)
        wf.step_transition(1, StepStatus.STARTED)
        wf.step_transition(1, StepStatus.COMPLETED)

        wf.step_transition(2, StepStatus.STARTED)
        wf.step_transition(2, StepStatus.FAILED)

        assert wf.get_completed_steps() == [1]
        assert wf.get_failed_steps() == [2]

    def test_is_terminal(self):
        wf = WorkflowState(workflow_id="wf-4")
        assert wf.is_terminal is False

        wf.status = WorkflowStatus.RUNNING
        assert wf.is_terminal is False

        wf.status = WorkflowStatus.COMPLETED
        assert wf.is_terminal is True

        wf.status = WorkflowStatus.CANCELLED
        assert wf.is_terminal is True

        wf.status = WorkflowStatus.ROLLED_BACK
        assert wf.is_terminal is True

    def test_progress(self):
        wf = WorkflowState(workflow_id="wf-5")
        # Empty steps
        assert wf.progress == 0.0

        wf.register_steps(4)
        assert wf.progress == 0.0

        wf.step_transition(1, StepStatus.STARTED)
        wf.step_transition(1, StepStatus.COMPLETED)
        assert wf.progress == 25.0

        wf.step_transition(2, StepStatus.STARTED)
        wf.step_transition(2, StepStatus.COMPLETED)
        assert wf.progress == 50.0


# ---------------------------------------------------------------------------
# src.core.rate_limit_client & src.core.rate_limit
# ---------------------------------------------------------------------------
class TestRateLimitClient:
    def test_rate_limit_status_dataclass(self):
        st = RateLimitStatus(allowed=True, remaining=50, limit=100, reset_in=30)
        assert st.allowed is True
        assert st.remaining == 50

    def test_can_proceed(self):
        client = RateLimitClient()
        assert client.can_proceed() is True

        client._remaining = 0
        client._last_retry = time.time()
        client._reset_in = 60
        # Wait period active
        assert client.can_proceed() is False

        # Wait period expired
        client._last_retry = time.time() - 100
        assert client.can_proceed() is True

    def test_handle_429_with_retry_after(self):
        client = RateLimitClient()
        resp = requests.Response()
        resp.headers["Retry-After"] = "45"
        resp.headers["X-RateLimit-Limit"] = "200"
        resp.headers["X-RateLimit-Remaining"] = "0"

        client.handle_429(resp)
        assert client._reset_in == 45
        assert client._limit == 200
        assert client._remaining == 0
        assert client._retry_count == 1

    def test_handle_429_without_retry_after_and_unlimited(self):
        client = RateLimitClient()
        resp = requests.Response()
        resp.headers["X-RateLimit-Limit"] = "unlimited"
        resp.headers["X-RateLimit-Remaining"] = "unlimited"

        client.handle_429(resp)
        # Base delay * 2^(1-1) = 1.0
        assert client._reset_in == 1.0
        assert client._limit == client.DEFAULT_LIMIT
        assert client._remaining == 0

        # Second 429
        client.handle_429(resp)
        assert client._reset_in == 2.0
        assert client._retry_count == 2

    def test_update_from_headers(self):
        client = RateLimitClient()
        headers = {
            "X-RateLimit-Limit": "150",
            "X-RateLimit-Remaining": "75",
            "X-RateLimit-Reset": "25",
        }
        client.update_from_headers(headers)
        assert client._limit == 150
        assert client._remaining == 75
        assert client._reset_in == 25

        # Ignore unlimited
        client.update_from_headers({
            "X-RateLimit-Limit": "unlimited",
            "X-RateLimit-Remaining": "unlimited",
        })
        assert client._limit == 150
        assert client._remaining == 75

    def test_wait_for_reset(self):
        client = RateLimitClient()
        client._reset_in = 10
        client._retry_count = 3
        with patch("time.sleep") as mock_sleep:
            client.wait_for_reset()
            # Sleeps max 5s
            mock_sleep.assert_called_once_with(5)
            assert client._retry_count == 0
            assert client._remaining == client._limit

    def test_get_status_and_reset(self):
        client = RateLimitClient()
        client._remaining = 10
        status = client.get_status()
        assert status.remaining == 10
        assert status.allowed is True

        client.reset()
        assert client._remaining == client.DEFAULT_LIMIT
        assert client._retry_count == 0
        assert client._last_retry is None

    def test_rate_limiter_shim(self):
        assert RateLimiter is RateLimitClient


# ---------------------------------------------------------------------------
# src.core.sentry_init
# ---------------------------------------------------------------------------
class TestSentryInit:
    def test_init_sentry_no_dsn(self, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        with patch("sentry_sdk.init") as mock_init:
            init_sentry()
            mock_init.assert_not_called()

    def test_init_sentry_with_dsn(self, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/12345")
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.setenv("APP_VERSION", "6.0.1")

        with patch("sentry_sdk.init") as mock_init:
            init_sentry()
            mock_init.assert_called_once_with(
                dsn="https://key@sentry.io/12345",
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment="staging",
                release="6.0.1",
            )


# ---------------------------------------------------------------------------
# src.core.rollback & src.core.orchestrator.rollback
# ---------------------------------------------------------------------------
class TestRollback:
    def test_rollback_shim_exports(self):
        import src.core.orchestrator.rollback as orch_rollback
        assert RollbackHandler is orch_rollback.RollbackHandler
        assert handle_failure is orch_rollback.handle_failure

    def test_rollback_handler_disabled(self):
        handler = RollbackHandler(enable_rollback=False)
        recipe = Recipe(name="test", description="")
        res = OrchestrationResult(status=OrchestrationStatus.FAILED, recipe=recipe)
        failed_step = RecipeStep(order=1, title="step1", description="")
        handler.rollback(res, failed_step)
        assert res.status == OrchestrationStatus.FAILED

    def test_rollback_handler_sanitizer_init_exception(self):
        with patch("src.core.command_sanitizer.CommandSanitizer", side_effect=ImportError("no sanitizer")):
            handler = RollbackHandler(enable_rollback=True)
            assert handler._sanitizer is None

    def test_rollback_handler_execution(self):
        step_passed = RecipeStep(order=1, title="s1", description="", params={"rollback": "echo passed"})
        step_no_rollback = RecipeStep(order=2, title="s2", description="", params={})
        step_unpassed = RecipeStep(order=3, title="s3", description="", params={"rollback": "echo unpassed"})
        step_blocked = RecipeStep(order=4, title="s4", description="", params={"rollback": "rm -rf /"})
        step_failed_proc = RecipeStep(order=5, title="s5", description="", params={"rollback": "false"})
        step_timeout = RecipeStep(order=6, title="s6", description="", params={"rollback": "sleep 100"})
        step_exception = RecipeStep(order=7, title="s7", description="", params={"rollback": "error_cmd"})

        def make_sr(step, passed=True):
            return StepResult(
                step=step,
                execution=ExecutionResult(exit_code=0),
                verification=VerificationReport(passed=passed),
            )

        step_results = [
            make_sr(step_passed, passed=True),
            make_sr(step_no_rollback, passed=True),
            make_sr(step_unpassed, passed=False),
            make_sr(step_blocked, passed=True),
            make_sr(step_failed_proc, passed=True),
            make_sr(step_timeout, passed=True),
            make_sr(step_exception, passed=True),
        ]

        recipe = Recipe(name="test", description="")
        res = OrchestrationResult(status=OrchestrationStatus.FAILED, recipe=recipe, step_results=step_results)

        handler = RollbackHandler(enable_rollback=True)

        def mock_run(cmd, capture_output=True, text=True, timeout=30):
            if cmd == ["echo", "passed"]:
                return subprocess.CompletedProcess(cmd, returncode=0, stdout="ok", stderr="")
            if cmd == ["false"]:
                return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="command failed")
            if cmd == ["sleep", "100"]:
                raise subprocess.TimeoutExpired(cmd, timeout=30)
            if cmd == ["error_cmd"]:
                raise RuntimeError("custom crash")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            handler.rollback(res, step_failed_proc)

        assert res.status == OrchestrationStatus.ROLLED_BACK
        assert "Rollback completed with errors" in res.warnings
        assert any("rollback blocked (security)" in e for e in res.errors)
        assert any("rollback failed: command failed" in e for e in res.errors)
        assert any("rollback timed out" in e for e in res.errors)
        assert any("rollback error: custom crash" in e for e in res.errors)

    def test_handle_failure_function(self):
        console = MagicMock(spec=Console)
        step_passed = RecipeStep(order=1, title="s1", description="", params={"rollback": "echo 1"})
        step_list_args = RecipeStep(order=2, title="s2", description="", params={"rollback": ["echo", "list"]})
        step_no_cmd = RecipeStep(order=3, title="s3", description="", params={})
        step_not_verified = RecipeStep(order=4, title="s4", description="", params={"rollback": "echo skip"})
        step_fail_code = RecipeStep(order=5, title="s5", description="", params={"rollback": "false"})
        step_timeout = RecipeStep(order=6, title="s6", description="", params={"rollback": "sleep 10"})
        step_exc = RecipeStep(order=7, title="s7", description="", params={"rollback": "crash"})

        def make_sr(step, passed=True):
            return StepResult(
                step=step,
                execution=ExecutionResult(exit_code=0),
                verification=VerificationReport(passed=passed),
            )

        step_results = [
            make_sr(step_passed, passed=True),
            make_sr(step_list_args, passed=True),
            make_sr(step_no_cmd, passed=True),
            make_sr(step_not_verified, passed=False),
            make_sr(step_fail_code, passed=True),
            make_sr(step_timeout, passed=True),
            make_sr(step_exc, passed=True),
        ]

        recipe = Recipe(name="test", description="")

        # Test disabled rollback
        res_disabled = OrchestrationResult(status=OrchestrationStatus.FAILED, recipe=recipe, step_results=step_results)
        handle_failure(res_disabled, step_fail_code, enable_rollback=False, console=console)
        assert res_disabled.status == OrchestrationStatus.FAILED

        # Test enabled rollback
        res_enabled = OrchestrationResult(status=OrchestrationStatus.FAILED, recipe=recipe, step_results=step_results)

        def mock_subprocess_run(args, shell=False, capture_output=True, text=True, timeout=30):
            if args == ["echo", "1"] or args == ["echo", "list"]:
                return subprocess.CompletedProcess(args, returncode=0, stdout="ok", stderr="")
            if args == ["false"]:
                return subprocess.CompletedProcess(args, returncode=1, stdout="", stderr="proc fail")
            if args == ["sleep", "10"]:
                raise subprocess.TimeoutExpired(args, timeout=30)
            if args == ["crash"]:
                raise RuntimeError("bad command")
            return subprocess.CompletedProcess(args, returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_subprocess_run):
            handle_failure(res_enabled, step_fail_code, enable_rollback=True, console=console)

        assert res_enabled.status == OrchestrationStatus.ROLLED_BACK
        assert "Rollback completed with errors" in res_enabled.warnings
        assert any("rollback failed: proc fail" in e for e in res_enabled.errors)
        assert any("rollback timed out" in e for e in res_enabled.errors)
        assert any("rollback error: bad command" in e for e in res_enabled.errors)
