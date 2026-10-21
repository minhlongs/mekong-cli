"""Goal decomposition task builders for security, bugfix, and UI workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .constants import ROLE_CONTEXT_BUDGETS, ROLE_TOOL_ALLOWLISTS
from .models import PevPhase, PevTask, TaskStatus, VerificationCriteria


def _make_task(
    task_id: str,
    mission_id: str,
    order_idx: int,
    title: str,
    description: str,
    role: str,
    phase: PevPhase,
    depends_on: list[str],
    rubric_prompt: str,
    timestamp: str,
    test_command: Optional[str] = None,
    default_budget: int = 20000,
    default_tools: Optional[list[str]] = None,
) -> PevTask:
    tools_fallback = default_tools or ["Read", "Write", "Edit", "Bash", "Task"]
    return PevTask(
        task_id=task_id,
        mission_id=mission_id,
        order_idx=order_idx,
        title=title,
        description=description,
        role=role,
        phase=phase,
        status=TaskStatus.PENDING,
        depends_on=depends_on,
        context_budget=ROLE_CONTEXT_BUDGETS.get(role, default_budget),
        allowed_tools=ROLE_TOOL_ALLOWLISTS.get(role, tools_fallback),
        verification_criteria=VerificationCriteria(
            exit_code=0,
            test_command=test_command,
            rubric_prompt=rubric_prompt,
        ),
        created_at=timestamp,
        updated_at=timestamp,
    )


def _decompose_security(
    goal: str, mission_id: str, timestamp: str, project_root: Path
) -> list[PevTask]:
    t1, t2, t3 = f"task_{mission_id}_01", f"task_{mission_id}_02", f"task_{mission_id}_03"
    test_cmd = (
        "python3 -m pytest tests/test_core_boundary.py"
        if (project_root / "tests" / "test_core_boundary.py").exists()
        else None
    )
    return [
        _make_task(
            t1, mission_id, 1, "Security Posture & Boundary Audit",
            f"Analyze codebase and architecture for security risks in goal: {goal}",
            "cso", PevPhase.PLAN, [], "CSO produces comprehensive security risk assessment",
            timestamp, default_budget=20000, default_tools=["Read", "Bash", "Task"],
        ),
        _make_task(
            t2, mission_id, 2, "Implement Hardening & Boundary Enforcement",
            f"Remediate security risks and enforce boundary controls for: {goal}",
            "eng", PevPhase.EXECUTE, [t1], "Zero external vendor SDK leaks; boundary passes 100%",
            timestamp, test_command=test_cmd, default_budget=24000,
        ),
        _make_task(
            t3, mission_id, 3, "Independent Security & Regression Verification",
            f"Validate hardening measures and ensure regression-free deployment for: {goal}",
            "code-reviewer", PevPhase.VERIFY, [t2],
            "Independent verifier confirms zero security violations and passing gates",
            timestamp, default_budget=16000, default_tools=["Read", "Bash", "Task"],
        ),
    ]


def _decompose_bugfix(
    goal: str, mission_id: str, timestamp: str, project_root: Path
) -> list[PevTask]:
    t1, t2, t3 = f"task_{mission_id}_01", f"task_{mission_id}_02", f"task_{mission_id}_03"
    test_cmd = "python3 -m pytest tests/" if (project_root / "tests").exists() else None
    return [
        _make_task(
            t1, mission_id, 1, "Root Cause Analysis & Diagnosis",
            f"Investigate failure symptoms and identify root cause for: {goal}",
            "debugger", PevPhase.PLAN, [],
            "Root cause identified with reproducer test or scenario",
            timestamp, default_budget=24000,
        ),
        _make_task(
            t2, mission_id, 2, "Implement Minimal Bug Fix",
            f"Apply minimal, robust fix to resolve defect: {goal}",
            "eng", PevPhase.EXECUTE, [t1],
            "Bug resolved without introducing collateral regressions",
            timestamp, test_command=test_cmd, default_budget=24000,
        ),
        _make_task(
            t3, mission_id, 3, "Regression & Gate Verification",
            f"Verify fix correctness and test suite stability for: {goal}",
            "tester", PevPhase.VERIFY, [t2],
            "Tester confirms bug fix verification and regression tests pass",
            timestamp, default_budget=16000, default_tools=["Read", "Bash", "Task"],
        ),
    ]


def _decompose_ui(goal: str, mission_id: str, timestamp: str) -> list[PevTask]:
    t1, t2, t3 = f"task_{mission_id}_01", f"task_{mission_id}_02", f"task_{mission_id}_03"
    return [
        _make_task(
            t1, mission_id, 1, "UI/UX Architecture & Component Spec",
            f"Specify interface layout, interactions, and design constraints for: {goal}",
            "ui-ux-designer", PevPhase.PLAN, [],
            "Design spec completed and verified against UX principles",
            timestamp, default_budget=20000,
        ),
        _make_task(
            t2, mission_id, 2, "Build UI Components & Wiring",
            f"Implement frontend components and business logic for: {goal}",
            "fullstack-developer", PevPhase.EXECUTE, [t1],
            "UI components render correctly with expected functionality",
            timestamp, default_budget=24000,
        ),
        _make_task(
            t3, mission_id, 3, "UI Quality & Responsive Verification",
            f"Validate component rendering and accessibility for: {goal}",
            "tester", PevPhase.VERIFY, [t2],
            "All visual and behavioral criteria verified",
            timestamp, default_budget=16000, default_tools=["Read", "Bash", "Task"],
        ),
    ]
