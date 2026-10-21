"""DAG scheduling, verification adapters, and intent classification."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.core.dag_scheduler import DAGScheduler
from src.core.protocols import Plan

from .models import CheckResult, CheckSpec, Criteria, Task, Verification

logger = logging.getLogger(__name__)


def _plan_has_dependencies(plan: Plan) -> bool:
    """Fast-path check: True if any step in the plan declares dependencies."""
    return DAGScheduler(plan.steps).has_dependencies()


def _topological_task_order(tasks: list[Task]) -> list[Task]:
    """Return ``tasks`` reordered so every task follows its dependencies."""
    if len(tasks) <= 1:
        return list(tasks)

    id_to_task: dict[str, Task] = {str(task.step.id): task for task in tasks}
    if len(id_to_task) != len(tasks):
        raise RuntimeError("duplicate task step ids in plan")

    sched = DAGScheduler(tasks)
    ordered_ids = sched.get_execution_order(strict=True)
    return [id_to_task[str(tid)] for tid in ordered_ids]


@dataclass
class _ExecResultLike:
    """Minimal ExecutionResult-shaped adapter for bridging core Result -> RecipeVerifier."""

    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _criteria_to_verifier_dict(criteria: Criteria) -> dict[str, Any]:
    """Translate core Criteria -> RecipeVerifier criteria-dict."""
    out: dict[str, Any] = {}
    for spec in criteria.checks:
        if spec.kind == "exit_code":
            out["exit_code"] = spec.params.get("expected", 0)
        elif spec.kind in ("output_pattern", "output_contains"):
            pattern = spec.params.get("pattern") or spec.params.get("text")
            if pattern:
                out.setdefault("output_contains", []).append(pattern)
        elif spec.kind == "output_not_contains":
            pattern = spec.params.get("pattern") or spec.params.get("text")
            if pattern:
                out.setdefault("output_not_contains", []).append(pattern)
        elif spec.kind == "file_exists":
            filepath = spec.params.get("path") or spec.params.get("filepath")
            if filepath:
                out.setdefault("file_exists", []).append(filepath)
        elif spec.kind == "file_not_exists":
            filepath = spec.params.get("path") or spec.params.get("filepath")
            if filepath:
                out.setdefault("file_not_exists", []).append(filepath)
        else:
            logger.debug("verify: skipping unknown check kind=%s", spec.kind)
    return out


def _report_to_verification(report: Any) -> Verification:
    """Translate RecipeVerifier VerificationReport -> core Verification."""
    checks: list[CheckResult] = []
    for check in report.checks:
        checks.append(
            CheckResult(
                check=CheckSpec(kind=check.name),
                passed=(check.status.value == "passed"),
                detail=check.message,
            )
        )
    failures: list[str] = list(report.errors or [])
    return Verification(passed=report.passed, checks=checks, failures=failures)


_INTENT_AGENT_KEYWORDS: dict[str, str] = {
    "code": "cto",
    "refactor": "cto",
    "implement": "cto",
    "develop": "cto",
    "debug": "cto",
    "review": "cto",
    "marketing": "cmo",
    "campaign": "cmo",
    "brand": "cmo",
    "operations": "coo",
    "logistics": "coo",
    "workflow": "coo",
    "finance": "cfo",
    "budget": "cfo",
    "accounting": "cfo",
    "analysis": "cso",
    "analyze": "cso",
    "strategy": "cso",
    "competitive": "cso",
    "market": "cso",
    "plan": "planner",
    "roadmap": "planner",
    "architecture": "planner",
}


def _classify_intent(intent: str | None) -> str:
    """Map a goal intent to a registered built-in agent name."""
    lowered = (intent or "").lower()
    for keyword, agent_name in _INTENT_AGENT_KEYWORDS.items():
        if keyword in lowered:
            return agent_name
    return ""
