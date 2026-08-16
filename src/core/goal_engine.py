# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""GoalEngine — decompose, adapt, and commit high-level goals."""
from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.core.error_sanitizer import sanitize
from src.core.llm_client import get_client
from src.core.protocols import Plan, PlanStatus, Step

logger = logging.getLogger(__name__)

# Instruction-override patterns to reject in user input
_INJECTION_PATTERNS = re.compile(
    r"(?i)(ignore\s+(all\s+)?previous\s+instructions|"
    r"disregard\s+(all\s+)?prior|"
    r"new\s+instruction|"
    r"you\s+are\s+now|"
    r"system\s*:\s*|"
    r"assistant\s*:\s*)"
)


def _safe_input(text: str) -> str:
    """Reject or escape input resembling instruction overrides."""
    if _INJECTION_PATTERNS.search(text):
        logger.warning("[GOAL-ENGINE] blocked injection-like input")
        return "[REDACTED: input blocked]"
    return text


def _safe_error(text: str) -> str:
    """Sanitize error output before embedding in prompts."""
    return re.sub(r"(?i)(system|assistant|user)\s*:", r"\\1:", text or "")


@dataclass
class FailureInfo:
    step_id: str
    error: str
    output: str = ""


@dataclass
class GoalResult:
    plan_id: str
    success: bool
    step_results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@runtime_checkable
class GoalEngineProtocol(Protocol):
    def decompose(self, goal: str) -> Plan: ...
    def adapt(self, plan: Plan, failure: FailureInfo) -> Plan: ...
    def commit(self, plan: Plan) -> GoalResult: ...


_SYSTEM_PROMPT = (
    "Decompose a high-level goal into atomic executable steps. "
    "Return a JSON array: [{id, description, dependencies}]. "
    "id is a short slug, dependencies are step ids. Return ONLY valid JSON."
)
_MAX_RETRIES = 2


def _parse_steps(raw: str) -> list[Step]:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
    data = json.loads(text)
    if not isinstance(data, list):
        data = data.get("steps", []) if isinstance(data, dict) else []
    return [
        Step(id=str(it.get("id", f"s{i}")), description=str(it.get("description", "")),
             dependencies=list(it.get("dependencies", [])))
        for i, it in enumerate(data) if isinstance(it, dict)
    ]


def _topo_sort(steps: list[Step]) -> list[Step]:
    by_id = {s.id: s for s in steps}
    visited: set[str] = set()
    result: list[Step] = []

    def _visit(sid: str) -> None:
        if sid in visited or sid not in by_id:
            return
        visited.add(sid)
        for dep in by_id[sid].dependencies:
            _visit(dep)
        result.append(by_id[sid])

    for s in steps:
        _visit(s.id)
    return result


class GoalEngineImpl:
    """Concrete GoalEngine: decompose via LLM, replan on failure, commit."""

    def __init__(self, llm_client: Any | None = None) -> None:
        self._llm = llm_client

    def _client(self) -> Any:
        return self._llm or get_client()

    def _chat(self, messages: list[dict[str, str]]) -> str:
        resp = self._client().chat(messages)
        return resp.content if hasattr(resp, "content") else str(resp)

    def decompose(self, goal: str) -> Plan:
        pid = f"plan-{uuid.uuid4().hex[:12]}"
        client = self._client()
        if not getattr(client, "is_available", False):
            logger.warning("[GOAL-ENGINE] LLM unavailable — single-step fallback")
            return Plan(id=pid, goal=goal,
                        steps=[Step(id="s0", description=goal)])
        try:
            raw = self._chat([{"role": "system", "content": _SYSTEM_PROMPT},
                              {"role": "user", "content": _safe_input(goal)}])
            steps = _parse_steps(raw)
            if not steps:
                raise ValueError("LLM returned empty step list")
            return Plan(id=pid, goal=goal, steps=steps)
        except Exception as exc:
            logger.error("[GOAL-ENGINE] decompose failed: %s", sanitize(exc))
            return Plan(id=pid, goal=goal,
                        steps=[Step(id="s0", description=goal)])

    def adapt(self, plan: Plan, failure: FailureInfo) -> Plan:
        retries = int(plan.metadata.get("retries", 0))
        if retries >= _MAX_RETRIES:
            plan.status = PlanStatus.FAILED
            logger.warning("[GOAL-ENGINE] max retries (%d) for %s",
                           _MAX_RETRIES, plan.id)
            return plan
        failed_idx = next(
            (i for i, s in enumerate(plan.steps) if s.id == failure.step_id), None)
        if failed_idx is None:
            plan.status = PlanStatus.FAILED
            return plan
        # Collect failed + downstream dependents
        failed_ids: set[str] = {failure.step_id}
        changed = True
        while changed:
            changed = False
            for s in plan.steps:
                if s.id not in failed_ids and any(d in failed_ids for d in s.dependencies):
                    failed_ids.add(s.id)
                    changed = True
        # LLM replan
        prompt = (f"Goal: {plan.goal}\nFailed step: {plan.steps[failed_idx].description}\n"
                  f"Error: {_safe_error(failure.error)}\nReturn JSON array of replacement steps.")
        new_steps: list[Step] = []
        client = self._client()
        if getattr(client, "is_available", False):
            try:
                raw = self._chat([{"role": "system", "content": _SYSTEM_PROMPT},
                                  {"role": "user", "content": prompt}])
                new_steps = _parse_steps(raw)
            except Exception as exc:
                logger.error("[GOAL-ENGINE] adapt failed: %s", sanitize(exc))
        if not new_steps:
            new_steps = [Step(id=failure.step_id,
                              description=plan.steps[failed_idx].description)]
        plan.steps = [s for s in plan.steps if s.id not in failed_ids] + new_steps
        plan.metadata["retries"] = retries + 1
        plan.status = PlanStatus.IN_PROGRESS
        return plan

    def commit(self, plan: Plan) -> GoalResult:
        plan.status = PlanStatus.IN_PROGRESS
        results: list[dict[str, Any]] = []
        completed: set[str] = set()
        for step in _topo_sort(plan.steps):
            unmet = set(step.dependencies) - completed
            if unmet:
                results.append({"step_id": step.id, "skipped": True,
                                "reason": f"unmet deps: {unmet}"})
                continue
            try:
                client = self._client()
                if not getattr(client, "is_available", False):
                    raise RuntimeError("LLM unavailable")
                safe_desc = _safe_input(step.description)
                output = self._chat([{"role": "system", "content": "Execute this step."},
                                     {"role": "user", "content": safe_desc}])
                completed.add(step.id)
                results.append({"step_id": step.id, "success": True, "output": output})
            except Exception as exc:
                plan.status = PlanStatus.FAILED
                results.append({"step_id": step.id, "success": False,
                                "error": sanitize(exc)})
                return GoalResult(plan_id=plan.id, success=False,
                                  step_results=results, error=sanitize(exc))
        plan.status = PlanStatus.COMPLETED
        return GoalResult(plan_id=plan.id, success=True, step_results=results)
