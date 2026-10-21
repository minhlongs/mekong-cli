# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway authentication, project discovery, and execution summary helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, Request

from src.core.gateway.models import HumanSummary, ProjectInfo

if TYPE_CHECKING:
    from src.core.orchestrator import OrchestrationResult


def verify_token(token: str) -> None:
    """Verify the provided token against MEKONG_API_TOKEN env var."""
    expected = os.environ.get("MEKONG_API_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="MEKONG_API_TOKEN not configured on server",
        )
    import hmac as _hmac
    if not _hmac.compare_digest(token.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid token")


def require_swarm_token(request: Request) -> None:
    """Auth dependency for swarm endpoints."""
    token = request.headers.get("X-API-Key", "") or request.query_params.get("token", "")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header or token query parameter",
        )
    verify_token(token)


def build_human_summary(result: OrchestrationResult) -> HumanSummary:
    """Generate a non-dev friendly summary from orchestration result."""
    status = result.status.value
    rate = result.success_rate

    if status == "success":
        en = f"All done! {result.completed_steps} tasks completed successfully."
        vi = f"Xong! {result.completed_steps} tac vu hoan thanh thanh cong."
    elif status == "partial":
        en = (f"Partially done. {result.completed_steps}/{result.total_steps} "
              f"tasks completed ({rate:.0f}%). Some issues need attention.")
        vi = (f"Hoan thanh mot phan. {result.completed_steps}/{result.total_steps} "
              f"tac vu ({rate:.0f}%). Can xem lai mot so van de.")
    else:
        en = f"Failed. {result.failed_steps} tasks had problems. Please check errors."
        vi = f"That bai. {result.failed_steps} tac vu gap loi. Vui long kiem tra."

    return HumanSummary(en=en, vi=vi)


def scan_projects() -> list[ProjectInfo]:
    """Scan configured project paths for sub-projects."""
    from src.core.gateway.gateway_dash_router import GATEWAY_CONFIG
    projects: list[ProjectInfo] = []
    for base in GATEWAY_CONFIG.project_paths:
        base_dir = Path(base)
        if not base_dir.is_dir():
            continue
        for child in sorted(base_dir.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                projects.append(ProjectInfo(
                    name=child.name,
                    path=str(child),
                    has_git=(child / ".git").exists(),
                ))
    return projects


__all__ = [
    "build_human_summary",
    "require_swarm_token",
    "scan_projects",
    "verify_token",
]
