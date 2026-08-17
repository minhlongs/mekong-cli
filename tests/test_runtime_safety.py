# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for MekongCoreRuntimeImpl safety gates — governance, cost, retry limit."""

from unittest.mock import MagicMock, patch

from src.core.governance import Governance
from src.core.runtime_adapter import (
    MekongCoreRuntimeImpl,
    RepairStrategy,
    Task,
    AgentId,
    Verification,
    CheckResult,
    CheckSpec,
    Result,
)
from src.core.protocols import Step


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeDispatcher:
    def dispatch(self, task, agent=None):
        return {"dispatched": True}


class _FakeToolRegistry:
    def execute(self, tool_id, params):
        return {"ok": True}


def _make_task(tool: str = "test-tool", description: str = "read file") -> Task:
    step = Step(id="step-0", description=description, params={})
    return Task(
        id="task-test",
        step=step,
        agent=AgentId(name="test-agent"),
        params={"tool": tool, "description": description},
    )


def _ok_result(task_id: str = "task-test") -> Result:
    return Result(task_id=task_id, output={"ok": True}, error=None, metadata={})


def _fail_result(task_id: str = "task-test", error: str = "boom") -> Result:
    return Result(task_id=task_id, output=None, error=error, metadata={})


def _ok_verification() -> Verification:
    return Verification(passed=True, checks=[], failures=[])


def _fail_verification(errors: list[str] | None = None) -> Verification:
    errs = errors or ["exit_code failed"]
    checks = [CheckResult(check=CheckSpec(kind="exit_code"), passed=False, detail=e) for e in errs]
    return Verification(passed=False, checks=checks, failures=errs)


# ---------------------------------------------------------------------------
# Tests: execute + governance gate
# ---------------------------------------------------------------------------

class TestExecuteGovernanceGate:
    @patch("src.core.governance.Governance._load_audit", lambda self: None)
    @patch("src.core.governance.os.path.exists", return_value=False)
    def test_blocks_forbidden_action(self, _mock_exists):
        gov = Governance(audit_path="/dev/null")
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            governance=gov,
        )
        task = _make_task(description="drop table users")
        result = runtime.execute(task)
        assert result.error is not None
        assert "forbidden" in result.error.lower()
        assert result.output is None

    @patch("src.core.governance.Governance._load_audit", lambda self: None)
    @patch("src.core.governance.os.path.exists", return_value=False)
    def test_allows_safe_action(self, _mock_exists):
        gov = Governance(audit_path="/dev/null")
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            governance=gov,
        )
        task = _make_task(description="read file report.csv")
        result = runtime.execute(task)
        assert result.error is None
        assert result.output is not None

    @patch("src.core.governance.Governance._load_audit", lambda self: None)
    @patch("src.core.governance.os.path.exists", return_value=False)
    def test_blocks_rm_rf(self, _mock_exists):
        gov = Governance(audit_path="/dev/null")
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            governance=gov,
        )
        task = _make_task(description="rm -rf /tmp/data")
        result = runtime.execute(task)
        assert result.error is not None
        assert "forbidden" in result.error.lower()


class TestExecuteWithoutGovernance:
    def test_execute_without_governance_still_works(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        assert runtime._governance is None
        task = _make_task(tool="test-tool", description="any goal here")
        result = runtime.execute(task)
        assert result.error is None
        # tool="test-tool" is truthy so tool_registry.execute runs first
        assert result.output == {"ok": True}

    def test_governance_none_bypasses_gate(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            governance=None,
        )
        task = _make_task(tool=None, description="drop table everything")
        result = runtime.execute(task)
        assert result.error is None


# ---------------------------------------------------------------------------
# Tests: execute + retry limit gate
# ---------------------------------------------------------------------------

class TestExecuteRetryGate:
    def test_execute_blocks_after_max_retries(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        runtime._repair_count = 3
        task = _make_task(description="anything")
        result = runtime.execute(task)
        assert result.error is not None
        assert "max repair retries" in result.error.lower()


# ---------------------------------------------------------------------------
# Tests: execute + cost estimate gate
# ---------------------------------------------------------------------------

class TestExecuteCostGate:
    def test_cost_estimate_called_before_execute(self):
        mock_llm = MagicMock()
        mock_llm.estimate_cost.return_value = {"tokens": 25, "cost_usd": 0.001}
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            llm_router=mock_llm,
        )
        task = _make_task(description="analyze this text")
        result = runtime.execute(task)
        mock_llm.estimate_cost.assert_called_once()
        assert "estimated_cost" in result.metadata

    def test_cost_estimate_failure_does_not_block(self):
        mock_llm = MagicMock()
        mock_llm.estimate_cost.side_effect = RuntimeError("pricing unavailable")
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            llm_router=mock_llm,
        )
        task = _make_task(description="do something")
        result = runtime.execute(task)
        assert result.error is None


# ---------------------------------------------------------------------------
# Tests: repair retry limit
# ---------------------------------------------------------------------------

class TestRepairRetryLimit:
    def test_repair_increments_count(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        assert runtime._repair_count == 0
        runtime.repair(_fail_verification())
        assert runtime._repair_count == 1
        runtime.repair(_fail_verification())
        assert runtime._repair_count == 2

    def test_repair_aborts_after_max_retries(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        # Exhaust 3 retries
        runtime.repair(_fail_verification())
        runtime.repair(_fail_verification())
        runtime.repair(_fail_verification())
        assert runtime._repair_count == 3
        # 4th call should abort
        action = runtime.repair(_fail_verification())
        assert action.strategy == RepairStrategy.ESCALATE
        assert runtime._repair_count == 3  # not incremented past limit

    def test_repair_returns_retry_for_retriable_errors(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        action = runtime.repair(_fail_verification(["error in output"]))
        assert action.strategy == RepairStrategy.RETRY

    def test_repair_returns_fallback_for_non_errors(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        action = runtime.repair(_fail_verification(["output check failed"]))
        assert action.strategy == RepairStrategy.FALLBACK

    def test_repair_returns_retry_when_no_failures(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        action = runtime.repair(_ok_verification())
        assert action.strategy == RepairStrategy.RETRY


# ---------------------------------------------------------------------------
# Tests: integration — execute + retry gate together
# ---------------------------------------------------------------------------

class TestSafetyGatesIntegration:
    @patch("src.core.governance.Governance._load_audit", lambda self: None)
    @patch("src.core.governance.os.path.exists", return_value=False)
    def test_all_gates_stack(self, _mock_exists):
        gov = Governance(audit_path="/dev/null")
        mock_llm = MagicMock()
        mock_llm.estimate_cost.return_value = 0.01
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            governance=gov,
            llm_router=mock_llm,
        )
        # Safe action with cost estimate
        task = _make_task(description="read file data.csv")
        result = runtime.execute(task)
        assert result.error is None
        assert "estimated_cost" in result.metadata
        mock_llm.estimate_cost.assert_called_once()
