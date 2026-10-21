# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Standard webhook event types and envelope model for RaaS lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from typing import Any, Dict
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    """Standard webhook event envelope."""

    event_type: RaaSEventType
    tenant_id: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now_iso)
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
        """Return HMAC-SHA256 hex signature for the event body."""
        body = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
