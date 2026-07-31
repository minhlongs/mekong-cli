"""Engine License Gate Middleware — bridges LicenseEnforcer into the gateway middleware chain.

Calls LicenseEnforcer.require_tier for configured minimum tiers on incoming requests.
Skips health/admin endpoints.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Request

from .license_enforcer import LicenseEnforcer, Tier
from .license_store import get_license_store

logger = logging.getLogger(__name__)

_EXEMPT_PATHS = {"/health", "/api-docs", "/api-redoc", "/openapi.json", "/favicon.ico"}
_MINIMUM_TIER_ENV = "MEKONG_MINIMUM_TIER"


class EngineLicenseGateMiddleware:
    """Gate every request by minimum configured tier."""

    def __init__(self, app, minimum_tier: Optional[Tier] = None) -> None:
        self.app = app
        self.minimum_tier = minimum_tier or self._tier_from_env()
        self._enforcer = LicenseEnforcer()

    @staticmethod
    def _tier_from_env() -> Tier:
        raw = os.environ.get(_MINIMUM_TIER_ENV, "FREE").upper()
        try:
            return Tier[raw]
        except KeyError:
            return Tier.FREE

    async def __call__(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT_PATHS):
            return await call_next(request)

        user_id = request.headers.get("X-User-Id") or request.query_params.get("user_id")
        try:
            self._enforcer.require_tier(self.minimum_tier, user_id)
        except Exception as exc:
            logger.warning("License gate blocked %s: %s", path, exc)
            raise
        return await call_next(request)
