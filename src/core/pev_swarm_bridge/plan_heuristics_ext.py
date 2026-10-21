"""Extended goal decomposition (docs/canonical) and subagent payload construction."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .models import PevPhase, PevTask
from .plan_heuristics import (
    _decompose_bugfix,
    _decompose_security,
    _decompose_ui,
    _make_task,
)

logger = logging.getLogger(__name__)


def _decompose_docs(goal: str, mission_id: str, timestamp: str) -> list[PevTask]:
    t1, t2, t3 = f"task_{mission_id}_01", f"task_{mission_id}_02", f"task_{mission_id}_03"
    return [
        _make_task(
            t1, mission_id, 1, "Documentation Outline & Audience Scope",
            f"Define documentation structure and topics for: {goal}",
            "pm", PevPhase.PLAN, [], "Documentation outline drafted",
            timestamp, default_budget=20000,
        ),
        _make_task(
            t2, mission_id, 2, "Author Technical Documentation",
            f"Write complete, clear documentation for: {goal}",
            "docs-manager", PevPhase.EXECUTE, [t1],
            "Technical documents created and formatted",
            timestamp, default_budget=16000,
        ),
        _make_task(
            t3, mission_id, 3, "Review & Verify Documentation Completeness",
            f"Verify accuracy, links, and completeness for: {goal}",
            "code-reviewer", PevPhase.VERIFY, [t2],
            "Documentation validated with no broken references",
            timestamp, default_budget=16000, default_tools=["Read", "Bash", "Task"],
        ),
    ]


def _decompose_canonical(
    goal: str, mission_id: str, timestamp: str, project_root: Path
) -> list[PevTask]:
    t1, t2, t3 = f"task_{mission_id}_01", f"task_{mission_id}_02", f"task_{mission_id}_03"
    test_cmd = "python3 -m pytest tests/" if (project_root / "tests").exists() else None
    return [
        _make_task(
            t1, mission_id, 1, "Requirements & Architecture Specification",
            f"Analyze requirements and design system architecture for: {goal}",
            "pm", PevPhase.PLAN, [], "PRD and architecture specification complete",
            timestamp, default_budget=20000,
        ),
        _make_task(
            t2, mission_id, 2, "Core Engineering Implementation",
            f"Implement source code, modules, and interfaces for: {goal}",
            "eng", PevPhase.EXECUTE, [t1],
            "Implementation complete with zero build/syntax errors",
            timestamp, test_command=test_cmd, default_budget=24000,
        ),
        _make_task(
            t3, mission_id, 3, "Quality Assurance & Independent Verification",
            f"Perform independent testing, verification gates, and regression checks for: {goal}",
            "tester", PevPhase.VERIFY, [t2],
            "All automated tests and verification gates pass cleanly",
            timestamp, default_budget=16000, default_tools=["Read", "Bash", "Task"],
        ),
    ]


def decompose_goal_impl(
    goal: str, mission_id: str, timestamp: str, project_root: Path
) -> list[PevTask]:
    """Heuristically decompose goal into structured DAG tasks with 25-subagent roles."""
    lower_goal = goal.lower()
    if any(k in lower_goal for k in ("security", "audit", "pentest", "vulnerability", "sox")):
        return _decompose_security(goal, mission_id, timestamp, project_root)
    if any(k in lower_goal for k in ("fix", "bug", "error", "issue", "debug", "patch")):
        return _decompose_bugfix(goal, mission_id, timestamp, project_root)
    if any(k in lower_goal for k in ("ui", "frontend", "design", "css", "component", "page")):
        return _decompose_ui(goal, mission_id, timestamp)
    if any(k in lower_goal for k in ("doc", "docs", "documentation", "readme", "guide")):
        return _decompose_docs(goal, mission_id, timestamp)
    return _decompose_canonical(goal, mission_id, timestamp, project_root)


def build_subagent_payload_impl(
    role: str,
    task_desc: str,
    context_budget: int,
    allowed_tools: list[str],
    project_root: Path,
) -> dict[str, Any]:
    """Construct Antigravity define_subagent, invoke_subagent, and context payload."""
    try:
        from src.core.subagent_dispatch import build_subagent_dispatch_payload

        payload = build_subagent_dispatch_payload(
            role=role,
            task=task_desc,
            project_root=project_root,
        )
        if payload.get("ok"):
            payload["context_engineering"]["token_budget"] = context_budget
            payload["context_engineering"]["tool_allowlist"] = allowed_tools
            if "define_subagent" in payload:
                payload["define_subagent"]["tools"] = allowed_tools
            return payload
    except Exception as exc:
        logger.debug("Falling back to local subagent payload construction: %s", exc)

    return {
        "ok": True,
        "role": role,
        "task": task_desc,
        "define_subagent": {
            "name": f"mekong-{role}",
            "description": f"Mekong CLI Domain Subagent: {role}",
            "system_prompt": f"You are {role} in the Mekong CLI CEO Solo Harness.\nTask: {task_desc}",
            "tools": allowed_tools,
            "model_tier": "pro" if role in ("ceo", "sun-tzu", "cto") else "flash",
        },
        "invoke_subagent": {
            "subagent_name": f"mekong-{role}",
            "prompt": task_desc,
        },
        "context_engineering": {
            "token_budget": context_budget,
            "token_ceiling": 40000,
            "tool_allowlist": allowed_tools,
            "sop_layer": f"sops/{role}/",
        },
    }
