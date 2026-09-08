"""Tests for PatternAnalyzer (Learner)."""

import tempfile
import unittest
from unittest.mock import MagicMock

import pytest

from src.core.learner import PatternAnalyzer, Pattern
from src.core.memory_canonical import MemoryEntry
from src.core.event_bus import EventType, Event

# The session-scoped gateway mock in conftest replaces
# ``src.core.memory_canonical.MemoryStore`` with a MagicMock so the gateway
# app can import without a live LLM.  Without this, ``MemoryStore(...)`` in
# setUp returns a mock whose ``_entries`` is empty and every analyzer call
# returns [] — so restore the real class for the whole module.
pytestmark = pytest.mark.usefixtures("restore_real_memory_store")


class TestPattern(unittest.TestCase):
    """Test Pattern dataclass."""

    def test_pattern_creation(self):
        """Pattern can be instantiated with all fields."""
        p = Pattern(
            pattern_type="repeated_failure",
            description="Test pattern",
            confidence=0.8,
            data={"key": "value"},
        )
        self.assertEqual(p.pattern_type, "repeated_failure")
        self.assertEqual(p.description, "Test pattern")
        self.assertEqual(p.confidence, 0.8)
        self.assertEqual(p.data, {"key": "value"})

    def test_pattern_default_data(self):
        """Pattern.data defaults to empty dict."""
        p = Pattern(pattern_type="test", description="d", confidence=0.5)
        self.assertEqual(p.data, {})


