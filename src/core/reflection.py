# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Reflection Engine (AGI v2)."""

import json
import logging
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .event_bus import EventType, get_event_bus

REFLECTION_PERSIST_PATH = os.path.expanduser("~/.mekong/reflection_log.jsonl")
logger = logging.getLogger(__name__)

_REFLECTION_PROMPT = (
    "You are the meta-cognition engine of Mekong CLI, an AGI agent.\n"
    "Analyze this task execution and provide structured reflection.\n"
    "Goal: {goal} | Status: {status} | Duration: {duration_ms:.0f}ms | Error: {error}\n"
    "Previous Reflections: {previous_reflections}\n"
    'Return JSON: {{"strengths": ["what went well"], "weaknesses": ["what went wrong"], '
    '"alternative_approach": "better approach", "confidence_adjustment": 0.1, '
    '"lesson_learned": "key takeaway", "should_change_strategy": false}}'
)


@dataclass
class ReflectionReport:
    goal: str; status: str; duration_ms: float = 0.0  # noqa: E702
    strengths: List[str] = field(default_factory=list); weaknesses: List[str] = field(default_factory=list)  # noqa: E702
    alternative_approach: str = ""; confidence_adjustment: float = 0.0; lesson_learned: str = ""  # noqa: E702
    should_change_strategy: bool = False; timestamp: float = field(default_factory=time.time)  # noqa: E702


@dataclass
class StrategyRecord:
    strategy_name: str; uses: int = 0; successes: int = 0; failures: int = 0; avg_duration_ms: float = 0.0  # noqa: E702

    @property
    def success_rate(self) -> float:
        return self.successes / self.uses if self.uses > 0 else 0.0


class ConfidenceCalibrator:
    MAX_HISTORY: int = 100

    def __init__(self) -> None:
        self._predictions: List[Dict[str, float]] = []

    def record(self, predicted_confidence: float, actual_success: bool) -> None:
        self._predictions = (self._predictions + [{"predicted": predicted_confidence, "actual": 1.0 if actual_success else 0.0, "timestamp": time.time()}])[-self.MAX_HISTORY:]

    def get_calibration_error(self) -> float:
        if len(self._predictions) < 5:
            return 0.5
        bins: Dict[int, List[Dict[str, float]]] = {i: [] for i in range(5)}
        for pred in self._predictions:
            bins[min(int(pred["predicted"] * 5), 4)].append(pred)
        total_err = total_cnt = 0.0
        for bp in bins.values():
            if bp:
                total_err += abs(sum(p["predicted"] for p in bp) / len(bp) - sum(p["actual"] for p in bp) / len(bp)) * len(bp)
                total_cnt += len(bp)
        return total_err / total_cnt if total_cnt > 0 else 0.5

    def get_adjusted_confidence(self, raw_confidence: float) -> float:
        if len(self._predictions) < 10:
            return raw_confidence
        recent = self._predictions[-20:]
        bias = sum(p["predicted"] - p["actual"] for p in recent) / len(recent)
        return max(0.05, min(0.99, raw_confidence - (bias * 0.5)))

    @property
    def prediction_count(self) -> int:
        return len(self._predictions)


