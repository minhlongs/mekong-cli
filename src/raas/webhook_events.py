# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Standard webhook event definitions for RaaS lifecycle.

Emits typed events for mission lifecycle, credit changes, and system alerts.
All events conform to a standard envelope for Polar.sh webhook delivery.
"""
from __future__ import annotations

import logging

from src.raas.webhook_events_models import (
    RaaSEventType,
    RaaSWebhookEvent,
    _new_id,
    _now_iso,
)

logger = logging.getLogger(__name__)


def mission_created_event(
    tenant_id: str,
    mission_id: str,
    goal: str,
    complexity: str,
    credits_cost: int,
) -> RaaSWebhookEvent:
    """Build a mission.created event."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.MISSION_CREATED,
        tenant_id=tenant_id,
        payload={
            "mission_id": mission_id,
            "goal": goal,
            "complexity": complexity,
            "credits_cost": credits_cost,
        },
    )


def mission_completed_event(
    tenant_id: str,
    mission_id: str,
    credits_billed: int,
    duration_seconds: float,
) -> RaaSWebhookEvent:
    """Build a mission.completed event."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.MISSION_COMPLETED,
        tenant_id=tenant_id,
        payload={
            "mission_id": mission_id,
            "credits_billed": credits_billed,
            "duration_seconds": duration_seconds,
        },
    )


def mission_failed_event(
    tenant_id: str,
    mission_id: str,
    reason: str,
) -> RaaSWebhookEvent:
    """Build a mission.failed event."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.MISSION_FAILED,
        tenant_id=tenant_id,
        payload={"mission_id": mission_id, "reason": reason},
    )


def credits_depleted_event(
    tenant_id: str,
    balance: int,
    plan: str,
) -> RaaSWebhookEvent:
    """Build a credits.depleted event."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.CREDITS_DEPLETED,
        tenant_id=tenant_id,
        payload={
            "balance": balance,
            "plan": plan,
            "upgrade_url": "https://mekongmind.com/pricing",
        },
    )


def credits_low_event(
    tenant_id: str,
    balance: int,
    limit: int,
) -> RaaSWebhookEvent:
    """Build a credits.low event (triggered at <10% remaining)."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.CREDITS_LOW,
        tenant_id=tenant_id,
        payload={
            "balance": balance,
            "limit": limit,
            "percent_remaining": round((balance / limit) * 100, 1) if limit > 0 else 0,
        },
    )


def credits_provisioned_event(
    tenant_id: str,
    amount: int,
    new_balance: int,
    source: str,
) -> RaaSWebhookEvent:
    """Build a credits.provisioned event after Polar purchase."""
    return RaaSWebhookEvent(
        event_type=RaaSEventType.CREDITS_PROVISIONED,
        tenant_id=tenant_id,
        payload={
            "amount_added": amount,
            "new_balance": new_balance,
            "source": source,
        },
    )


__all__ = [
    "RaaSEventType",
    "RaaSWebhookEvent",
    "mission_created_event",
    "mission_completed_event",
    "mission_failed_event",
    "credits_depleted_event",
    "credits_low_event",
    "credits_provisioned_event",
    "_new_id",
    "_now_iso",
]
