# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sync, entitlement, and webhook payload models for RaaS Usage Event Schema."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class UsageSummary(BaseModel):
    """Summary of usage metrics for sync."""

    total_requests: int = 0
    total_payload_size: int = 0
    hours_active: int = 0
    peak_hour: Optional[str] = None
    peak_requests: int = 0
    first_request: Optional[datetime] = None
    last_request: Optional[datetime] = None


class EncryptedPayload(BaseModel):
    """Encrypted usage payload for secure transmission."""

    nonce: str
    ciphertext: str
    version: str = "v1"

    @classmethod
    def from_bytes(cls, nonce: bytes, ciphertext: bytes) -> "EncryptedPayload":
        """Create from raw bytes."""
        return cls(
            nonce=base64.b64encode(nonce).decode("ascii"),
            ciphertext=base64.b64encode(ciphertext).decode("ascii"),
        )

    def to_bytes(self) -> tuple[bytes, bytes]:
        """Convert back to raw bytes."""
        return (
            base64.b64decode(self.nonce),
            base64.b64decode(self.ciphertext),
        )


class SyncRequest(BaseModel):
    """Request payload for /v1/usage/sync endpoint."""

    license_key: str
    tenant_id: str
    encrypted_payload: EncryptedPayload
    summary: UsageSummary
    checksum: str
    synced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EntitlementResponse(BaseModel):
    """Response from /v1/license/entitlements endpoint."""

    tenant_id: str
    tier: str
    features: List[str] = Field(default_factory=list)
    rate_limit: int = 60
    rate_limit_window: int = 60
    max_payload_size: int = 1048576  # 1MB
    retention_days: int = 30
    expires_at: Optional[datetime] = None


class WebhookEvent(BaseModel):
    """Webhook event for Stripe/Polar integration."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "stripe" or "polar"
    tenant_id: str
    usage_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_stripe_format(self) -> Dict[str, Any]:
        """Convert to Stripe Usage Record format."""
        return {
            "type": "usage_record.create",
            "object": "billing.usage_record",
            "data": {
                "subscription_item": self.usage_data.get("subscription_item_id"),
                "quantity": self.usage_data.get("total_tokens", 0),
                "timestamp": int(self.created_at.timestamp()),
                "action": "set",
            },
        }

    def to_polar_format(self) -> Dict[str, Any]:
        """Convert to Polar Webhook format."""
        return {
            "type": "benefit.usage.reported",
            "object": "benefit_usage",
            "data": {
                "benefit_id": self.usage_data.get("benefit_id"),
                "customer_id": self.tenant_id,
                "used": self.usage_data.get("total_tokens", 0),
                "unit": "tokens",
                "reported_at": self.created_at.isoformat(),
            },
        }
