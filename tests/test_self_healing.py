"""Tests for AI self-healing in RecipeOrchestrator."""

import unittest
from unittest.mock import MagicMock, patch

from tests.conftest import _pre_gateway_originals
from src.core.orchestrator import RecipeOrchestrator as RecipeOrchestrator, StepResult
from src.core.parser import Recipe, RecipeStep
from src.core.verifier import ExecutionResult


class TestSelfHealing(unittest.TestCase):
    """Test AI self-correction retry logic in orchestrator."""

    def setUp(self):
        """Restore the real RecipeOrchestrator for direct construction.

        A session-scoped conftest mock replaces RecipeOrchestrator with a
        MagicMock so gateway tests can import the app without a live LLM.
        Tests in this class construct the real class directly, so the mock
        must be unwound for their scope.  Both the module attribute and the
        locally-imported name are patched, because the test calls
        ``RecipeOrchestrator(...)`` using the name bound at import time.
        """
        import src.core.orchestrator as _orch
        import tests.test_self_healing as _self

        _real = _pre_gateway_originals.get("src.core.orchestrator.RecipeOrchestrator")
        assert _real is not None, "conftest did not capture RecipeOrchestrator before patching"
        self._orch_patch = patch.object(_orch, "RecipeOrchestrator", _real)
        self._name_patch = patch.object(_self, "RecipeOrchestrator", _real)
        self._orch_patch.start()
        self._name_patch.start()
        self.addCleanup(self._orch_patch.stop)
        self.addCleanup(self._name_patch.stop)

    def _make_recipe(self, command: str = "ls /nonexistent") -> Recipe:
        """Helper to build a single-step shell recipe."""
        step = RecipeStep(
            order=1,
            title="Test step",
            description=command,
            params={"type": "shell", "verification": {}},
        )
        return Recipe(name="test", description="test recipe", steps=[step])

    def test_suggest_correction_called_on_failure(self):
        """When a shell step fails and LLM is available, LLM.generate is called
        and the corrected command is retried."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "ls /tmp"

        orch = RecipeOrchestrator(
            llm_client=mock_llm,
            strict_verification=False,
            enable_rollback=False,
        )

        recipe = self._make_recipe("ls /nonexistent_dir_xyz")

        # Patch executor so first call fails, second succeeds
        fail_result = ExecutionResult(exit_code=1, stdout="", stderr="No such file")
        ok_result = ExecutionResult(exit_code=0, stdout="success", stderr="")

        with patch("src.core.executor.RecipeExecutor.execute_step") as mock_exec, \
             patch("src.core.command_sanitizer.CommandSanitizer.is_safe_command", return_value=True):
            mock_exec.side_effect = [fail_result, ok_result]
            result = orch.run_from_recipe(recipe)

        # LLM generate should have been called for self-heal
        mock_llm.generate.assert_called_once()
        prompt_arg = mock_llm.generate.call_args[0][0]
        self.assertIn("failed", prompt_arg.lower())
        # Step should be marked as self-healed
        self.assertTrue(result.step_results[0].self_healed)

    def test_self_heal_skipped_when_no_llm(self):
        """Without LLM client, no self-heal attempt is made."""
        orch = RecipeOrchestrator(
            llm_client=None,
            strict_verification=False,
            enable_rollback=False,
        )

        recipe = self._make_recipe("ls /nonexistent_dir_xyz")

        fail_result = ExecutionResult(exit_code=1, stdout="", stderr="No such file")

        with patch("src.core.executor.RecipeExecutor.execute_step") as mock_exec:
            mock_exec.return_value = fail_result
            result = orch.run_from_recipe(recipe)

        # Should not be self-healed
        self.assertFalse(result.step_results[0].self_healed)
        # execute_step called only once (no retry)
        mock_exec.assert_called_once()

    def test_step_result_has_self_healed_field(self):
        """StepResult dataclass includes self_healed field defaulting to False."""
        step = RecipeStep(order=1, title="t", description="echo hi")
        exec_result = ExecutionResult(exit_code=0, stdout="hi", stderr="")
        from src.core.verifier import VerificationReport

        report = VerificationReport(passed=True)
        sr = StepResult(step=step, execution=exec_result, verification=report)
        self.assertFalse(sr.self_healed)

        sr2 = StepResult(
            step=step, execution=exec_result, verification=report, self_healed=True
        )
        self.assertTrue(sr2.self_healed)


if __name__ == "__main__":
    unittest.main()
