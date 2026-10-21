# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Open-Core 25-Step Public GitHub + SaaS Status & Deep Brainstorm API Routes."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

from src.core.opencore.opencore_25_step_deep_brainstorm_engine import (
    OpenCoreDeepBrainstormEngine,
)
from src.core.opencore.phase_560_opencore_saas_readiness_engine import (
    OpenCoreSaasReadinessEngine,
)

router = APIRouter(prefix="/api/open-core", tags=["Open-Core SaaS"])
_DEFAULT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_IDEA = (
    "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS"
)


def build_blueprint_audit(repo_root: Path) -> dict[str, Any]:
    """Delegate 25-step blueprint synchronization check to OpenCoreSaasReadinessEngine."""
    return OpenCoreSaasReadinessEngine.audit_blueprint(repo_root)


@router.get("/status")
async def get_open_core_status() -> dict[str, Any]:
    """Return 25-step Open-Core + SaaS readiness, filesystem hygiene, and blueprint sync."""
    readiness = OpenCoreSaasReadinessEngine.audit_repository(_DEFAULT_ROOT)
    hygiene = OpenCoreSaasReadinessEngine.verify_filesystem_hygiene(_DEFAULT_ROOT)
    return {
        "readiness": {
            "verdict": readiness.verdict.value,
            "completion_pct": readiness.completion_pct,
            "total_catalog_steps": readiness.total_catalog_steps,
            "safe_for_public_github_push": readiness.safe_for_public_github_push,
            "saas_paywall_active": readiness.saas_paywall_active,
            "rationale": readiness.rationale,
        },
        "hygiene": dataclasses.asdict(hygiene),
        "blueprint_audit": build_blueprint_audit(_DEFAULT_ROOT),
    }


@router.get("/brainstorm")
async def get_open_core_brainstorm(
    idea: str = Query(_DEFAULT_IDEA, description="Idea prompt for 25-step brainstorm"),
    deep: bool = Query(True, description="Include deep 25-step synthesis"),
) -> dict[str, Any]:
    """Return the bounded 4-field Brainstorm Contract, 3 options, and 25-step synthesis."""
    report = OpenCoreDeepBrainstormEngine.synthesize(
        idea_text=idea, repo_root=_DEFAULT_ROOT, deep=deep
    )
    return report.to_dict()
