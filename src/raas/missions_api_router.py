"""FastAPI router for RaaS mission REST endpoints.

Endpoints:
    POST   /raas/missions            - Submit mission (reserves credits + executes)
    GET    /raas/missions            - List missions for tenant (paginated)
    GET    /raas/missions/{id}       - Get mission by ID
    GET    /raas/credits/balance     - Current credit balance
    GET    /raas/credits/history     - Transaction history
    GET    /raas/usage/summary       - Usage analytics (last 30 days)
    GET    /raas/usage/activity      - Recent activity feed
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.credits import CreditStore
from src.raas.mission_lifecycle import InsufficientCreditsError, MissionLifecycle
from src.raas.mission_models import (
    CreateMissionRequest,
    MissionResponse,
)
from src.raas.mission_store import MissionStore
from src.raas.usage_analytics import UsageAnalytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/raas", tags=["RaaS Missions"])

# ---------------------------------------------------------------------------
# Dependency factories (singletons via module-level instances)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Mission endpoints
# ---------------------------------------------------------------------------


@router.post("/missions", response_model=MissionResponse, status_code=202)
async def submit_mission(
    body: CreateMissionRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    lifecycle: MissionLifecycle = Depends(_get_lifecycle),
) -> MissionResponse:
    """Submit a new mission.  Credits are reserved atomically before queuing.

    After queuing, launches background LLM execution via hybrid router.
    Returns HTTP 402 when the tenant has insufficient credits.
    """
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

    # Launch background execution — mission transitions queued → running → completed
    background_tasks.add_task(
        _execute_mission_background,
        mission_id=record.id,
        tenant_id=tenant.tenant_id,
        goal=body.goal,
        lifecycle=lifecycle,
    )

    return MissionResponse.from_record(record)


async def _execute_mission_background(
    mission_id: str,
    tenant_id: str,
    goal: str,
    lifecycle: MissionLifecycle,
) -> None:
    """Background task: execute mission via hybrid LLM router."""
    import time

    try:
        from src.core.hybrid_router import route_and_execute

        lifecycle.start(mission_id, tenant_id)
        logger.info("Mission %s executing via hybrid router", mission_id)

        start_time = time.monotonic()
        # Credits already deducted by MissionLifecycle.submit()
        # Pass a pre-approved MCU gate so hybrid router skips double-billing
        from src.core.mcu_gate import MCUGate
        pre_approved_gate = MCUGate(":memory:")
        pre_approved_gate.seed_balance(tenant_id, 9999, reason="raas_pre_approved")

        result = await route_and_execute(
            goal=goal,
            tenant_id=tenant_id,
            mission_id=mission_id,
            mcu_gate=pre_approved_gate,
        )
        duration = time.monotonic() - start_time

        if result.success:
            lifecycle.complete(mission_id, tenant_id, duration_seconds=duration)
            logger.info("Mission %s completed in %.1fs", mission_id, duration)
        else:
            lifecycle.fail(
                mission_id, tenant_id,
                reason=result.error or "Execution failed",
                refund=True,
            )
            logger.warning("Mission %s failed: %s", mission_id, result.error)

    except Exception as exc:
        logger.exception("Mission %s crashed: %s", mission_id, exc)
        lifecycle.fail(
            mission_id, tenant_id,
            reason=str(exc)[:500],
            refund=True,
        )


@router.get("/missions", response_model=List[MissionResponse])
def list_missions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[MissionResponse]:
    """Return paginated mission list for the authenticated tenant."""
    records = _mission_store.list_for_tenant(
        tenant_id=tenant.tenant_id,
        limit=limit,
        offset=offset,
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


# ---------------------------------------------------------------------------
# Credit endpoints
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Usage / analytics endpoints
# ---------------------------------------------------------------------------


@router.get("/usage/summary")
def get_usage_summary(
    days: int = Query(default=30, ge=1, le=365),
    tenant: TenantContext = Depends(get_tenant_context),
    analytics: UsageAnalytics = Depends(_get_analytics),
) -> dict:
    """Return aggregated usage for the last N days."""
    summary = analytics.get_tenant_summary(tenant.tenant_id, days=days)
    return {
        "tenant_id": summary.tenant_id,
        "period_start": summary.period_start,
        "period_end": summary.period_end,
        "total_credits_used": summary.total_credits_used,
        "total_missions": summary.total_missions,
        "missions_completed": summary.missions_completed,
        "missions_failed": summary.missions_failed,
        "complexity_breakdown": summary.complexity_breakdown,
        "daily_breakdown": [
            {
                "date": d.date,
                "credits_used": d.credits_used,
                "missions_count": d.missions_count,
                "missions_completed": d.missions_completed,
                "missions_failed": d.missions_failed,
            }
            for d in summary.daily_breakdown
        ],
    }


@router.get("/usage/activity")
def get_recent_activity(
    limit: int = Query(default=10, ge=1, le=50),
    tenant: TenantContext = Depends(get_tenant_context),
    analytics: UsageAnalytics = Depends(_get_analytics),
) -> dict:
    """Return recent mission activity for the dashboard feed."""
    activity = analytics.get_recent_activity(tenant.tenant_id, limit=limit)
    return {"tenant_id": tenant.tenant_id, "activity": activity}
