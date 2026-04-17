"""FeedbackLoop — wraps SoloCompanyOrchestrator with Ops + Analyst + retry rounds.

Sync MVP: runs the pipeline, consults Ops + Analyst, re-runs the pipeline with
Analyst recommendations appended to the goal if verdict is revise/block or Ops
raises a non-info severity. Bounded by `max_rounds` to avoid runaway loops.

Each session persists its per-round compact dict into SeedMemory under
``agent_id="feedback_session"`` so subsequent sessions' AnalystAgent can
observe cross-session trend data (closes PDF "Hệ thống ghi nhật ký và học hồi").
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from agent_core.agents.analyst import AnalystAgent
from agent_core.agents.ops import OpsAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory
from agent_core.orchestrator import PipelineReport, SoloCompanyOrchestrator

_SESSION_AGENT_ID = "feedback_session"


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

    def persist(self, memory: SeedMemory) -> list[str]:
        """Store each round as an individual memory record; return doc ids."""
        ids: list[str] = []
        for r in self.rounds:
            payload = {
                "goal": self.goal,
                "round": r.round_index,
                "review": r.report.review,
                "test": r.report.test,
                "ops": r.ops,
                "analyst": r.analyst,
            }
            ids.append(
                memory.remember(
                    agent_id=_SESSION_AGENT_ID,
                    content=json.dumps(payload, ensure_ascii=False),
                    metadata={
                        "round": r.round_index,
                        "verdict": r.report.review.get("verdict", "?"),
                        "trend": r.analyst.get("trend", "?"),
                    },
                )
            )
        return ids


def list_recent_sessions(memory: SeedMemory, limit: int = 10) -> list[dict]:
    """Return persisted rounds with timestamps, newest first, for operator inspection.

    Each row: ``{created_at, round, verdict, trend, goal, score}`` — ready to
    feed into a formatter. Malformed rows are skipped silently.
    """
    records = memory.get_recent(_SESSION_AGENT_ID, limit=limit)
    rows: list[dict] = []
    for rec in records:
        try:
            payload = json.loads(rec.content)
        except json.JSONDecodeError:
            continue
        review = payload.get("review", {}) if isinstance(payload, dict) else {}
        rows.append(
            {
                "created_at": rec.created_at,
                "round": payload.get("round", rec.metadata.get("round", 0)),
                "verdict": review.get("verdict", rec.metadata.get("verdict", "?")),
                "score": review.get("score", 0),
                "trend": payload.get("analyst", {}).get(
                    "trend", rec.metadata.get("trend", "?")
                ),
                "goal": (payload.get("goal") or "")[:60],
            }
        )
    return rows


def load_recent_history(memory: SeedMemory, limit: int = 3) -> list[dict]:
    """Return up to ``limit`` most-recent persisted rounds as pipeline-report dicts.

    Used to seed Analyst history so it can observe cross-session trends.
    Malformed rows are skipped silently — memory is best-effort, never load-bearing.
    """
    records = memory.get_recent(_SESSION_AGENT_ID, limit=limit)
    out: list[dict] = []
    for rec in records:
        try:
            payload = json.loads(rec.content)
        except json.JSONDecodeError:
            continue
        out.append(
            {
                "review": payload.get("review", {}),
                "test": payload.get("test", {}),
                "ops": payload.get("ops", {}),
            }
        )
    return out


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

    def process_goal(
        self, goal: str, max_rounds: int = 2, *, persist: bool = True
    ) -> FeedbackSession:
        if max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")
        session = FeedbackSession(goal=goal)
        # Seed Analyst history with prior sessions so trends span beyond this run.
        history: list[dict] = load_recent_history(self.memory, limit=3)
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

        if persist:
            session.persist(self.memory)
            _apply_retention(self.memory)
        return session


def _apply_retention(memory: SeedMemory) -> None:
    """Auto-prune oldest feedback_session rows when AGENT_CORE_SESSION_RETENTION>0.

    Default 0 = unbounded (preserves PR #117 behaviour). Parsing errors silent —
    retention is best-effort, never a hard failure mode for the loop.
    """
    raw = os.getenv("AGENT_CORE_SESSION_RETENTION")
    if not raw:
        return
    try:
        keep = int(raw)
    except ValueError:
        return
    if keep <= 0:
        return
    try:
        memory.prune_agent(_SESSION_AGENT_ID, keep_last_n=keep)
    except Exception:  # noqa: BLE001 — retention is best-effort
        pass
