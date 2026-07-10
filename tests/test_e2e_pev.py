"""E2E integration tests for the full PEV pipeline.

Tests PEVOrchestrator end-to-end: recipe file execution, goal-string
decomposition, metrics recording, and memory persistence via MemoryBridge.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.harness.pev import PEVOrchestrator, PipelineResult, get_pev_metrics, reset_pev_metrics  # noqa: E402
from src.core.memory_bridge import get_bridge  # noqa: E402

RECIPE_PATH = Path(_ROOT) / "src" / "harness" / "pev" / "recipes" / "hello-world.md"


class TestPEVE2E(unittest.TestCase):
    """End-to-end tests for the PEV orchestrator pipeline."""

    def setUp(self) -> None:
        reset_pev_metrics()

    def tearDown(self) -> None:
        reset_pev_metrics()

    # 1. Recipe file execution
    def test_orchestrator_runs_recipe_file(self) -> None:
        """orchestrator.run(Path) succeeds and reports >= 1 step."""
        orchestrator = PEVOrchestrator()
        result = orchestrator.run(RECIPE_PATH)
        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.steps_total, 1)

    # 2. Metrics recording
    def test_orchestrator_records_metrics(self) -> None:
        """After a run, get_pev_metrics() contains the pipeline."""
        orchestrator = PEVOrchestrator()
        result = orchestrator.run(RECIPE_PATH)
        self.assertTrue(result.success)

        metrics = get_pev_metrics()
        summary = metrics.get_pipeline_summary(result.pipeline_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["pipeline_id"], result.pipeline_id)

    # 3. Memory persistence
    def test_orchestrator_records_memory(self) -> None:
        """After a run, the memory bridge has a recent record."""
        bridge = get_bridge("memory")
        orchestrator = PEVOrchestrator(memory=bridge)
        result = orchestrator.run(RECIPE_PATH)
        self.assertTrue(result.success)

        results = bridge.search(result.pipeline_id, limit=5)
        self.assertTrue(
            any(result.pipeline_id in r.content for r in results),
            f"Pipeline {result.pipeline_id!r} not found via search: {[r.content for r in results]}",
        )

    # 4. Goal string (no recipe file)
    def test_orchestrator_with_goal_string(self) -> None:
        """Passing a plain string goal runs via the planner path."""
        orchestrator = PEVOrchestrator()
        result = orchestrator.run("print hello world")
        self.assertIsInstance(result, PipelineResult)
        # The planner may fail without an LLM, but the pipeline should
        # complete and produce a PipelineResult with valid fields.
        self.assertIsNotNone(result.pipeline_id)
        self.assertIsNotNone(result.goal)

    # 5. PipelineResult attribute contract
    def test_pipeline_result_attributes(self) -> None:
        """PipelineResult exposes all expected fields with correct types."""
        orchestrator = PEVOrchestrator()
        result = orchestrator.run(RECIPE_PATH)

        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.pipeline_id, str)
        self.assertGreater(len(result.pipeline_id), 0)
        self.assertIsInstance(result.goal, str)
        self.assertIsInstance(result.steps_total, int)
        self.assertGreaterEqual(result.steps_total, 0)
        self.assertIsInstance(result.steps_passed, int)
        self.assertGreaterEqual(result.steps_passed, 0)
        self.assertIsInstance(result.steps_failed, int)
        self.assertGreaterEqual(result.steps_failed, 0)
        self.assertIsInstance(result.duration_ms, float)
        self.assertGreaterEqual(result.duration_ms, 0)
        self.assertIsInstance(result.error, (str, type(None)))


if __name__ == "__main__":
    unittest.main()
