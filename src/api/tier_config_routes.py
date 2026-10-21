# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Tier Config API Routes — ROIaaS Phase 6

RESTful API endpoints for managing tier rate limit configurations and tenant overrides.
"""

from fastapi import APIRouter

from src.api.tier_config_handlers import (  # noqa: F401
    create_tenant_override,
    delete_tenant_override,
    get_tenant_overrides,
    get_tier_config,
    handlers_router,
    list_tenant_overrides,
    list_tier_configs,
    update_tier_config,
)
from src.api.tier_config_models import (  # noqa: F401
    VALID_PRESETS,
    CreateTenantOverrideRequest,
    RateLimitConfigResponse,
    TenantOverrideListResponse,
    TenantOverrideResponse,
    TierConfigResponse,
    TierConfigsListResponse,
    UpdateTierConfigRequest,
)
from src.auth.rbac import Role, require_role, status  # noqa: F401

router = APIRouter(prefix="/api", tags=["Tier Configuration"])
router.include_router(handlers_router)

__all__ = ["router"]
