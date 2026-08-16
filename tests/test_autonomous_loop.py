"""Integration test for the full autonomous loop.

Tests the complete pipeline:
  goal → context → plan → delegate → execute → observe → verify → repair → remember → commit

Uses MagicMock stubs so the test exercises the loop structure without
depending on real business-logic implementations.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from src.core.runtime_adapter import MekongCoreRuntimeImpl, Result


class TestAutonomousLoop(unittest.TestCase):
    """One focused integration test proving the 10-step loop completes."""

    def _build_runtime(self) -> MekongCoreRuntimeImpl:
        """Return a runtime wired entirely with MagicMocks.

        All optional deps are provided explicitly so the runtime never
        falls back to a missing ``_default_*`` helper.
        """
        return MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            memory_store=MagicMock(),
            billing=MagicMock(),
            telemetry=MagicMock(),
            llm_router=MagicMock(),
        )

    def test_full_loop_returns_result(self) -> None:
        """Goal text enters, Result exits — loop structure holds end-to-end."""
        runtime = self._build_runtime()
        result = runtime.run("test goal")

        # Result must be the correct type (dataclass defined in runtime_adapter)
        self.assertIsInstance(result, Result)

        # Result carries the expected public contract
        self.assertIsInstance(result.task_id, str)
        self.assertTrue(result.task_id)          # non-empty string
        self.assertIsNotNone(result.output)      # loop produced output (may be MagicMock stub)
        self.assertIsNotNone(result.metadata)    # dict of loop metadata


if __name__ == "__main__":
    unittest.main()