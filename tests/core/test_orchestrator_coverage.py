"""Additional coverage tests for src/core/orchestrator.py.

Targets uncovered branches in:
- RecipeOrchestrator.__init__ (AGI v2 optional component loading)
- RecipeOrchestrator.run_from_recipe (DAG path, sequential path, rollback)
- RecipeOrchestrator._handle_failure (rollback with/without rollback cmds)
- RecipeOrchestrator._display_report / _format_status
- RecipeOrchestrator._post_execution_agi
- OrchestrationResult properties
"""

from __future__ import annotations

import sys
import os
import subprocess
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from src.core.orchestrator import (
    OrchestrationResult,
    OrchestrationStatus,
    RecipeOrchestrator,
    StepResult,
)
from src.core.parser import Recipe, RecipeStep
from src.core.verifier import (
    ExecutionResult,
    VerificationCheck,
    VerificationReport,
    VerificationStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recipe(name: str = "r", steps: list | None = None) -> Recipe:
    return Recipe(name=name, description="desc", steps=steps or [], metadata={})


def _step(
    order: int = 1,
    title: str = "step",
    desc: str = "echo hi",
    params: dict | None = None,
    deps: list | None = None,
) -> RecipeStep:
    return RecipeStep(
        order=order,
        title=title,
        description=desc,
        params=params or {},
        dependencies=deps or [],
    )


def _ok_exec() -> ExecutionResult:
    return ExecutionResult(exit_code=0, stdout="ok", stderr="")


def _fail_exec(stderr: str = "err") -> ExecutionResult:
    return ExecutionResult(exit_code=1, stdout="", stderr=stderr)


def _pass_report() -> VerificationReport:
    return VerificationReport(
        passed=True,
        checks=[VerificationCheck(
            name="exit_code", status=VerificationStatus.PASSED,
            message="ok", expected=0, actual=0,
        )],
    )


def _fail_report(msg: str = "fail") -> VerificationReport:
    return VerificationReport(
        passed=False,
        checks=[VerificationCheck(
            name="exit_code", status=VerificationStatus.FAILED,
            message=msg, expected=0, actual=1,
        )],
        errors=[msg],
    )


def _make_orchestrator(**kwargs) -> RecipeOrchestrator:
    """Build a RecipeOrchestrator with all external I/O mocked."""
    with patch("src.core.orchestrator.RecipePlanner"), \
         patch("src.core.orchestrator.RecipeVerifier"), \
         patch("src.core.orchestrator.TelemetryCollector"), \
         patch("src.core.orchestrator.MemoryStore"), \
         patch("src.core.orchestrator.IntentClassifier"), \
         patch("src.core.orchestrator.ExecutionHistory"), \
         patch("src.core.orchestrator.RetryPolicy"):
        orch = RecipeOrchestrator(**kwargs)
    return orch


# ---------------------------------------------------------------------------
# RecipeOrchestrator.__init__ — optional AGI component loading
# ---------------------------------------------------------------------------

class TestOrchestratorInit:
    def test_default_init_no_swarm(self):
        orch = _make_orchestrator()
        assert orch.dispatcher is None
        assert orch.enable_rollback is True

    def test_enable_rollback_false(self):
        orch = _make_orchestrator(enable_rollback=False)
        assert orch.enable_rollback is False

    def test_agi_components_silently_fail(self):
        """AGI optional imports failing should not raise."""
        with patch("src.core.orchestrator.RecipePlanner"), \
             patch("src.core.orchestrator.RecipeVerifier"), \
             patch("src.core.orchestrator.TelemetryCollector"), \
             patch("src.core.orchestrator.MemoryStore"), \
             patch("src.core.orchestrator.IntentClassifier"), \
             patch("src.core.orchestrator.ExecutionHistory"), \
             patch("src.core.orchestrator.RetryPolicy"), \
             patch.dict("sys.modules", {
                 "src.core.reflection": None,
                 "src.core.world_model": None,
                 "src.core.tool_registry": None,
             }):
            orch = RecipeOrchestrator()
        # Should be None or objects — just no exception
        assert orch is not None

    def test_swarm_dispatcher_created(self):
        """use_swarm=True creates a SwarmDispatcher (import happens inside __init__)."""
        mock_dispatcher = Mock()
        mock_swarm_mod = MagicMock()
        mock_swarm_mod.SwarmDispatcher.return_value = mock_dispatcher
        mock_swarm_mod.SwarmRegistry.return_value = Mock()
        with patch("src.core.orchestrator.RecipePlanner"), \
             patch("src.core.orchestrator.RecipeVerifier"), \
             patch("src.core.orchestrator.TelemetryCollector"), \
             patch("src.core.orchestrator.MemoryStore"), \
             patch("src.core.orchestrator.IntentClassifier"), \
             patch("src.core.orchestrator.ExecutionHistory"), \
             patch("src.core.orchestrator.RetryPolicy"), \
             patch.dict("sys.modules", {"src.core.swarm": mock_swarm_mod}):
            orch = RecipeOrchestrator(use_swarm=True)
        assert orch.dispatcher is mock_dispatcher


# ---------------------------------------------------------------------------
# OrchestrationResult — all status enum values
# ---------------------------------------------------------------------------

class TestOrchestrationResultCoverage:
    def test_rolled_back_status(self):
        r = OrchestrationResult(
            status=OrchestrationStatus.ROLLED_BACK,
            recipe=_recipe(),
        )
        assert r.status == OrchestrationStatus.ROLLED_BACK

    def test_partial_status(self):
        r = OrchestrationResult(
            status=OrchestrationStatus.PARTIAL,
            recipe=_recipe(),
            total_steps=2,
            completed_steps=1,
            failed_steps=1,
        )
        assert r.success_rate == 50.0

    def test_success_rate_with_warnings_and_errors(self):
        r = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            total_steps=3,
            completed_steps=1,
            failed_steps=2,
            warnings=["warn1"],
            errors=["err1", "err2"],
        )
        assert abs(r.success_rate - 33.333) < 0.01
        assert len(r.errors) == 2
        assert len(r.warnings) == 1


