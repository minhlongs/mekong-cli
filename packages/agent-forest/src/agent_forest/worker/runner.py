"""Single-job executor: CEO plan → Developer execute → write artifact.

Each worker process sets AGENT_CORE_OUTPUTS to the per-user sandbox directory
BEFORE importing `agent_core.tools.file_system`, so the sandbox points at
`outputs/{user_id}/` rather than the worker's cwd.
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


def run_job(prompt: str, user_sandbox: Path) -> JobOutcome:
    """Execute a single CEO→Developer pass, writing any artifact under user_sandbox."""
    os.environ["AGENT_CORE_OUTPUTS"] = str(user_sandbox)
    try:
        # Delayed import so AGENT_CORE_OUTPUTS takes effect.
        fs = importlib.import_module("agent_core.tools.file_system")
        importlib.reload(fs)
        from agent_core.agents.ceo import CEOAgent
        from agent_core.agents.developer import DeveloperAgent
        from agent_core.llm_client import LLMClient
        from agent_core.memory import SeedMemory

        memory = SeedMemory(root=user_sandbox / ".memory")
        llm = LLMClient()
        ceo = CEOAgent(llm=llm, memory=memory)
        dev = DeveloperAgent(llm=llm, memory=memory)

        plan = ceo.plan(prompt)
        dev_reply = dev.execute(prompt, plan_context=plan)
        artifact_msg = _maybe_write_artifact(dev_reply, fs)
        result = dev_reply if not artifact_msg else f"{dev_reply}\n\n{artifact_msg}"
        return JobOutcome(status="completed", result=result[:4000])
    except Exception as exc:  # noqa: BLE001 — worker-level catch-all is intentional
        return JobOutcome(status="failed", error=f"{type(exc).__name__}: {exc}"[:4000])


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
