"""Single-job executor bridging agent-forest worker with agent-core.

Modes:
- ``max_rounds=1`` (default): legacy CEO→Developer single-pass — fast, no retry.
- ``max_rounds>=2``: agent-core FeedbackLoop (CEO→Dev→Tester→Reviewer + Ops +
  Analyst with bounded retry). Closes the self-heal loop per Solo-Platform PDF Bước 5.

Each worker process sets ``AGENT_CORE_OUTPUTS`` to the per-user sandbox
BEFORE importing ``agent_core.tools.file_system`` so the sandbox points at
``outputs/{user_id}/`` rather than the worker's cwd.
"""

from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class JobOutcome:
    status: str  # "completed" | "failed"
    result: str | None = None
    error: str | None = None


def run_job(prompt: str, user_sandbox: Path, *, max_rounds: int = 1) -> JobOutcome:
    """Execute a single job, writing any artifact under ``user_sandbox``."""
    os.environ["AGENT_CORE_OUTPUTS"] = str(user_sandbox)
    try:
        fs = importlib.import_module("agent_core.tools.file_system")
        importlib.reload(fs)
        from agent_core.llm_client import LLMClient
        from agent_core.memory import SeedMemory

        memory = SeedMemory(root=user_sandbox / ".memory")
        llm = LLMClient()

        if max_rounds >= 2:
            return _run_feedback_loop(prompt, llm, memory, max_rounds)
        return _run_single_pass(prompt, llm, memory, fs)
    except Exception as exc:  # noqa: BLE001 — worker-level catch-all is intentional
        return JobOutcome(status="failed", error=f"{type(exc).__name__}: {exc}"[:4000])


def _run_single_pass(prompt: str, llm, memory, fs_module) -> JobOutcome:
    from agent_core.agents.ceo import CEOAgent
    from agent_core.agents.developer import DeveloperAgent

    ceo = CEOAgent(llm=llm, memory=memory)
    dev = DeveloperAgent(llm=llm, memory=memory)
    plan = ceo.plan(prompt)
    dev_reply = dev.execute(prompt, plan_context=plan)
    artifact_msg = _maybe_write_artifact(dev_reply, fs_module)
    result = dev_reply if not artifact_msg else f"{dev_reply}\n\n{artifact_msg}"
    return JobOutcome(status="completed", result=result[:4000])


def _run_feedback_loop(prompt: str, llm, memory, max_rounds: int) -> JobOutcome:
    """Run agent-core FeedbackLoop; artifact writing is delegated to DeveloperAgent."""
    from agent_core.feedback_loop import FeedbackLoop

    loop = FeedbackLoop(llm=llm, memory=memory)
    session = loop.process_goal(prompt, max_rounds=max_rounds)
    final = session.final
    verdict = final.review.get("verdict", "unknown")
    summary = _summarize_session(session)
    status = "completed" if verdict == "ship" else "failed"
    if status == "failed":
        return JobOutcome(status=status, error=summary[:4000])
    return JobOutcome(status=status, result=summary[:4000])


def _summarize_session(session) -> str:
    """Compact human-readable session summary for webhook/result."""
    lines = [f"rounds={len(session.rounds)}"]
    for r in session.rounds:
        verdict = r.report.review.get("verdict", "?")
        test_status = r.report.test.get("status", "?")
        severity = r.ops.get("severity", "?")
        trend = r.analyst.get("trend", "?")
        lines.append(
            f"#{r.round_index}: verdict={verdict} test={test_status} "
            f"ops={severity} trend={trend}"
        )
    final = session.final
    lines.append("---")
    lines.append(str(final.artifact)[:1500])
    return "\n".join(lines)


def _maybe_write_artifact(reply: str, fs_module) -> str | None:
    try:
        from agent_core.base_agent import BaseAgent

        parsed = BaseAgent.parse_json(reply)
    except Exception:  # noqa: BLE001
        return None
    path = parsed.get("file_path") if isinstance(parsed, dict) else None
    content = parsed.get("content") if isinstance(parsed, dict) else None
    if not (isinstance(path, str) and isinstance(content, str)):
        return None
    try:
        return fs_module.write_file(path, content)
    except Exception as exc:  # noqa: BLE001
        return f"artifact write failed: {exc}"
