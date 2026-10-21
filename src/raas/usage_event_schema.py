# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Usage Event Schema - Phase 5 Analytics Dashboard Compatible

Defines Pydantic schemas for usage events sent to RaaS Gateway.
Compatible with Phase 5 Analytics Dashboard event schemas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, field_validator

from src.raas.usage_event_payloads import (
    EncryptedPayload,
    EntitlementResponse,
    SyncRequest,
    UsageSummary,
    WebhookEvent,
)


class UsageEventType(str, Enum):
    """Supported usage event types."""

    CLI_COMMAND = "cli:command"
    AGENT_SPAWN = "agent:spawn"
    LLM_CALL = "llm:call"
    USAGE_TOKENS = "usage:tokens"
    SYNC_METRICS = "sync:metrics"


class UsageEvent(BaseModel):
    """Single usage event record."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: UsageEventType
    tenant_id: str
    license_key: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    endpoint: Optional[str] = None
    model: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp", mode="before")
    @classmethod
    def ensure_utc(cls, v):
        """Ensure timestamp is UTC."""
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "tenant_id": self.tenant_id,
            "license_key": self.license_key,
            "timestamp": self.timestamp.isoformat(),
            "endpoint": self.endpoint,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


class HourlyBucket(BaseModel):
    """Aggregated usage metrics for one hour bucket."""

    hour_bucket: str  # YYYY-MM-DD-HH
    tenant_id: str
    event_count: int = 0
    total_tokens: int = 0
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    total_duration_ms: float = 0.0
    unique_endpoints: int = 0

    @classmethod
    def from_events(cls, events: List[UsageEvent]) -> "HourlyBucket":
        """Build hourly bucket from list of events."""
        if not events:
            return cls(hour_bucket="", tenant_id="")

        first_event = events[0]
        hour_bucket = first_event.timestamp.strftime("%Y-%m-%d-%H")
        tenant_id = first_event.tenant_id

        events_by_type: Dict[str, int] = {}
        total_tokens = 0
        total_duration = 0.0
        endpoints = set()

        for event in events:
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
            total_tokens += event.input_tokens + event.output_tokens
            total_duration += event.duration_ms
            if event.endpoint:
                endpoints.add(event.endpoint)

        return cls(
            hour_bucket=hour_bucket,
            tenant_id=tenant_id,
            event_count=len(events),
            total_tokens=total_tokens,
            events_by_type=events_by_type,
            total_duration_ms=total_duration,
            unique_endpoints=len(endpoints),
        )


__all__ = [
    "UsageEventType",
    "UsageEvent",
    "HourlyBucket",
    "UsageSummary",
    "EncryptedPayload",
    "SyncRequest",
    "EntitlementResponse",
    "WebhookEvent",
]
