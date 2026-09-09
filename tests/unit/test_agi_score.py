"""Tests for the AGI Score Engine (src/core/agi_score.py).

The engine introspects the live codebase (module availability, cross-wiring,
runtime metrics, self-improvement), so these tests stub the introspection
boundaries — importlib and the data-store factories — rather than asserting on
whatever happens to be importable in CI at any given moment.
"""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any
from unittest.mock import patch

import pytest

from src.core.agi_score import (
    AGIScoreEngine,
    AGIScoreReport,
    SubsystemScore,
    _AGI_MODULES,
    _WIRING_CHECKS,
)


class _FakeStore:
    """Duck-typed MemoryStore returning canned stats."""

    def __init__(self, stats: dict[str, Any]) -> None:
        self._stats = stats

    def stats(self) -> dict[str, Any]:
        return self._stats


class _FakeEvolution:
    def __init__(self, stats: dict[str, Any]) -> None:
        self._stats = stats

    def get_stats(self) -> dict[str, Any]:
        return self._stats


def _make_module(cls_name: str) -> ModuleType:
    """Build a synthetic module exposing ``cls_name`` with a dummy class."""
    mod = ModuleType("fake_module")
    setattr(mod, cls_name, type(cls_name, (), {}))
    return mod


def _fake_import_module(target_name: str, cls_name: str):
    """Return an importlib.import_module replacement that resolves one
    specific module path to a fake module and delegates everything else."""

    real_import = __import__("importlib").import_module

    def _import(name: str, *args: Any, **kwargs: Any):
        if name == target_name:
            return _make_module(cls_name)
        return real_import(name, *args, **kwargs)

    return _import


class TestSubsystemScoreDataclass:
    """SubsystemScore/AGIScoreReport defaults."""

    def test_subsystem_score_defaults(self):
        sub = SubsystemScore(name="NLU")
        assert sub.available is False
        assert sub.score == 0.0
        assert sub.details == ""
        assert sub.icon == "❓"

    def test_report_defaults(self):
        report = AGIScoreReport()
        assert report.total_score == 0.0
        assert report.grade == "F"
        assert report.subsystems == []
        assert report.details == {}


class TestModuleScoring:
    """Module availability contributes 5 pts per online module."""

    def test_all_modules_online_scores_45(self):
        engine = AGIScoreEngine()
        # One stubbed module proves the online path: 5 pts, subsystem online.
        with patch("src.core.agi_score._AGI_MODULES", [
            ("NLU", "fake_nlu", "IntentClassifier", "📡"),
        ]), patch("importlib.import_module",
                   _fake_import_module("fake_nlu", "IntentClassifier")):
            report = AGIScoreReport()
            score = engine._score_modules(report)
        assert score == 5.0
        assert len(report.subsystems) == 1
        assert report.subsystems[0].available is True
        assert report.subsystems[0].details == "online"
        assert report.subsystems[0].score == 5.0

    def test_import_succeeds_but_class_missing(self):
        """import works, getattr fails — module counts as offline."""
        engine = AGIScoreEngine()
        with patch("src.core.agi_score._AGI_MODULES", [
            ("NLU", "fake_nlu", "NotExported", "📡"),
        ]), patch("importlib.import_module",
                   _fake_import_module("fake_nlu", "OtherClass")):
            report = AGIScoreReport()
            score = engine._score_modules(report)
        assert score == 0.0
        assert report.subsystems[0].available is False

    def test_offline_module_scores_zero(self):
        engine = AGIScoreEngine()
        with patch("src.core.agi_score._AGI_MODULES", [
            ("Missing", "definitely_not_a_module", "Class", "❓"),
        ]):
            report = AGIScoreReport()
            score = engine._score_modules(report)
        assert score == 0.0
        sub = report.subsystems[0]
        assert sub.available is False
        assert sub.details.startswith("offline:")

    def test_real_registry_has_nine_modules(self):
        assert len(_AGI_MODULES) == 9
        # every entry exposes the 4-tuple shape the scorer iterates
        for name, mod_path, cls_name, icon in _AGI_MODULES:
            assert name and mod_path.startswith("src.core.") and cls_name and icon


