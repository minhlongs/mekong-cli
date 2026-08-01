"""Pydantic request/response models for the Gateway API.

Extracted from gateway.py to keep each module under 200 lines.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreateMissionRequest(BaseModel):
    """Request body for POST /v1/missions."""

    goal: str = Field(..., description="Natural language goal")
    tenant_id: str = Field(..., description="AgencyOS tenant ID")
    webhook_url: Optional[str] = Field(None, description="Callback URL for results")
    priority: str = Field("normal", description="low|normal|high")
    metadata: dict = Field(default_factory=dict)


class CreateMissionResponse(BaseModel):
    """Response body for POST /v1/missions."""

    mission_id: str
    status: str
    created_at: str
    estimated_steps: int = 0
    stream_url: str


class MissionStatusResponse(BaseModel):
    """Response body for GET /v1/missions/{id}."""

    mission_id: str
    status: str
    goal: str
    tenant_id: str
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    steps_total: int = 0
    steps_completed: int = 0


class TestWebhookRequest(BaseModel):
    """Request body for POST /v1/webhook/test."""

    webhook_url: str = Field(..., description="Webhook URL to test")
    tenant_id: Optional[str] = Field(None, description="Optional tenant context")


class TestWebhookResponse(BaseModel):
    """Response body for POST /v1/webhook/test."""

    success: bool
    message: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None


class MCUDeductRequest(BaseModel):
    """Request body for POST /v1/mcu/deduct."""

    tenant_id: str = Field(..., description="Tenant identifier")
    complexity: str = Field("simple", description="simple|standard|complex")
    mission_id: str = Field("", description="Associated mission ID")
    idempotency_key: Optional[str] = Field(None, description="Client-supplied idempotency key")


class MCUDeductResponse(BaseModel):
    """Response body for POST /v1/mcu/deduct."""

    success: bool
    balance_before: int
    balance_after: int
    amount_deducted: int
    low_balance: bool = False
    error: str = ""
