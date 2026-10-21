# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""FastAPI router for RaaS mission REST endpoints."""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.credits import CreditStore
from src.raas.mission_lifecycle import InsufficientCreditsError, MissionLifecycle
from src.raas.mission_models import CreateMissionRequest, MissionResponse
from src.raas.mission_store import MissionStore
from src.raas.missions_api_router_helpers import (
    _execute_mission_background,
    format_usage_summary_payload,
)
from src.raas.usage_analytics import UsageAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/raas", tags=["RaaS Missions"])

_mission_store = MissionStore()
_credit_store = CreditStore()
_analytics = UsageAnalytics()
_lifecycle = MissionLifecycle(
    mission_store=_mission_store,
    credit_store=_credit_store,
)


def _get_lifecycle() -> MissionLifecycle:
    return _lifecycle


def _get_analytics() -> UsageAnalytics:
    return _analytics


@router.post("/missions", response_model=MissionResponse, status_code=202)
async def submit_mission(
    body: CreateMissionRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    lifecycle: MissionLifecycle = Depends(_get_lifecycle),
) -> MissionResponse:
    """Submit a new mission; reserves credits atomically and runs in background."""
    try:
        record = lifecycle.submit(tenant_id=tenant.tenant_id, request=body)
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status_code=402,
            detail=str(exc),
            headers={"X-Upgrade-URL": "https://mekongmind.com/pricing"},
        ) from exc
    except Exception as exc:
        logger.exception("Mission submit error: %s", exc)
        raise HTTPException(status_code=500, detail="Mission submission failed") from exc

    background_tasks.add_task(
        _execute_mission_background,
        mission_id=record.id,
        tenant_id=tenant.tenant_id,
        goal=body.goal,
        lifecycle=lifecycle,
    )
    return MissionResponse.from_record(record)


@router.get("/missions", response_model=List[MissionResponse])
def list_missions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[MissionResponse]:
    """Return paginated mission list for the authenticated tenant."""
    records = _mission_store.list_for_tenant(
        tenant_id=tenant.tenant_id, limit=limit, offset=offset
    )
    return [MissionResponse.from_record(r) for r in records]


@router.get("/missions/{mission_id}", response_model=MissionResponse)
def get_mission(
    mission_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> MissionResponse:
    """Fetch a single mission by ID (tenant-scoped)."""
    record = _mission_store.get(mission_id, tenant.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return MissionResponse.from_record(record)


@router.get("/credits/balance")
def get_credit_balance(
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Return current credit balance for the authenticated tenant."""
    balance = _credit_store.get_balance(tenant.tenant_id)
    return {"tenant_id": tenant.tenant_id, "balance": balance}


@router.get("/credits/history")
def get_credit_history(
    limit: int = Query(default=50, ge=1, le=200),
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """Return recent credit transactions (newest first)."""
    history = _credit_store.get_history(tenant.tenant_id, limit=limit)
    return {
        "tenant_id": tenant.tenant_id,
        "transactions": [
            {
                "id": t.id,
                "amount": t.amount,
                "reason": t.reason,
                "timestamp": t.timestamp,
            }
            for t in history
        ],
    }


@router.get("/usage/summary")
def get_usage_summary(
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_context),
    analytics: UsageAnalytics = Depends(_get_analytics),
) -> dict:
    """Return aggregated usage for the last N days."""
    summary = analytics.get_tenant_summary(tenant.tenant_id, days=days)
    return format_usage_summary_payload(summary)


@router.get("/usage/activity")
def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    tenant: TenantContext = Depends(get_tenant_context),
    analytics: UsageAnalytics = Depends(_get_analytics),
) -> dict:
    """Return recent mission activity for the dashboard feed."""
    activity = analytics.get_recent_activity(tenant.tenant_id, limit=limit)
    return {"tenant_id": tenant.tenant_id, "activity": activity}


__all__ = [
    "router",
    "_mission_store",
    "_credit_store",
    "_analytics",
    "_lifecycle",
    "_get_lifecycle",
    "_get_analytics",
    "_execute_mission_background",
    "submit_mission",
    "list_missions",
    "get_mission",
    "get_credit_balance",
    "get_credit_history",
    "get_usage_summary",
    "get_recent_activity",
]