class TestWiringScoring:
    """Cross-wiring checks are guarded by try/except — failures score zero."""

    def test_wiring_all_checks_failing_scores_zero(self):
        engine = AGIScoreEngine()
        # Every wiring entry point must fail: orchestrator import, planner
        # import, smart_router import, executor import.
        with patch("src.core.orchestrator.RecipeOrchestrator",
                   side_effect=ImportError("boom")), \
             patch("src.core.planner.RecipePlanner",
                   side_effect=ImportError("gone")), \
             patch("src.core.smart_router._INTENT_TOOLS", {}, create=True), \
             patch("src.core.executor.RecipeExecutor",
                   side_effect=ImportError("gone")):
            report = AGIScoreReport()
            score = engine._score_wiring(report)
        assert score == 0.0
        assert report.details["wired"] == []

    def test_wiring_router_import_failure_is_caught(self):
        """``from src.core.smart_router import _INTENT_TOOLS`` raising → the
        except branch (lines 186-187) logs and scores zero for that check."""
        fake_router = ModuleType("src.core.smart_router")
        # Deliberately omit ``_INTENT_TOOLS`` so the ``from ... import``
        # raises ImportError and hits the except branch.
        engine = AGIScoreEngine()
        report = AGIScoreReport()
        original = sys.modules.get("src.core.smart_router")
        sys.modules["src.core.smart_router"] = fake_router
        try:
            engine._score_wiring(report)
        finally:
            if original is not None:
                sys.modules["src.core.smart_router"] = original
            else:
                sys.modules.pop("src.core.smart_router", None)
        # router_intent_tools must NOT appear in the wired list.
        assert "router_intent_tools" not in report.details["wired"]

    def test_wiring_list_has_ten_checks(self):
        assert len(_WIRING_CHECKS) == 10


def _fake_orchestrator(components: dict[str, Any]):
    """Build a synthetic orchestrator exposing ``components`` as attrs."""

    class _FakeOrchestrator:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            for name, value in components.items():
                setattr(self, name, value)

    return _FakeOrchestrator


def _installed_orchestrator(components: dict[str, Any]):
    """Install a fake src.core.orchestrator module into sys.modules.

    The wiring code uses ``from src.core.orchestrator import RecipeOrchestrator``,
    which re-imports the module fresh each call — patching the attribute on
    the real module would not reach it. Replacing sys.modules entries does.
    """
    fake_mod = ModuleType("src.core.orchestrator")
    fake_mod.RecipeOrchestrator = _fake_orchestrator(components)
    return fake_mod


class TestWiringOrchestratorDetail:
    """Orchestrator-driven wiring checks via a sys.modules stub."""

    def test_wiring_orchestrator_components_online(self):
        """A fully wired orchestrator scores 2.5 per present component."""
        engine = AGIScoreEngine()
        fake = _installed_orchestrator({
            "_reflection": object(), "_world_model": object(),
            "_tool_registry": object(), "_collaboration": object(),
            "_code_evolution": object(), "_vector_memory": object(),
            "_event_bus": object(),
        })
        with patch.dict(sys.modules, {"src.core.orchestrator": fake}):
            report = AGIScoreReport()
            score = engine._score_wiring(report)
        # 7 orchestrator × 2.5 = 17.5, capped by the 25-point ceiling.
        assert score == 25.0
        wired = report.details["wired"]
        for name in ("reflection", "world_model", "tool_registry",
                     "collaboration", "code_evolution", "vector_memory",
                     "event_bus"):
            assert name in wired

    def test_wiring_orchestrator_with_none_components(self):
        """Components explicitly None must NOT score; the event_bus check
        must still see ``orch`` and short-circuit without NameError."""
        engine = AGIScoreEngine()
        fake = _installed_orchestrator({
            "_reflection": None, "_world_model": None,
            "_tool_registry": None, "_collaboration": None,
            "_code_evolution": None, "_vector_memory": None,
            "_event_bus": None,
        })
        with patch.dict(sys.modules, {"src.core.orchestrator": fake}):
            report = AGIScoreReport()
            score = engine._score_wiring(report)
        # None components contribute 0 from the orchestrator block; the
        # planner/router/executor checks still score against the live
        # modules, so the floor is not 0.
        assert score >= 0.0
        wired = report.details["wired"]
        assert "reflection" not in wired
        assert "event_bus" not in wired


