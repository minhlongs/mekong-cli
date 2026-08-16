# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Role specialization and deterministic task assignment."""

from __future__ import annotations

from dataclasses import dataclass

from src.mekongcli.core.goal_engine.models import AgentRole, GoalTask


@dataclass(frozen=True)
class AgentRoleSpec:
    role: AgentRole
    responsibilities: tuple[str, ...]
    review_required: bool = True


@dataclass(frozen=True)
class TaskAssignment:
    task_id: str
    role: AgentRole
    rationale: str


class RoleRegistry:
    """Local role registry for the v1 autonomous swarm."""

    def __init__(self) -> None:
        self._roles = {
            AgentRole.ARCHITECT: AgentRoleSpec(
                AgentRole.ARCHITECT,
                ("system design", "module boundaries", "event-driven patterns"),
            ),
            AgentRole.BACKEND: AgentRoleSpec(
                AgentRole.BACKEND,
                ("APIs", "services", "business logic"),
            ),
            AgentRole.FRONTEND: AgentRoleSpec(
                AgentRole.FRONTEND,
                ("UI", "dashboard", "visualization"),
            ),
            AgentRole.INFRA: AgentRoleSpec(
                AgentRole.INFRA,
                ("Docker", "CI/CD", "observability"),
            ),
            AgentRole.QA: AgentRoleSpec(
                AgentRole.QA,
                ("unit tests", "integration tests", "adversarial cases"),
            ),
            AgentRole.SECURITY: AgentRoleSpec(
                AgentRole.SECURITY,
                ("secrets scanning", "dependency audit", "exploit detection"),
            ),
            AgentRole.DOCS: AgentRoleSpec(
                AgentRole.DOCS,
                ("README", "architecture docs", "API specs"),
            ),
            AgentRole.QUANT: AgentRoleSpec(
                AgentRole.QUANT,
                ("algorithmic logic", "statistics", "simulations"),
            ),
            AgentRole.REVIEWER: AgentRoleSpec(
                AgentRole.REVIEWER,
                ("code quality", "architecture consistency", "duplication detection"),
            ),
        }

    def list_roles(self) -> list[AgentRoleSpec]:
        return list(self._roles.values())

    def assign(self, task: GoalTask) -> TaskAssignment:
        spec = self._roles[task.role]
        return TaskAssignment(
            task_id=task.id,
            role=task.role,
            rationale=", ".join(spec.responsibilities[:2]),
        )