class ReflectionEngine:
    MAX_REFLECTIONS: int = 50

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        self.llm_client = llm_client
        self.calibrator = ConfidenceCalibrator()
        self._reflections: List[ReflectionReport] = []
        self._strategies: Dict[str, StrategyRecord] = {}

    def _persist(self, report: ReflectionReport) -> None:
        try:
            path = Path(REFLECTION_PERSIST_PATH)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(report), default=str) + "\n")
        except Exception as exc:
            logger.debug("Reflection persist failed: %s", exc)

    def reflect(self, goal: str, status: str, duration_ms: float = 0.0, error: str = "", predicted_confidence: float = 0.8) -> ReflectionReport:
        is_success = status == "success"
        self.calibrator.record(predicted_confidence, is_success)
        report = ReflectionReport(goal=goal, status=status, duration_ms=duration_ms)
        if is_success:
            report.strengths.extend(["Task completed successfully", *(["Fast execution time"] if duration_ms < 5000 else [])])
            report.confidence_adjustment = 0.05
        else:
            report.weaknesses.append(f"Task failed: {error or 'unknown error'}")
            report.confidence_adjustment = -0.1
            if len(sim := [r for r in self._reflections[-10:] if r.status != "success" and r.goal == goal]) >= 2:
                report.should_change_strategy = True
                report.weaknesses.append(f"Repeated failure ({len(sim) + 1} times). Strategy change recommended.")
                report.confidence_adjustment = -0.2

        if self.llm_client and hasattr(self.llm_client, "generate_json"):
            try:
                llm_r = self._llm_reflect(goal, status, duration_ms, error)
                report.strengths.extend(llm_r.get("strengths", []))
                report.weaknesses.extend(llm_r.get("weaknesses", []))
                report.alternative_approach, report.lesson_learned = llm_r.get("alternative_approach", ""), llm_r.get("lesson_learned", "")
                if "confidence_adjustment" in llm_r:
                    report.confidence_adjustment = float(llm_r["confidence_adjustment"])
                if llm_r.get("should_change_strategy"):
                    report.should_change_strategy = True
            except Exception as e:
                logger.debug("LLM reflection failed: %s", e)

        report.strengths, report.weaknesses = list(dict.fromkeys(report.strengths)), list(dict.fromkeys(report.weaknesses))
        report.confidence_adjustment = max(-1.0, min(1.0, report.confidence_adjustment))
        self._reflections = (self._reflections + [report])[-self.MAX_REFLECTIONS:]
        self._persist(report)
        get_event_bus().emit(EventType.AUTONOMOUS_CYCLE, {"event": "reflection_complete", "goal": goal, "status": status, "should_change_strategy": report.should_change_strategy, "lesson": report.lesson_learned})
        return report

    def get_strategy_suggestion(self, goal: str) -> str:
        gl = goal.lower()
        if not (rel := [r for r in self._reflections if gl in r.goal.lower() or r.goal.lower() in gl]):
            return "No prior data. Using default strategy."
        succ, fail = [r for r in rel if r.status == "success"], [r for r in rel if r.status != "success"]
        if not fail:
            return "Previous attempts all succeeded. Continue current approach."
        if len(fail) > len(succ):
            alts = [r.alternative_approach for r in fail if r.alternative_approach]
            return f"Previous approach failed often. Try: {alts[-1]}" if alts else "Previous approach unreliable. Consider a different strategy."
        return "Mixed results. Current approach works but may need refinement."

    def get_recent(self, limit: int = 10) -> List[ReflectionReport]:
        return self._reflections[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        if not self._reflections:
            return {"total_reflections": 0, "calibration_error": 0.5, "strategy_changes_suggested": 0}
        return {
            "total_reflections": len(self._reflections), "calibration_error": self.calibrator.get_calibration_error(),
            "prediction_count": self.calibrator.prediction_count, "strategy_changes_suggested": sum(1 for r in self._reflections if r.should_change_strategy),
            "avg_confidence_adjustment": sum(r.confidence_adjustment for r in self._reflections) / len(self._reflections),
            "lessons_learned": [r.lesson_learned for r in self._reflections[-5:] if r.lesson_learned],
        }

    def _llm_reflect(self, goal: str, status: str, duration_ms: float, error: str) -> Dict[str, Any]:
        if self.llm_client is None:
            return {}
        prev = "".join(f"- [{r.status}] {r.goal}: {r.lesson_learned or 'no lesson'}\n" for r in self._reflections[-3:])
        try:
            res = self.llm_client.generate_json(_REFLECTION_PROMPT.format(goal=goal, status=status, duration_ms=duration_ms, error=error or "none", previous_reflections=prev or "None yet."))
            return res if isinstance(res, dict) else {}
        except Exception:
            return {}


__all__ = ["ReflectionEngine", "ReflectionReport", "ConfidenceCalibrator", "StrategyRecord"]
