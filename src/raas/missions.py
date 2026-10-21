# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MissionService and FastAPI router for RaaS missions.

Storage layer lives in :mod:`src.raas.mission_store`.
Models live in :mod:`src.raas.mission_models`.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException  # noqa: F401

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.mission_models import (
    CreateMissionRequest,
    MissionComplexity,
    MissionRecord,
    MissionResponse,
    MissionStatus,
)
from src.raas.mission_store import MissionStore
from src.raas.missions_service import (
    _COMPLEXITY_THRESHOLDS,
    _SHELL_META,
    MissionService,
    _auto_detect_complexity,
    _sanitize_goal,
)

logger = logging.getLogger(__name__)

_service: Optional[MissionService] = None


def _get_service() -> MissionService:
    """Return (or lazily create) the module-level :class:`MissionService`."""
    global _service  # noqa: PLW0603
    if _service is None:
        from src.raas.credits import CreditStore

        _service = MissionService(
            mission_store=MissionStore(),
            credit_store=CreditStore(),
            tenant_tasks_dir=Path.home() / ".mekong" / "raas" / "tasks",
        )
    return _service


mission_router = APIRouter(tags=["missions"])


@mission_router.post("/missions", response_model=MissionResponse, status_code=201)
def create_mission(
    req: CreateMissionRequest, tenant: TenantContext = Depends(get_tenant_context)
) -> MissionResponse:
    """POST /missions — deduct credits, persist, dispatch; returns 201."""
    return _get_service().create_mission(tenant.tenant_id, tenant.tenant_name, req)


@mission_router.get("/missions", response_model=List[MissionResponse])
def list_missions(
    limit: int = 20, offset: int = 0, tenant: TenantContext = Depends(get_tenant_context)
) -> List[MissionResponse]:
    """GET /missions — paginated list for the authenticated tenant."""
    return _get_service().list_missions(tenant.tenant_id, limit=limit, offset=offset)


@mission_router.get("/missions/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str, tenant: TenantContext = Depends(get_tenant_context)
) -> MissionResponse:
    """GET /missions/{mission_id} — retrieve mission by ID (tenant-scoped)."""
    return _get_service().get_mission(tenant.tenant_id, mission_id)


@mission_router.get("/missions/{mission_id}/logs")
def get_mission_logs(
    mission_id: str, tenant: TenantContext = Depends(get_tenant_context)
) -> dict:
    """GET /missions/{mission_id}/logs — return execution log content."""
    return {"mission_id": mission_id, "logs": _get_service().get_logs(tenant.tenant_id, mission_id)}


@mission_router.post("/missions/{mission_id}/cancel", response_model=MissionResponse)
def cancel_mission(
    mission_id: str, tenant: TenantContext = Depends(get_tenant_context)
) -> MissionResponse:
    """POST /missions/{mission_id}/cancel — cancel queued mission and refund credits."""
    return _get_service().cancel_mission(tenant.tenant_id, mission_id)


__all__ = [
    "_SHELL_META",
    "_COMPLEXITY_THRESHOLDS",
    "_sanitize_goal",
    "_auto_detect_complexity",
    "MissionService",
    "_service",
    "_get_service",
    "mission_router",
    "create_mission",
    "list_missions",
    "get_mission",
    "get_mission_logs",
    "cancel_mission",
    "MissionComplexity",
    "MissionRecord",
    "MissionStatus",
]
