# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tier configuration and tenant override endpoint handlers."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from src.api.tier_config_models import (
    VALID_PRESETS,
    CreateTenantOverrideRequest,
    TenantOverrideListResponse,
    TenantOverrideResponse,
    TierConfigResponse,
    TierConfigsListResponse,
    UpdateTierConfigRequest,
)
from src.auth.rbac import Role, require_role, status

handlers_router = APIRouter()


def _to_tier_resp(cfg) -> TierConfigResponse:
    return TierConfigResponse(
        id=cfg.id, tier=cfg.tier, preset=cfg.preset, rate_limit=cfg.rate_limit, window_seconds=cfg.window_seconds
    )


def _to_override_resp(o) -> TenantOverrideResponse:
    return TenantOverrideResponse(
        id=o.id, tenant_id=o.tenant_id, tier=o.tier, preset=o.preset,
        custom_limit=o.custom_limit, custom_window=o.custom_window, expires_at=o.expires_at,
    )


def _validate_preset(preset: str) -> str:
    if preset.lower() not in VALID_PRESETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid preset '{preset}'. Valid presets: {VALID_PRESETS}"
        )
    return preset.lower()


@handlers_router.get("/tier-configs", response_model=TierConfigsListResponse)
async def list_tier_configs(_admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))) -> TierConfigsListResponse:
    """List all tier rate limit configurations."""
    from src.db.tier_config_repository import get_repository

    configs = await get_repository().get_all_configs()
    result = {
        tier_name: {preset_name: _to_tier_resp(cfg) for preset_name, cfg in presets.items()}
        for tier_name, presets in configs.items()
    }
    return TierConfigsListResponse(configs=result)


@handlers_router.get("/tier-configs/{tier}", response_model=List[TierConfigResponse])
async def get_tier_config(
    tier: str, _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))
) -> List[TierConfigResponse]:
    """Get all configurations for a specific tier."""
    from src.db.tier_config_repository import get_repository

    repo = get_repository()
    configs = []
    for preset in VALID_PRESETS:
        cfg = await repo.get_config(tier.lower(), preset)
        if cfg:
            configs.append(_to_tier_resp(cfg))

    if not configs:
        from engine.billing.tier_config import get_tier_config as get_default_config

        try:
            default = get_default_config(tier)
            return [
                TierConfigResponse(
                    id=None, tier=tier, preset=p, rate_limit=getattr(default, p).requests_per_minute, window_seconds=60
                )
                for p in VALID_PRESETS
            ]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tier '{tier}' not found. Valid tiers: free, trial, pro, enterprise",
            )
    return configs


@handlers_router.put("/tier-configs/{tier}/{preset}", response_model=TierConfigResponse)
async def update_tier_config(
    tier: str,
    preset: str,
    request: UpdateTierConfigRequest,
    _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER)),
) -> TierConfigResponse:
    """Update rate limit configuration for a tier preset."""
    from engine.billing.tier_config import Tier
    from src.db.tier_config_repository import get_repository
    from src.lib.rate_limiter_factory import invalidate_cache

    valid_tiers = [t.value for t in Tier]
    if tier.lower() not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid tier '{tier}'. Valid tiers: {valid_tiers}"
        )
    preset_lower = _validate_preset(preset)
    config = await get_repository().update_config(
        tier=tier.lower(), preset=preset_lower, rate_limit=request.rate_limit, window_seconds=request.window_seconds
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update configuration"
        )
    invalidate_cache(tier.lower())
    return _to_tier_resp(config)


@handlers_router.get("/tenant-overrides", response_model=TenantOverrideListResponse)
async def list_tenant_overrides(
    tenant_id: Optional[str] = None, _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))
) -> TenantOverrideListResponse:
    """List all tenant rate limit overrides."""
    from src.db.tier_config_repository import get_repository

    overrides = await get_repository().get_all_tenant_overrides(tenant_id)
    return TenantOverrideListResponse(overrides=[_to_override_resp(o) for o in overrides])


@handlers_router.get("/tenant-overrides/{tenant_id}", response_model=TenantOverrideListResponse)
async def get_tenant_overrides(
    tenant_id: str, _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))
) -> TenantOverrideListResponse:
    """Get all overrides for a specific tenant."""
    from src.db.tier_config_repository import get_repository

    overrides = await get_repository().get_all_tenant_overrides(tenant_id)
    return TenantOverrideListResponse(overrides=[_to_override_resp(o) for o in overrides])


@handlers_router.post(
    "/tenant-overrides", response_model=TenantOverrideResponse, status_code=status.HTTP_201_CREATED
)
async def create_tenant_override(
    request: CreateTenantOverrideRequest, _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))
) -> TenantOverrideResponse:
    """Create a new tenant rate limit override."""
    from src.db.tier_config_repository import get_repository

    preset_lower = _validate_preset(request.preset)
    try:
        override = await get_repository().set_tenant_override(
            tenant_id=request.tenant_id if hasattr(request, "tenant_id") else "default",
            preset=preset_lower, custom_limit=request.custom_limit, custom_window=request.custom_window,
            tier=request.tier.lower() if request.tier else None, expires_at=request.expires_at,
        )
        return _to_override_resp(override)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@handlers_router.delete(
    "/tenant-overrides/{tenant_id}/{preset}",
    status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None,
)
async def delete_tenant_override(
    tenant_id: str, preset: str, _admin: None = Depends(require_role(Role.ADMIN, Role.OWNER))
) -> None:
    """Remove a tenant rate limit override."""
    from src.db.tier_config_repository import get_repository

    deleted = await get_repository().delete_tenant_override(tenant_id, _validate_preset(preset))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No override found for tenant '{tenant_id}' and preset '{preset}'",
        )
