# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Role-matching and goal-decomposition heuristics for C1 Orchestration."""

from __future__ import annotations

from src.harness.agents.factory import AgentFactory
from src.harness.orchestration.models import ChildTask

_ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "eng": (
        "code", "build", "fix", "implement", "api", "backend",
        "frontend", "test", "debug", "refactor", "database", "deploy",
    ),
    "cto": ("architecture", "design", "system", "review", "audit"),
    "cmo": ("marketing", "campaign", "copy", "seo", "content", "brand"),
    "cfo": ("financial", "budget", "revenue", "cost", "invoice"),
    "coo": ("monitor", "health", "ops", "worker", "deployment", "infra"),
    "pm": ("plan", "roadmap", "spec", "requirement", "sprint"),
    "analyst": ("analyze", "research", "data", "report", "forecast"),
    "sales": ("sales", "pipeline", "prospect", "deal", "outreach"),
    "docs": ("document", "readme", "docs", "guide"),
    "security": ("security", "vulnerability", "secret", "access"),
}

_ROLE_CANONICAL: dict[str, str] = {
    "eng": "eng", "engineering": "eng", "developer": "eng",
    "cto": "cto", "architect": "cto",
    "cmo": "cmo", "marketing": "cmo",
    "cfo": "cfo", "finance": "cfo",
    "coo": "ops", "ops": "ops", "operations": "ops",
    "pm": "pm", "product": "pm",
    "analyst": "analyst", "sales": "sales",
    "docs": "docs", "documentation": "docs",
    "security": "security", "audit": "security",
}


def _match_agent_id(description: str, factory: AgentFactory) -> str:
    """Pick the best agent_id for *description* from the factory registry."""
    desc_lower = description.lower()
    best_id: str | None = None
    best_score = 0
    for role, keywords in _ROLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in desc_lower)
        if score > best_score:
            best_score = score
            canonical = _ROLE_CANONICAL.get(role, role)
            if canonical in factory.list_available():
                best_id = canonical
    if best_id is None:
        for alias, canonical in _ROLE_CANONICAL.items():
            if alias in desc_lower and canonical in factory.list_available():
                best_id = canonical
                break
    if best_id is None:
        available = factory.list_available()
        best_id = available[0] if available else "ceo"
    return best_id


def decompose_goal(goal: str, factory: AgentFactory) -> list[ChildTask]:
    """Split a high-level goal into role-assigned child tasks."""
    assigned_roles: set[str] = set()
    primary_id = _match_agent_id(goal, factory)
    children: list[ChildTask] = [
        ChildTask(
            id="child-001",
            description=goal[:120],
            agent_id=primary_id,
            input={"goal": goal},
        )
    ]
    assigned_roles.add(primary_id)
    goal_lower = goal.lower()
    for role, kws in _ROLE_KEYWORDS.items():
        canonical = _ROLE_CANONICAL.get(role, role)
        if canonical in assigned_roles or canonical not in factory.list_available():
            continue
        if any(kw in goal_lower for kw in kws):
            children.append(
                ChildTask(
                    id=f"child-{len(children)+1:03d}",
                    description=f"{canonical} sub-task for: {goal[:80]}",
                    agent_id=canonical,
                    input={"goal": goal, "role": canonical},
                )
            )
            assigned_roles.add(canonical)
    return children
