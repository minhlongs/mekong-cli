# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License Enforcement Service — ROIaaS Phase 8.

Service for validating license status with caching and tier comparison.
Used by middleware to block requests from suspended/revoked licenses.
"""
from __future__ import annotations

import logging
import time
from typing import Dict, Optional, Tuple

from src.db.database import DatabaseConnection, get_database
from src.services.license_enforcement_models import (
    TIER_HIERARCHY,
    LicenseInfo,
    LicenseStatus,
    check_tier_sufficiency,
    determine_license_status,
)

logger = logging.getLogger("mekong.license_enforcement")


class LicenseEnforcementService:
    """Service for license enforcement with 5-minute TTL caching."""

    CACHE_TTL = 300
    TIER_HIERARCHY = TIER_HIERARCHY

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()
        self._cache: Dict[str, Tuple[LicenseInfo, float]] = {}

    def _cache_get(self, key: str) -> Optional[LicenseInfo]:
        """Get license info from cache if not expired."""
        if key not in self._cache:
            return None
        license_info, cached_at = self._cache[key]
        if time.time() - cached_at > self.CACHE_TTL:
            del self._cache[key]
            return None
        return license_info

    def _cache_set(self, key: str, license_info: LicenseInfo) -> None:
        """Set license info in cache with current timestamp."""
        self._cache[key] = (license_info, time.time())

    def _cache_invalidate(self, key: str) -> None:
        """Invalidate cached license info."""
        if key in self._cache:
            del self._cache[key]

    async def _check_license_in_db(self, license_key: str) -> Optional[LicenseInfo]:
        """Check license status in database."""
        try:
            key_id = license_key
            if license_key.startswith("raasjwt-"):
                from engine.license.jwt_license_generator import validate_jwt_license

                is_valid, payload, _ = validate_jwt_license(license_key)
                if is_valid and payload:
                    key_id = payload.get("key_id", license_key)

            query = """
                SELECT id, key_id, tier, status, email, expires_at, created_at, updated_at
                FROM raas_license_keys
                WHERE key_id = $1 OR license_key = $2
                LIMIT 1
            """
            result = await self._db.fetch_one(query, (key_id, license_key))
            if not result:
                return None

            return LicenseInfo(
                key_id=str(result["id"]),
                tier=result["tier"],
                status=result["status"],
                email=result.get("email"),
                expires_at=result.get("expires_at"),
                created_at=result.get("created_at"),
                updated_at=result.get("updated_at"),
            )
        except Exception as e:
            logger.error(
                "license_enforcement.db_check_error: %s (key=%s)",
                str(e),
                license_key[:8] + "..." if len(license_key) > 8 else license_key,
            )
            return None

    async def check_license_status(self, license_key: str) -> LicenseStatus:
        """Check license status with caching and JWT fallback."""
        cached_info = self._cache_get(license_key)
        if cached_info:
            return self._determine_status(cached_info)

        license_info = await self._check_license_in_db(license_key)
        if not license_info:
            if license_key.startswith("raasjwt-"):
                from engine.license.jwt_license_generator import validate_jwt_license

                is_valid, payload, _ = validate_jwt_license(license_key)
                if is_valid and payload:
                    license_info = LicenseInfo(
                        key_id=payload.get("jti", "unknown"),
                        tier=payload.get("tier", "free"),
                        status="active",
                        email=payload.get("email"),
                    )
                else:
                    return LicenseStatus.INVALID
            else:
                return LicenseStatus.INVALID

        self._cache_set(license_key, license_info)
        return self._determine_status(license_info)

    def _determine_status(self, license_info: LicenseInfo) -> LicenseStatus:
        """Determine license status from license info."""
        return determine_license_status(license_info)

    def is_tier_sufficient(self, current_tier: str, required_tier: str) -> bool:
        """Check if current tier meets or exceeds required tier."""
        return check_tier_sufficiency(current_tier, required_tier, self.TIER_HIERARCHY)

    async def get_license_info(self, license_key: str) -> Optional[LicenseInfo]:
        """Get full license information."""
        cached_info = self._cache_get(license_key)
        if cached_info:
            return cached_info
        license_info = await self._check_license_in_db(license_key)
        if license_info:
            self._cache_set(license_key, license_info)
        return license_info

    def clear_cache(self) -> None:
        """Clear all cached license statuses."""
        self._cache.clear()
        logger.info("license_enforcement.cache_cleared", message="License cache cleared")


_license_enforcement_service: Optional[LicenseEnforcementService] = None


def get_license_enforcement() -> LicenseEnforcementService:
    """Get global license enforcement service instance."""
    global _license_enforcement_service
    if _license_enforcement_service is None:
        _license_enforcement_service = LicenseEnforcementService()
    return _license_enforcement_service


async def check_license_status(license_key: str) -> LicenseStatus:
    """Check license status using global service."""
    return await get_license_enforcement().check_license_status(license_key)


def is_tier_sufficient(current_tier: str, required_tier: str) -> bool:
    """Check if current tier meets required tier."""
    return get_license_enforcement().is_tier_sufficient(current_tier, required_tier)


__all__ = [
    "LicenseStatus",
    "LicenseInfo",
    "LicenseEnforcementService",
    "get_license_enforcement",
    "check_license_status",
    "is_tier_sufficient",
]
