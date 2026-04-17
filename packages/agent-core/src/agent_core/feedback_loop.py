"""FeedbackLoop — wraps SoloCompanyOrchestrator with Ops + Analyst + retry rounds.

Sync MVP: runs the pipeline, consults Ops + Analyst, re-runs the pipeline with
Analyst recommendations appended to the goal if verdict is revise/block or Ops
raises a non-info severity. Bounded by `max_rounds` to avoid runaway loops.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_core.agents.analyst import AnalystAgent
from agent_core.agents.ops import OpsAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory
from agent_core.orchestrator import PipelineReport, SoloCompanyOrchestrator


@dataclass
class FeedbackRound:
    round_index: int
    report: PipelineReport
    ops: dict
    analyst: dict


@dataclass
class FeedbackSession:
    goal: str
    rounds: list[FeedbackRound] = field(default_factory=list)

    @property
    def final(self) -> PipelineReport:
        return self.rounds[-1].report

    def as_dict(self) -> dict:
        return {
            "goal": self.goal,
            "rounds": [
                {
                    "round": r.round_index,
                    "review_verdict": r.report.review["verdict"],
                    "review_score": r.report.review["score"],
                    "test_status": r.report.test["status"],
                    "ops_severity": r.ops["severity"],
                    "analyst_trend": r.analyst["trend"],
                }
                for r in self.rounds
            ],
            "final": self.final.as_dict(),
        }


class FeedbackLoop:
    def __init__(
        self,
        orchestrator: SoloCompanyOrchestrator | None = None,
        ops: OpsAgent | None = None,
        analyst: AnalystAgent | None = None,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        self.llm = llm or LLMClient()
        self.memory = memory or SeedMemory()
        self.orchestrator = orchestrator or SoloCompanyOrchestrator(
            llm=self.llm, memory=self.memory
        )
        self.ops = ops or OpsAgent(llm=self.llm, memory=self.memory)
        self.analyst = analyst or AnalystAgent(llm=self.llm, memory=self.memory)

    def _needs_retry(self, ops_report: dict, pipeline_report: PipelineReport) -> bool:
        if pipeline_report.review["verdict"] in ("revise", "block"):
            return True
        if pipeline_report.test["status"] == "fail":
            return True
        if ops_report["severity"] in ("warn", "critical"):
            return True
        return False

    def _next_goal(self, original_goal: str, analyst_report: dict) -> str:
        recs = analyst_report.get("recommendations", [])
        if not recs:
            return original_goal
        bullet = "\n".join(f"- {r}" for r in recs[:5])
        return (
            f"{original_goal}\n\n"
            f"[Vòng lặp cải tiến] Ưu tiên xử lý các khuyến nghị sau:\n{bullet}"
        )

    def process_goal(self, goal: str, max_rounds: int = 2) -> FeedbackSession:
        if max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")
        session = FeedbackSession(goal=goal)
        history: list[dict] = []
        current_goal = goal

        for i in range(1, max_rounds + 1):
            report = self.orchestrator.process_goal(current_goal)
            ops_report = self.ops.monitor(report.as_dict())
            analyst_report = self.analyst.analyze(report.as_dict(), history=history)
            session.rounds.append(
                FeedbackRound(
                    round_index=i,
                    report=report,
                    ops=ops_report,
                    analyst=analyst_report,
                )
            )
            history.append(report.as_dict())
            if not self._needs_retry(ops_report, report):
                break
            if i == max_rounds:
                break
            current_goal = self._next_goal(goal, analyst_report)

        return session
