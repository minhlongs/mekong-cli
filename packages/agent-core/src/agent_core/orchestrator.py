"""SoloCompanyOrchestrator — drives CEO → Developer → Tester → Reviewer chain.

Synchronous for MVP: easier to test, no asyncio complexity. Upgrade path to
asyncio.Queue + _task_consumer loop is left for Phase 2.2 (feedback_monitor).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agent_core.agents.ceo import CEOAgent
from agent_core.agents.developer import DeveloperAgent
from agent_core.agents.reviewer import ReviewerAgent
from agent_core.agents.tester import TesterAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory


class Role(StrEnum):
    CEO = "ceo"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"


@dataclass
class Task:
    goal: str
    assigned_role: Role
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Any = None


@dataclass
class PipelineReport:
    goal: str
    plan: str
    artifact: str
    test: dict
    review: dict
    tasks: list[Task]

    def as_dict(self) -> dict:
        return {
            "goal": self.goal,
            "plan": self.plan,
            "artifact": self.artifact,
            "test": self.test,
            "review": self.review,
            "tasks": [
                {"id": t.id, "role": t.assigned_role.value, "status": t.status}
                for t in self.tasks
            ],
        }


class SoloCompanyOrchestrator:
    """Synchronous pipeline: CEO plans → Dev builds → Tester checks → Reviewer rates."""

    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.memory = memory or SeedMemory()
        self.agents = {
            Role.CEO: CEOAgent(llm=self.llm, memory=self.memory),
            Role.DEVELOPER: DeveloperAgent(llm=self.llm, memory=self.memory),
            Role.TESTER: TesterAgent(llm=self.llm, memory=self.memory),
            Role.REVIEWER: ReviewerAgent(llm=self.llm, memory=self.memory),
        }

    def _new_task(self, goal: str, role: Role, context: dict | None = None) -> Task:
        return Task(goal=goal, assigned_role=role, context=context or {})

    def process_goal(self, goal: str) -> PipelineReport:
        tasks: list[Task] = []

        ceo_task = self._new_task(goal, Role.CEO)
        tasks.append(ceo_task)
        ceo_task.status = "running"
        plan = self.agents[Role.CEO].plan(goal)
        ceo_task.result = plan
        ceo_task.status = "completed"

        dev_task = self._new_task(goal, Role.DEVELOPER, context={"plan": plan})
        tasks.append(dev_task)
        dev_task.status = "running"
        artifact = self.agents[Role.DEVELOPER].execute(
            task=f"Thực hiện bước đầu tiên trong kế hoạch: {goal}",
            plan_context=plan,
        )
        dev_task.result = artifact
        dev_task.status = "completed"

        tester_task = self._new_task(goal, Role.TESTER, context={"artifact": artifact})
        tasks.append(tester_task)
        tester_task.status = "running"
        test_report = self.agents[Role.TESTER].evaluate(goal, artifact)
        tester_task.result = test_report
        tester_task.status = "completed" if test_report["status"] == "pass" else "failed"

        reviewer_task = self._new_task(goal, Role.REVIEWER, context={"artifact": artifact})
        tasks.append(reviewer_task)
        reviewer_task.status = "running"
        review_report = self.agents[Role.REVIEWER].review(goal, artifact)
        reviewer_task.result = review_report
        reviewer_task.status = "completed" if review_report["verdict"] != "block" else "failed"

        return PipelineReport(
            goal=goal,
            plan=plan,
            artifact=artifact,
            test=test_report,
            review=review_report,
            tasks=tasks,
        )