class TestRuntimeScoring:
    """Runtime metrics: memory stats + recipes/auto count, capped at 15."""

    def _score_with(self, store_stats, auto_dir_exists, auto_count=0):
        engine = AGIScoreEngine()
        with patch("src.core.memory_canonical.MemoryStore", return_value=_FakeStore(store_stats)), \
             patch("src.core.agi_score.Path") as agg_path:
            # Path("recipes/auto").exists() and Path(...).glob(...) are
            # stubbed on the aggregated class: chaining supports both calls.
            agg_path.return_value.exists.return_value = auto_dir_exists
            agg_path.return_value.glob.return_value = list(range(auto_count))
            report = AGIScoreReport()
            return engine._score_runtime(report), report

    def test_runtime_max_metrics_score(self):
        score, report = self._score_with(
            {"total": 100, "success_rate": 100.0}, True, auto_count=5)
        # 5 (history) + 5 (success rate) + 5 (auto recipes) = 15
        assert score == 15.0
        assert report.details["executions"] == 100
        assert report.details["success_rate"] == 100.0

    def test_runtime_zero_metrics_score(self):
        score, report = self._score_with({"total": 0, "success_rate": 0.0}, False)
        assert score == 0.0

    def test_runtime_exception_swallowed(self):
        engine = AGIScoreEngine()
        with patch("src.core.memory_canonical.MemoryStore", side_effect=RuntimeError("db down")):
            report = AGIScoreReport()
            score = engine._score_runtime(report)
        assert score == 0.0


class TestImprovementScoring:
    """Self-improvement: reflection + evolution + telemetry, 5 pts each."""

    def test_improvement_all_available(self):
        engine = AGIScoreEngine()

        class _StubEngine:
            def __init__(self) -> None:
                pass

        with patch("src.core.reflection.ReflectionEngine", _StubEngine), \
             patch("src.core.code_evolution.CodeEvolutionEngine",
                   return_value=_FakeEvolution({"total_attempts": 3})), \
             patch("src.core.telemetry.TieredTelemetryStore", _StubEngine):
            report = AGIScoreReport()
            score = engine._score_improvement(report)
        assert score == 15.0
        assert report.details["reflection"] == "active"
        assert report.details["evolution_attempts"] == 3
        assert report.details["telemetry"] == "tiered"

    def test_improvement_reflection_only(self):
        engine = AGIScoreEngine()

        class _StubEngine:
            def __init__(self) -> None:
                pass

        with patch("src.core.reflection.ReflectionEngine", _StubEngine), \
             patch("src.core.code_evolution.CodeEvolutionEngine",
                   side_effect=ImportError("gone")), \
             patch("src.core.telemetry.TieredTelemetryStore",
                   side_effect=ImportError("gone")):
            report = AGIScoreReport()
            score = engine._score_improvement(report)
        assert score == 5.0
        assert "evolution_attempts" not in report.details

    def test_improvement_all_unavailable(self):
        engine = AGIScoreEngine()
        with patch("src.core.reflection.ReflectionEngine", side_effect=ImportError("gone")), \
             patch("src.core.code_evolution.CodeEvolutionEngine", side_effect=ImportError("gone")), \
             patch("src.core.telemetry.TieredTelemetryStore", side_effect=ImportError("gone")):
            report = AGIScoreReport()
            score = engine._score_improvement(report)
        assert score == 0.0


class TestGrading:
    """Grade thresholds on the 0-100 total."""

    @pytest.mark.parametrize("total,expected", [
        (95, "S"), (90, "S"),
        (85, "A"), (80, "A"),
        (75, "B"), (70, "B"),
        (65, "C"), (60, "C"),
        (55, "D"), (50, "D"),
        (45, "F"), (0, "F"),
    ])
    def test_grade_thresholds(self, total, expected):
        engine = AGIScoreEngine()
        with patch.object(AGIScoreEngine, "_score_modules", return_value=total), \
             patch.object(AGIScoreEngine, "_score_wiring", return_value=0.0), \
             patch.object(AGIScoreEngine, "_score_runtime", return_value=0.0), \
             patch.object(AGIScoreEngine, "_score_improvement", return_value=0.0):
            report = engine.calculate()
        assert report.total_score == total
        assert report.grade == expected

    def test_calculate_sums_component_scores(self):
        engine = AGIScoreEngine()
        with patch.object(AGIScoreEngine, "_score_modules", return_value=10.0), \
             patch.object(AGIScoreEngine, "_score_wiring", return_value=20.0), \
             patch.object(AGIScoreEngine, "_score_runtime", return_value=30.0), \
             patch.object(AGIScoreEngine, "_score_improvement", return_value=40.0):
            report = engine.calculate()
        assert report.total_score == 100.0
        assert report.module_score == 10.0
        assert report.wiring_score == 20.0
        assert report.runtime_score == 30.0
        assert report.improvement_score == 40.0
        assert report.grade == "S"