# ---------------------------------------------------------------------------
# RecipeOrchestrator._format_status — all status colors
# ---------------------------------------------------------------------------

class TestFormatStatus:
    def _orch(self):
        return _make_orchestrator()

    def test_format_success(self):
        orch = self._orch()
        result = orch._format_status(OrchestrationStatus.SUCCESS)
        assert "green" in result
        assert "SUCCESS" in result

    def test_format_failed(self):
        orch = self._orch()
        result = orch._format_status(OrchestrationStatus.FAILED)
        assert "red" in result

    def test_format_partial(self):
        orch = self._orch()
        result = orch._format_status(OrchestrationStatus.PARTIAL)
        assert "yellow" in result

    def test_format_rolled_back(self):
        orch = self._orch()
        result = orch._format_status(OrchestrationStatus.ROLLED_BACK)
        assert "magenta" in result


# ---------------------------------------------------------------------------
# RecipeOrchestrator._display_report — errors and warnings rendered
# ---------------------------------------------------------------------------

class TestDisplayReport:
    def test_display_with_errors_and_warnings(self):
        orch = _make_orchestrator()
        r = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            total_steps=1,
            failed_steps=1,
            errors=["something broke"],
            warnings=["heads up"],
        )
        # Should not raise
        orch._display_report(r)

    def test_display_clean_result(self):
        orch = _make_orchestrator()
        r = OrchestrationResult(
            status=OrchestrationStatus.SUCCESS,
            recipe=_recipe(),
            total_steps=2,
            completed_steps=2,
        )
        orch._display_report(r)  # no exception


# ---------------------------------------------------------------------------
# RecipeOrchestrator._handle_failure — rollback paths
# ---------------------------------------------------------------------------

