# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - AGI Score Engine (AGI v2)."""

from dataclasses import dataclass, field
import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class SubsystemScore:
    """Health score for one AGI subsystem."""
    name: str
    available: bool = False
    score: float = 0.0
    details: str = ""
    icon: str = "❓"


@dataclass
class AGIScoreReport:
    """Complete AGI score report."""
    total_score: float = 0.0
    grade: str = "F"
    subsystems: List[SubsystemScore] = field(default_factory=list)
    module_score: float = 0.0
    wiring_score: float = 0.0
    runtime_score: float = 0.0
    improvement_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


_AGI_MODULES = [
    ("NLU", "src.core.nlu", "IntentClassifier", "📡"),
    ("Memory", "src.core.memory_canonical", "MemoryStore", "💾"),
    ("Reflection", "src.core.reflection", "ReflectionEngine", "🪞"),
    ("WorldModel", "src.core.world_model", "WorldModel", "🌍"),
    ("ToolRegistry", "src.core.tool_registry", "ToolRegistry", "🔧"),
    ("BrowserAgent", "src.core.browser_agent", "BrowserAgent", "🌐"),
    ("Collaboration", "src.core.collaboration", "CollaborationProtocol", "🤝"),
    ("CodeEvolution", "src.core.code_evolution", "CodeEvolutionEngine", "🧬"),
    ("VectorMemory", "src.core.vector_memory_store", "VectorMemoryStore", "🧠"),
]

_WIRING_CHECKS = [
    "orchestrator_reflection", "orchestrator_world_model", "orchestrator_tool_registry",
    "orchestrator_collaboration", "orchestrator_code_evolution", "orchestrator_vector_memory",
    "planner_step_types", "router_intent_tools", "executor_tool_step", "executor_browse_step",
]


class AGIScoreEngine:
    """Calculates real-time AGI capability score (0-100)."""

    def calculate(self) -> AGIScoreReport:
        report = AGIScoreReport()
        report.module_score = self._score_modules(report)
        report.wiring_score = self._score_wiring(report)
        report.runtime_score = self._score_runtime(report)
        report.improvement_score = self._score_improvement(report)
        report.total_score = round(report.module_score + report.wiring_score + report.runtime_score + report.improvement_score, 1)
        for threshold, grade in ((90, "S"), (80, "A"), (70, "B"), (60, "C"), (50, "D")):
            if report.total_score >= threshold:
                report.grade = grade
                break
        return report

    def _score_modules(self, report: AGIScoreReport) -> float:
        score = 0.0
        for name, mod_path, cls_name, icon in _AGI_MODULES:
            sub = SubsystemScore(name=name, icon=icon)
            try:
                getattr(importlib.import_module(mod_path), cls_name)
                sub.available, sub.score, sub.details = True, 5.0, "online"
                score += 5.0
            except Exception as e:
                sub.details = f"offline: {e}"
            report.subsystems.append(sub)
        return score

    def _score_wiring(self, report: AGIScoreReport) -> float:
        score, wired, orch = 0.0, [], None
        try:
            from src.core.orchestrator import RecipeOrchestrator
            orch = RecipeOrchestrator(llm_client=None, strict_verification=False)
            for name, obj in [
                ("reflection", orch._reflection), ("world_model", orch._world_model),
                ("tool_registry", orch._tool_registry), ("collaboration", orch._collaboration),
                ("code_evolution", orch._code_evolution), ("vector_memory", orch._vector_memory),
            ]:
                if obj is not None:
                    score += 2.5
                    wired.append(name)
        except Exception as _exc:
            logger.debug("Orchestrator wiring check failed: %s", _exc)

        try:
            from src.core.planner import RecipePlanner
            if hasattr(RecipePlanner(llm_client=None), "_detect_step_type"):
                score += 2.5
                wired.append("planner_step_types")
        except Exception as _exc:
            logger.debug("Planner step-type check failed: %s", _exc)

        try:
            from src.core.smart_router import _INTENT_TOOLS
            if _INTENT_TOOLS:
                score += 2.5
                wired.append("router_intent_tools")
        except Exception as _exc:
            logger.debug("Router intent-tools check failed: %s", _exc)

        try:
            from src.core.executor import RecipeExecutor
            from src.core.parser import Recipe
            exe = RecipeExecutor(Recipe(name="", description="", steps=[]))
            if hasattr(exe, "_execute_tool_step") and hasattr(exe, "_execute_browse_step"):
                score += 2.5
                wired.append("executor_step_types")
        except Exception as _exc:
            logger.debug("Executor step-type check failed: %s", _exc)

        if orch is not None and getattr(orch, "_event_bus", None) is not None:
            score += 2.5
            wired.append("event_bus")

        report.details["wired"] = wired
        return min(score, 25.0)

    def _score_runtime(self, report: AGIScoreReport) -> float:
        score = 0.0
        try:
            from src.core.memory_canonical import MemoryStore
            stats = MemoryStore().stats()
            total, success_rate = stats.get("total", 0), stats.get("success_rate", 0.0)
            if total > 0:
                score += min(5.0, total * 0.5)
            score += (success_rate / 100.0) * 5.0
            if (auto_dir := Path("recipes/auto")).exists():
                score += min(5.0, len(list(auto_dir.glob("*.md"))) * 1.0)
            report.details["executions"], report.details["success_rate"] = total, success_rate
        except Exception as _exc:
            logger.debug("Runtime metrics check failed: %s", _exc)
        return min(score, 15.0)

    def _score_improvement(self, report: AGIScoreReport) -> float:
        score = 0.0
        try:
            from src.core.reflection import ReflectionEngine
            ReflectionEngine()
            score += 5.0
            report.details["reflection"] = "active"
        except Exception as _exc:
            logger.debug("ReflectionEngine unavailable: %s", _exc)
        try:
            from src.core.code_evolution import CodeEvolutionEngine
            report.details["evolution_attempts"] = CodeEvolutionEngine().get_stats().get("total_attempts", 0)
            score += 5.0
        except Exception as _exc:
            logger.debug("CodeEvolutionEngine unavailable: %s", _exc)
        try:
            from src.core.telemetry import TieredTelemetryStore
            TieredTelemetryStore()
            score += 5.0
            report.details["telemetry"] = "tiered"
        except Exception as _exc:
            logger.debug("TieredTelemetryStore unavailable: %s", _exc)
        return min(score, 15.0)


__all__ = ["AGIScoreEngine", "AGIScoreReport", "SubsystemScore"]
