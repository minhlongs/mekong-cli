# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Request and response Pydantic models for Tier Config API Routes."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

VALID_PRESETS = ["auth_login", "auth_callback", "auth_refresh", "api_default"]


class RateLimitConfigResponse(BaseModel):
    """Rate limit configuration response."""

    preset: str
    rate_limit: int = Field(..., description="Requests per window")
    window_seconds: int = Field(..., description="Window size in seconds")
    burst_size: Optional[int] = Field(None, description="Token bucket burst size")


class TierConfigResponse(BaseModel):
    """Tier configuration response."""

    id: Optional[str]
    tier: str
    preset: str
    rate_limit: int
    window_seconds: int


class TierConfigsListResponse(BaseModel):
    """List of all tier configurations."""

    configs: dict[str, dict[str, TierConfigResponse]]


class UpdateTierConfigRequest(BaseModel):
    """Request to update tier configuration."""

    rate_limit: int = Field(..., gt=0, description="New rate limit (requests per window)")
    window_seconds: int = Field(60, gt=0, description="Window size in seconds")


class TenantOverrideResponse(BaseModel):
    """Tenant rate limit override response."""

    id: Optional[str]
    tenant_id: str
    tier: Optional[str]
    preset: str
    custom_limit: Optional[int]
    custom_window: int
    expires_at: Optional[str]


class TenantOverrideListResponse(BaseModel):
    """List of tenant overrides."""

    overrides: List[TenantOverrideResponse]


class CreateTenantOverrideRequest(BaseModel):
    """Request to create tenant override."""

    preset: str = Field(..., description="Preset name")
    custom_limit: int = Field(..., gt=0, description="Custom rate limit")
    custom_window: int = Field(60, gt=0, description="Custom window in seconds")
    tier: Optional[str] = Field(None, description="Optional tier override")
    expires_at: Optional[str] = Field(None, description="Optional expiration timestamp")


__all__ = [
    "CreateTenantOverrideRequest",
    "RateLimitConfigResponse",
    "TenantOverrideListResponse",
    "TenantOverrideResponse",
    "TierConfigResponse",
    "TierConfigsListResponse",
    "UpdateTierConfigRequest",
    "VALID_PRESETS",
]