class TestHandleFailure:
    def _orch_with_rollback(self, enable: bool = True) -> RecipeOrchestrator:
        orch = _make_orchestrator(enable_rollback=enable)
        return orch

    def test_rollback_disabled_returns_immediately(self):
        orch = self._orch_with_rollback(enable=False)
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
        )
        failed_step = _step()
        orch._handle_failure(result, failed_step)
        # Status unchanged since rollback is disabled
        assert result.status == OrchestrationStatus.FAILED

    def test_rollback_no_completed_steps(self):
        """No completed steps → no rollback commands run."""
        orch = self._orch_with_rollback()
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[],
        )
        orch._handle_failure(result, _step())
        assert result.status == OrchestrationStatus.ROLLED_BACK

    def test_rollback_step_without_rollback_cmd(self):
        """Passed step with no rollback param → skipped gracefully."""
        orch = self._orch_with_rollback()
        passed_sr = StepResult(
            step=_step(order=1, params={}),
            execution=_ok_exec(),
            verification=_pass_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[passed_sr],
        )
        orch._handle_failure(result, _step(order=2))
        assert result.status == OrchestrationStatus.ROLLED_BACK

    def test_rollback_step_with_cmd_succeeds(self):
        """Rollback command runs and succeeds."""
        orch = self._orch_with_rollback()
        passed_sr = StepResult(
            step=_step(order=1, params={"rollback": "echo rollback"}),
            execution=_ok_exec(),
            verification=_pass_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[passed_sr],
        )
        mock_proc = Mock()
        mock_proc.returncode = 0
        mock_proc.stderr = ""
        with patch("subprocess.run", return_value=mock_proc):
            orch._handle_failure(result, _step(order=2))
        assert result.status == OrchestrationStatus.ROLLED_BACK
        assert not result.errors or all("rollback" not in e for e in result.errors)

    def test_rollback_step_cmd_fails(self):
        """Rollback command fails → error appended."""
        orch = self._orch_with_rollback()
        passed_sr = StepResult(
            step=_step(order=1, params={"rollback": "exit 1"}),
            execution=_ok_exec(),
            verification=_pass_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[passed_sr],
            errors=[],
        )
        mock_proc = Mock()
        mock_proc.returncode = 1
        mock_proc.stderr = "rollback error"
        with patch("subprocess.run", return_value=mock_proc):
            orch._handle_failure(result, _step(order=2))
        assert result.status == OrchestrationStatus.ROLLED_BACK
        assert any("rollback" in e.lower() for e in result.errors)

    def test_rollback_cmd_timeout(self):
        """Rollback command times out → error appended."""
        orch = self._orch_with_rollback()
        passed_sr = StepResult(
            step=_step(order=1, params={"rollback": "sleep 999"}),
            execution=_ok_exec(),
            verification=_pass_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[passed_sr],
            errors=[],
        )
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            orch._handle_failure(result, _step(order=2))
        assert any("timed out" in e for e in result.errors)

    def test_rollback_cmd_exception(self):
        """Rollback command raises unexpected exception → error appended."""
        orch = self._orch_with_rollback()
        passed_sr = StepResult(
            step=_step(order=1, params={"rollback": "bad cmd"}),
            execution=_ok_exec(),
            verification=_pass_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[passed_sr],
            errors=[],
        )
        with patch("subprocess.run", side_effect=OSError("permission denied")):
            orch._handle_failure(result, _step(order=2))
        assert any("rollback error" in e.lower() for e in result.errors)

    def test_rollback_skips_failed_step_results(self):
        """Failed step results are skipped during rollback iteration."""
        orch = self._orch_with_rollback()
        failed_sr = StepResult(
            step=_step(order=1, params={"rollback": "echo should-not-run"}),
            execution=_fail_exec(),
            verification=_fail_report(),
        )
        result = OrchestrationResult(
            status=OrchestrationStatus.FAILED,
            recipe=_recipe(),
            step_results=[failed_sr],
            errors=[],
        )
        with patch("subprocess.run") as mock_run:
            orch._handle_failure(result, _step(order=2))
        mock_run.assert_not_called()


# ---------------------------------------------------------------------------
# RecipeOrchestrator.run_from_recipe — sequential path
# ---------------------------------------------------------------------------

