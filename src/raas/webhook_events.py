"""Standard webhook event definitions for RaaS lifecycle.

Emits typed events for mission lifecycle, credit changes, and system alerts.
All events conform to a standard envelope for Polar.sh webhook delivery.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RaaSEventType(str, Enum):
    """Standard RaaS webhook event types."""

    MISSION_CREATED = "mission.created"
    MISSION_STARTED = "mission.started"
    MISSION_COMPLETED = "mission.completed"
    MISSION_FAILED = "mission.failed"
    MISSION_CANCELLED = "mission.cancelled"
    CREDITS_DEPLETED = "credits.depleted"
    CREDITS_LOW = "credits.low"
    CREDITS_PROVISIONED = "credits.provisioned"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"


@dataclass
class RaaSWebhookEvent:
    """Standard webhook event envelope.

    Attributes:
        event_type: Enum event type.
        tenant_id: Owning tenant.
        payload: Event-specific data dict.
        event_id: Unique event UUID (auto-generated).
        created_at: ISO-8601 UTC timestamp.
        retry_count: Delivery attempt count.
    """

    event_type: RaaSEventType
    tenant_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: _new_id())
    created_at: str = field(default_factory=lambda: _now_iso())
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-serializable dict."""
        return {
            "id": self.event_id,
            "type": self.event_type.value,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at,
            "retry_count": self.retry_count,
            "data": self.payload,
        }

    def sign(self, secret: str) -> str:
        """Return HMAC-SHA256 hex signature for the event body.

        Args:
            secret: Shared webhook signing secret.

        Returns:
            Hex-encoded HMAC-SHA256 signature.
        """
        body = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


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
            "upgrade_url": "https://polar.sh/mekong",
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _new_id() -> str:
    import uuid
    return str(uuid.uuid4())


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