class TestPatternAnalyzer(unittest.TestCase):
    """Test PatternAnalyzer methods."""

    def setUp(self):
        # ``MemoryStore`` is imported at module level, which happens after the
        # session-scoped gateway mock has already replaced
        # ``src.core.memory_canonical.MemoryStore`` with a MagicMock — so the
        # local name would point at the mock.  Resolve the class through the
        # module (un-mocked by the restore_real_memory_store fixture) instead.
        import src.core.memory_canonical as _mc
        self._tmpdir = tempfile.TemporaryDirectory()
        self.store = _mc.MemoryStore(
            store_path=str(self._tmpdir.name + "/test_memory.yaml")
        )
        self.analyzer = PatternAnalyzer(self.store)

    def tearDown(self):
        from src.core.event_bus import get_event_bus
        bus = get_event_bus()
        bus.clear()
        self._tmpdir.cleanup()

    def _add_entry(self, goal: str, status: str, recipe: str = "",
               hour: int = 9) -> None:
        """Add a MemoryEntry to the store.

        ``hour`` pins the wall-clock hour used by ``get_time_patterns`` (which
        buckets via ``time.localtime``), so the test is timezone-independent —
        otherwise entries land in whatever slot the CI runner's local time
        happens to be.
        """
        import time as _time
        entry = MemoryEntry(
            goal=goal, status=status, recipe_used=recipe, duration_ms=0.0,
            timestamp=_time.mktime(
                (2026, 1, 1, hour, 0, 0, 0, 0, 0),
            ),
        )
        self.store._entries.append(entry)

    def test_analyze_failures_empty_store(self):
        """No patterns when store is empty."""
        patterns = self.analyzer.analyze_failures()
        self.assertEqual(patterns, [])

    def test_analyze_failures_no_streak(self):
        """No patterns when no goal has consecutive failures."""
        self._add_entry("deploy", "success")
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "success")
        patterns = self.analyzer.analyze_failures()
        self.assertEqual(patterns, [])

    def test_analyze_failures_detects_streak(self):
        """Detects goal with 3 consecutive failures."""
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "failed")
        patterns = self.analyzer.analyze_failures()
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].pattern_type, "repeated_failure")
        self.assertIn("deploy", patterns[0].description)
        self.assertIn("3", patterns[0].description)
        self.assertEqual(patterns[0].confidence, 0.3)  # 3/10

    def test_analyze_failures_confidence_capped_at_one(self):
        """Confidence capped at 1.0 for long streaks."""
        for _ in range(15):
            self._add_entry("deploy", "failed")
        patterns = self.analyzer.analyze_failures()
        self.assertEqual(patterns[0].confidence, 1.0)

    def test_analyze_failures_multiple_goals(self):
        """Tracks streaks per goal independently."""
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "failed")
        self._add_entry("backup", "failed")
        self._add_entry("backup", "failed")
        patterns = self.analyzer.analyze_failures()
        # deploy has streak of 3, backup has 2 (below threshold)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].data["goal"], "deploy")

    def test_analyze_failures_success_resets_streak(self):
        """A success resets the failure streak."""
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "failed")
        self._add_entry("deploy", "success")  # resets
        self._add_entry("deploy", "failed")
        patterns = self.analyzer.analyze_failures()
        # Last streak is 1, total max streak was 2
        self.assertEqual(patterns, [])

    def test_get_recipe_effectiveness_empty(self):
        """Empty dict when no entries with recipes."""
        result = self.analyzer.get_recipe_effectiveness()
        self.assertEqual(result, {})

    def test_get_recipe_effectiveness_single_recipe(self):
        """Computes success rate per recipe."""
        self._add_entry("deploy", "success", recipe="docker-deploy")
        self._add_entry("deploy", "failed", recipe="docker-deploy")
        self._add_entry("deploy", "success", recipe="docker-deploy")
        result = self.analyzer.get_recipe_effectiveness()
        self.assertAlmostEqual(result["docker-deploy"], 66.67, places=1)

    def test_get_recipe_effectiveness_multiple_recipes(self):
        """Tracks effectiveness per recipe independently."""
        self._add_entry("deploy", "success", recipe="docker-deploy")
        self._add_entry("deploy", "failed", recipe="k8s-deploy")
        result = self.analyzer.get_recipe_effectiveness()
        self.assertAlmostEqual(result["docker-deploy"], 100.0)
        self.assertAlmostEqual(result["k8s-deploy"], 0.0)

    def test_get_recipe_effectiveness_ignores_empty_recipe(self):
        """Entries without recipe_used are ignored."""
        self._add_entry("deploy", "success")
        self._add_entry("deploy", "success", recipe="real-recipe")
        result = self.analyzer.get_recipe_effectiveness()
        self.assertEqual(len(result), 1)
        self.assertIn("real-recipe", result)

    def test_get_time_patterns_insufficient_data(self):
        """No patterns when slots have fewer than 3 entries."""
        for _ in range(2):
            self._add_entry("task", "success")
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(patterns, [])

    def test_get_time_patterns_detects_slot(self):
        """Detects high-success time slot."""
        # Add 5 successes in 06-12 slot (hour=9)
        for _ in range(5):
            self._add_entry("task", "success")
        # Add 1 failure in 18-24 slot (hour=20)
        self._add_entry("task", "failed")
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].pattern_type, "time_correlation")
        self.assertIn("06-12", patterns[0].description)

    def test_get_time_patterns_low_success_rate_excluded(self):
        """Slots with <=70% success rate are not reported."""
        # 2 success, 2 failure = 50% in 06-12
        for _ in range(2):
            self._add_entry("task", "success")
        for _ in range(2):
            self._add_entry("task", "failed")
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(patterns, [])

    def test_get_time_patterns_confidence_calculation(self):
        """Confidence scales with sample size up to 1.0."""
        for _ in range(5):
            self._add_entry("task", "success")
        patterns = self.analyzer.get_time_patterns()
        self.assertAlmostEqual(patterns[0].confidence, 0.25)  # 5/20

    def test_get_time_patterns_confidence_capped_at_one(self):
        """Confidence capped at 1.0 for large samples."""
        for _ in range(25):
            self._add_entry("task", "success")
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(patterns[0].confidence, 1.0)

    def test_get_time_patterns_midnight_slot(self):
        """Detects pattern in 00-06 slot (midnight)."""
        # hour=3 → 00-06
        for _ in range(5):
            self._add_entry("task", "success", hour=3)
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertIn("00-06", patterns[0].description)

    def test_get_time_patterns_evening_slot(self):
        """Detects pattern in 18-24 slot (evening)."""
        # hour=20 → 18-24
        for _ in range(5):
            self._add_entry("task", "success", hour=20)
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertIn("18-24", patterns[0].description)

    def test_get_time_patterns_afternoon_slot(self):
        """Detects pattern in 12-18 slot (afternoon)."""
        # hour=15 → 12-18
        for _ in range(5):
            self._add_entry("task", "success", hour=15)
        patterns = self.analyzer.get_time_patterns()
        self.assertEqual(len(patterns), 1)
        self.assertIn("12-18", patterns[0].description)

    def test_on_memory_recorded_emits_pattern(self):
        """Subscriber emits PATTERN_DETECTED when failures detected."""
        bus = MagicMock()
        # The session-scoped gateway mock replaces
        # ``src.core.event_bus.get_event_bus`` with a MagicMock, so the
        # learner module (imported at collection time) captured that MagicMock
        # as its ``get_event_bus`` reference.  Patch the *learner module's*
        # reference so the analyzer calls our bus.
        import src.core.learner as learner_mod
        original_learner_get = learner_mod.get_event_bus
        learner_mod.get_event_bus = lambda: bus
        try:
            # Add 3 failures
            for _ in range(3):
                self._add_entry("deploy", "failed")
            # Trigger by emitting MEMORY_RECORDED
            self.analyzer.on_memory_recorded(Event(
                type=EventType.MEMORY_RECORDED,
                data={}
            ))
            # Verify PATTERN_DETECTED emitted
            self.assertTrue(bus.emit.called)
            emitted_types = {call.args[0] for call in bus.emit.call_args_list}
            self.assertIn(EventType.PATTERN_DETECTED, emitted_types)
        finally:
            learner_mod.get_event_bus = original_learner_get


if __name__ == "__main__":
    unittest.main()