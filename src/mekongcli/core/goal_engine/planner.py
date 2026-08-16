# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Deterministic role-aware goal decomposition for the v1 vertical slice."""

from __future__ import annotations

from .models import AcceptanceCriterion, AgentRole, GoalTask, new_id


class GoalPlanner:
    """Builds a practical starter task graph from a high-level goal."""

    def decompose(
        self,
        goal_id: str,
        title: str,
        retry_limit: int = 3,
    ) -> tuple[list[GoalTask], list[AcceptanceCriterion]]:
        architect = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Define architecture and module boundaries",
            description=f"Architect the delivery plan for: {title}",
            role=AgentRole.ARCHITECT,
            max_attempts=retry_limit,
        )
        backend = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Implement backend and orchestration contracts",
            description="Build the service interfaces, persistence, and orchestration behavior.",
            role=AgentRole.BACKEND,
            depends_on=[architect.id],
            max_attempts=retry_limit,
        )
        infra = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Prepare runtime, infra, and observability hooks",
            description="Wire local runtime, compose profile, telemetry, and operational defaults.",
            role=AgentRole.INFRA,
            depends_on=[architect.id],
            max_attempts=retry_limit,
        )
        qa = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Verify behavior with tests and adversarial checks",
            description="Run the verification profile and record evidence.",
            role=AgentRole.QA,
            depends_on=[backend.id, infra.id],
            max_attempts=retry_limit,
        )
        security = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Review safety boundaries and secret exposure risk",
            description="Check command safety, permissions, and dependency/security gates.",
            role=AgentRole.SECURITY,
            depends_on=[backend.id, infra.id],
            max_attempts=retry_limit,
        )
        docs = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Document workflow and operational usage",
            description="Update user-facing docs, architecture notes, and examples.",
            role=AgentRole.DOCS,
            depends_on=[backend.id, infra.id],
            max_attempts=retry_limit,
        )
        reviewer = GoalTask(
            id=new_id("task"),
            goal_id=goal_id,
            title="Perform final architecture and quality review",
            description="Check consistency, duplicate systems, and acceptance criteria.",
            role=AgentRole.REVIEWER,
            depends_on=[qa.id, security.id, docs.id],
            max_attempts=retry_limit,
        )
        criteria = [
            AcceptanceCriterion(
                id=new_id("criterion"),
                description="/goal command persists a goal and resumable task graph.",
            ),
            AcceptanceCriterion(
                id=new_id("criterion"),
                description="Swarm roles are assigned and recorded for each task.",
            ),
            AcceptanceCriterion(
                id=new_id("criterion"),
                description="Required verification gates pass before the goal is satisfied.",
            ),
            AcceptanceCriterion(
                id=new_id("criterion"),
                description="Execution checkpoints, events, and memory survive process restarts.",
            ),
        ]
        return [architect, backend, infra, qa, security, docs, reviewer], criteria
