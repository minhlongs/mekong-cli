# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Background execution and payload serialisers for RaaS mission REST endpoints."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from src.raas.mission_lifecycle import MissionLifecycle
from src.raas.usage_analytics import TenantUsageSummary

logger = logging.getLogger(__name__)


async def _execute_mission_background(
    mission_id: str,
    tenant_id: str,
    goal: str,
    lifecycle: MissionLifecycle,
) -> None:
    """Background task: execute mission via hybrid LLM router."""
    try:
        from src.core.hybrid_router import route_and_execute
        from src.core.mcu_gate import MCUGate

        lifecycle.start(mission_id, tenant_id)
        logger.info("Mission %s executing via hybrid router", mission_id)

        start_time = time.monotonic()
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
                mission_id,
                tenant_id,
                reason=result.error or "Execution failed",
                refund=True,
            )
            logger.warning("Mission %s failed: %s", mission_id, result.error)

    except Exception as exc:
        logger.exception("Mission %s crashed: %s", mission_id, exc)
        lifecycle.fail(
            mission_id,
            tenant_id,
            reason=str(exc)[:500],
            refund=True,
        )


def format_usage_summary_payload(summary: TenantUsageSummary) -> Dict[str, Any]:
    """Serialize TenantUsageSummary into the REST JSON dictionary."""
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
