# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Autonomous Engine (AGI v2)."""

import os
import time
from typing import Any, List, Optional

from .event_bus import EventType, get_event_bus
from .governance import ActionClass, AuditEntry, Governance, GovernanceDecision
from .autonomous_models import ConsciousnessReport, CycleResult, DecisionTrace


class AutonomousEngine:
    """Fully autonomous execution engine coordinating all subsystems."""

    MAX_HISTORY: int = 100

    def __init__(self, orchestrator: Optional[Any] = None, governance: Optional[Governance] = None) -> None:
        self.orchestrator = orchestrator
        self.governance = governance or Governance()
        self._memory = self._nlu = self._router = self._learner = self._recipe_gen = self._reflection = self._world_model = None
        self._consciousness_history: List[ConsciousnessReport] = []
        self._decision_traces: List[DecisionTrace] = []
        self._init_subsystems()

    def _init_subsystems(self) -> None:
        from src.providers.llm.client import LLMClient
        llm = LLMClient(gemini_key=os.getenv("GEMINI_API_KEY", ""))
        for attr, mod_name, cls_name, kwargs in (
            ("_memory", ".memory_canonical", "MemoryStore", {}),
            ("_nlu", ".nlu", "IntentClassifier", {"llm_client": llm}),
            ("_recipe_gen", ".recipe_gen", "RecipeGenerator", {"llm_client": llm}),
            ("_reflection", ".reflection", "ReflectionEngine", {"llm_client": llm}),
            ("_world_model", ".world_model", "WorldModel", {"llm_client": llm}),
        ):
            if getattr(self, attr) is None:
                try:
                    setattr(self, attr, getattr(__import__(f"src.core{mod_name}", fromlist=[cls_name]), cls_name)(**kwargs))
                except Exception:
                    pass
        try:
            from .smart_router import SmartRouter
            self._router = SmartRouter(memory_store=self._memory) if self._memory else None
        except Exception:
            pass
        if self._learner is None and self._memory:
            try:
                from .learner import PatternAnalyzer
                self._learner = PatternAnalyzer(memory_store=self._memory)
            except Exception:
                pass

    def process_goal(self, goal: str) -> CycleResult:
        result, trace, start_time = CycleResult(goal=goal), DecisionTrace(goal=goal), time.time()
        if self.governance.is_halted():
            result.result_status = trace.result = "halted"
            result.decision_trace = trace
            return result

        world_before = None
        if self._world_model:
            try:
                world_before, trace.world_state_summary = self._world_model.snapshot(), self._world_model.get_context_summary()
            except Exception:
                pass
        if self._nlu:
            try:
                ir = self._nlu.classify(goal)
                trace.intent_classified, trace.confidence = ir.intent.value, ir.confidence
            except Exception:
                pass

        decision = self.governance.classify(goal)
        result.governance_decision, trace.governance_decision = decision, decision.action_class.value
        if decision.action_class == ActionClass.FORBIDDEN:
            self.governance.record_audit(AuditEntry(goal=goal, action_class="forbidden", approved=False, result="blocked"))
            get_event_bus().emit(EventType.GOVERNANCE_BLOCKED, {"goal": goal, "reason": decision.reason})
            result.result_status, result.decision_trace = "blocked", trace
            trace.result = "blocked"
            return result
        if decision.action_class == ActionClass.REVIEW_REQUIRED and not self.governance.request_approval(goal, decision):
            self.governance.record_audit(AuditEntry(goal=goal, action_class="review_required", approved=False, result="rejected"))
            result.result_status, result.decision_trace = "rejected", trace
            trace.result = "rejected"
            return result

        if self._reflection:
            try:
                trace.strategy_used = self._reflection.get_strategy_suggestion(goal)
            except Exception:
                pass
        if self.orchestrator:
            try:
                result.executed, result.result_status = True, self.orchestrator.run_from_goal(goal).status.value
            except Exception:
                result.executed, result.result_status = True, "error"

        duration_ms = (time.time() - start_time) * 1000
        if self._memory and result.executed:
            from .memory_canonical import MemoryEntry
            self._memory.record(MemoryEntry(goal=goal, status=result.result_status, duration_ms=duration_ms))
        if self._learner and result.result_status == "failed":
            try:
                result.patterns_detected = len(self._learner.analyze_failures())
            except Exception:
                pass
        if self._recipe_gen and self._memory and result.result_status == "success":
            try:
                from .memory_canonical import MemoryEntry
                if (recipe := self._recipe_gen.from_successful_run(MemoryEntry(goal=goal, status="success"))).valid:
                    self._recipe_gen.save_recipe(recipe)
                    result.recipe_generated = True
            except Exception:
                pass
        if self._reflection and result.executed:
            try:
                ref = self._reflection.reflect(goal=goal, status=result.result_status, duration_ms=duration_ms, error="" if result.result_status == "success" else result.result_status)
                result.reflection_summary = trace.reflection_summary = ref.lesson_learned
            except Exception:
                pass
        if self._world_model and world_before:
            try:
                result.world_diff_summary = self._world_model.diff(world_before, self._world_model.snapshot()).summary()
            except Exception:
                pass

        trace.result = result.result_status
        self.governance.record_audit(AuditEntry(goal=goal, action_class=decision.action_class.value, approved=True, result="executed" if result.executed else "skipped"))
        result.decision_trace = trace
        self._decision_traces = (self._decision_traces + [trace])[-self.MAX_HISTORY:]
        get_event_bus().emit(EventType.AUTONOMOUS_CYCLE, {"goal": goal, "status": result.result_status, "executed": result.executed, "reflection": result.reflection_summary, "world_diff": result.world_diff_summary})
        return result

    def get_consciousness(self) -> ConsciousnessReport:
        r = ConsciousnessReport(
            memory_health=1.0 if self._memory else 0.0, nlu_health=1.0 if self._nlu else 0.0, router_health=1.0 if self._router else 0.0,
            learner_health=1.0 if self._learner else 0.0, evolution_health=1.0 if self._recipe_gen else 0.0,
            governance_health=1.0 if self.governance and not self.governance.is_halted() else 0.0,
            reflection_health=1.0 if self._reflection else 0.0, world_model_health=1.0 if self._world_model else 0.0,
        )
        if self._reflection:
            try:
                r.reflection_health = max(0.0, 1.0 - self._reflection.get_stats().get("calibration_error", 0.5))
            except Exception:
                pass
        if self._memory:
            try:
                entries = self._memory.recent(20)
                r.executor_health = (sum(1 for e in entries if getattr(e, "status", None) == "success") / len(entries)) if entries else 0.5
            except Exception:
                r.executor_health = 0.5
        r.score = int(r.memory_health * 12 + r.nlu_health * 12 + r.router_health * 8 + r.executor_health * 16 + r.learner_health * 8 + r.evolution_health * 8 + r.governance_health * 16 + r.reflection_health * 10 + r.world_model_health * 10)
        self._consciousness_history = (self._consciousness_history + [r])[-self.MAX_HISTORY:]
        return r

    def get_consciousness_trend(self, limit: int = 20) -> List[int]:
        return [r.score for r in self._consciousness_history[-limit:]]

    def get_decision_traces(self, limit: int = 10) -> List[DecisionTrace]:
        return self._decision_traces[-limit:]

    def is_halted(self) -> bool:
        return self.governance.is_halted()

    def halt(self) -> None:
        self.governance.halt()

    def resume(self) -> None:
        self.governance.resume()


__all__ = ["AutonomousEngine", "ConsciousnessReport", "CycleResult", "DecisionTrace"]