class TestRunFromRecipeSequential:
    def _setup_orch(self, enable_rollback: bool = True) -> RecipeOrchestrator:
        orch = _make_orchestrator(enable_rollback=enable_rollback)
        return orch

    def _patch_step_exec(self, orch, report: VerificationReport):
        """Patch _execute_and_verify_step to return given verification."""
        step = _step()
        mock_result = StepResult(
            step=step,
            execution=_ok_exec() if report.passed else _fail_exec(),
            verification=report,
        )
        orch._execute_and_verify_step = Mock(return_value=mock_result)
        return mock_result

    def test_empty_recipe_succeeds(self):
        orch = self._setup_orch()
        recipe = _recipe(steps=[])
        result = orch.run_from_recipe(recipe)
        assert result.status == OrchestrationStatus.SUCCESS
        assert result.completed_steps == 0

    def test_single_step_success(self):
        orch = self._setup_orch()
        step = _step(order=1)
        recipe = _recipe(steps=[step])

        sr = StepResult(step=step, execution=_ok_exec(), verification=_pass_report())
        orch._execute_and_verify_step = Mock(return_value=sr)

        result = orch.run_from_recipe(recipe)
        assert result.status == OrchestrationStatus.SUCCESS
        assert result.completed_steps == 1

    def test_step_failure_triggers_rollback(self):
        orch = self._setup_orch(enable_rollback=True)
        step = _step(order=1)
        recipe = _recipe(steps=[step])

        sr = StepResult(step=step, execution=_fail_exec(), verification=_fail_report("boom"))
        orch._execute_and_verify_step = Mock(return_value=sr)
        orch._handle_failure = Mock()

        result = orch.run_from_recipe(recipe)
        orch._handle_failure.assert_called_once()
        assert result.failed_steps == 1

    def test_step_failure_no_rollback_sets_partial(self):
        orch = self._setup_orch(enable_rollback=False)
        step = _step(order=1)
        recipe = _recipe(steps=[step])

        sr = StepResult(step=step, execution=_fail_exec(), verification=_fail_report("oops"))
        orch._execute_and_verify_step = Mock(return_value=sr)

        result = orch.run_from_recipe(recipe)
        assert result.status == OrchestrationStatus.PARTIAL

    def test_progress_callback_called(self):
        orch = self._setup_orch()
        step = _step(order=1)
        recipe = _recipe(steps=[step])

        sr = StepResult(step=step, execution=_ok_exec(), verification=_pass_report())
        orch._execute_and_verify_step = Mock(return_value=sr)
        cb = Mock()

        orch.run_from_recipe(recipe, progress_callback=cb)
        cb.assert_called_once()

    def test_warnings_collected(self):
        orch = self._setup_orch()
        step = _step(order=1)
        recipe = _recipe(steps=[step])

        warn_report = VerificationReport(
            passed=True,
            checks=[],
            warnings=["minor issue"],
        )
        sr = StepResult(step=step, execution=_ok_exec(), verification=warn_report)
        orch._execute_and_verify_step = Mock(return_value=sr)

        result = orch.run_from_recipe(recipe)
        assert any("minor issue" in w for w in result.warnings)

    def test_multi_step_all_succeed(self):
        orch = self._setup_orch()
        steps = [_step(order=i) for i in range(1, 4)]
        recipe = _recipe(steps=steps)

        def _make_sr(step, *args, **kwargs):
            return StepResult(step=step, execution=_ok_exec(), verification=_pass_report())

        orch._execute_and_verify_step = Mock(side_effect=_make_sr)

        result = orch.run_from_recipe(recipe)
        assert result.completed_steps == 3
        assert result.status == OrchestrationStatus.SUCCESS


# ---------------------------------------------------------------------------
# RecipeOrchestrator._post_execution_agi — optional AGI callbacks
# ---------------------------------------------------------------------------

class TestPostExecutionAgi:
    def test_post_execution_no_agi_components(self):
        """With no AGI components set, _post_execution_agi must not raise."""
        orch = _make_orchestrator()
        orch._reflection = None
        orch._world_model = None
        orch._code_evolution = None
        orch._vector_memory = None
        orch._collaboration = None
        # Must not raise
        orch._post_execution_agi("test goal", "success", 100.0, None, [])

    def test_post_execution_reflection_called(self):
        orch = _make_orchestrator()
        mock_reflect = Mock()
        mock_result = Mock()
        mock_result.lesson_learned = "lesson"
        mock_result.strategy_change = ""
        mock_reflect.reflect.return_value = mock_result
        orch._reflection = mock_reflect

        orch._post_execution_agi("goal", "success", 50.0, None, [])
        mock_reflect.reflect.assert_called_once()

    def test_post_execution_reflection_exception_ignored(self):
        orch = _make_orchestrator()
        mock_reflect = Mock()
        mock_reflect.reflect.side_effect = RuntimeError("agi fail")
        orch._reflection = mock_reflect

        # Must not propagate exception
        orch._post_execution_agi("goal", "failed", 10.0, None, ["error"])

    def test_post_execution_world_model_diff(self):
        orch = _make_orchestrator()
        mock_wm = Mock()
        mock_wm.snapshot.return_value = "snap_after"
        mock_diff = Mock()
        mock_diff.summary.return_value = "file added"
        mock_wm.diff.return_value = mock_diff
        orch._world_model = mock_wm
        world_before = "snap_before"

        orch._post_execution_agi("goal", "success", 50.0, world_before, [])
        mock_wm.diff.assert_called_once_with(world_before, "snap_after")

    def test_post_execution_world_model_no_before(self):
        """world_before=None → diff skipped."""
        orch = _make_orchestrator()
        mock_wm = Mock()
        orch._world_model = mock_wm

        orch._post_execution_agi("goal", "success", 50.0, None, [])
        mock_wm.diff.assert_not_called()

    def test_post_execution_code_evolution_called(self):
        orch = _make_orchestrator()
        mock_ce = Mock()
        mock_ce.get_journal.return_value = []
        mock_ce.get_stats.return_value = {"total_attempts": 3, "success_rate": 0.67}
        orch._code_evolution = mock_ce

        orch._post_execution_agi("goal", "success", 50.0, None, [])
        mock_ce.get_stats.assert_called_once()
