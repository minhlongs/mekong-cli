# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and tenant rate limit override operations for TierConfigRepository."""

import datetime
from dataclasses import dataclass
from typing import List, Optional

from src.db.database import DatabaseConnection


@dataclass
class TierConfig:
    """Tier configuration data class."""
    id: Optional[str]
    tier: str
    preset: str
    rate_limit: int
    window_seconds: int


@dataclass
class TenantRateLimitOverride:
    """Tenant rate limit override data class."""
    id: Optional[str]
    tenant_id: str
    tier: Optional[str]
    preset: str
    custom_limit: Optional[int]
    custom_window: int
    expires_at: Optional[str]

    def is_expired(self) -> bool:
        """Check if this override has expired."""
        if self.expires_at is None:
            return False

        try:
            expires_str = self.expires_at.replace("Z", "+00:00")
            expires_dt = datetime.datetime.fromisoformat(expires_str)
            now = datetime.datetime.now(datetime.timezone.utc)
            if expires_dt.tzinfo is None:
                expires_dt = expires_dt.replace(tzinfo=datetime.timezone.utc)
            return now > expires_dt
        except (ValueError, TypeError):
            return False


class TenantOverrideRepositoryMixin:
    """Mixin providing tenant rate limit override persistence methods."""

    _db: DatabaseConnection

    async def get_tenant_override(
        self,
        tenant_id: str,
        preset: str,
    ) -> Optional[TenantRateLimitOverride]:
        """Get tenant-specific rate limit override."""
        query = """
            SELECT id, tenant_id, tier, preset, custom_limit, custom_window, expires_at
            FROM tenant_rate_limits
            WHERE tenant_id = $1 AND preset = $2
        """
        result = await self._db.fetch_one(query, (tenant_id, preset.lower()))
        if not result:
            return None

        return TenantRateLimitOverride(
            id=str(result["id"]),
            tenant_id=result["tenant_id"],
            tier=result["tier"],
            preset=result["preset"],
            custom_limit=result["custom_limit"],
            custom_window=result["custom_window"],
            expires_at=result["expires_at"],
        )

    async def set_tenant_override(
        self,
        tenant_id: str,
        preset: str,
        custom_limit: int,
        custom_window: int = 60,
        tier: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> TenantRateLimitOverride:
        """Set or update tenant rate limit override."""
        query = """
            INSERT INTO tenant_rate_limits (
                tenant_id, tier, preset, custom_limit, custom_window, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (tenant_id, preset) DO UPDATE
            SET custom_limit = EXCLUDED.custom_limit,
                custom_window = EXCLUDED.custom_window,
                tier = EXCLUDED.tier,
                expires_at = EXCLUDED.expires_at
            RETURNING id, tenant_id, tier, preset, custom_limit, custom_window, expires_at
        """
        result = await self._db.fetch_one(
            query, (tenant_id, tier, preset.lower(), custom_limit, custom_window, expires_at)
        )
        return TenantRateLimitOverride(
            id=str(result["id"]),
            tenant_id=result["tenant_id"],
            tier=result["tier"],
            preset=result["preset"],
            custom_limit=result["custom_limit"],
            custom_window=result["custom_window"],
            expires_at=result["expires_at"],
        )

    async def delete_tenant_override(self, tenant_id: str, preset: str) -> bool:
        """Delete tenant rate limit override."""
        query = "DELETE FROM tenant_rate_limits WHERE tenant_id = $1 AND preset = $2"
        result = await self._db.execute(query, (tenant_id, preset.lower()))
        return result > 0

    async def get_all_tenant_overrides(
        self,
        tenant_id: Optional[str] = None,
    ) -> List[TenantRateLimitOverride]:
        """Get all tenant overrides, optionally filtered by tenant."""
        if tenant_id:
            query = """
                SELECT id, tenant_id, tier, preset, custom_limit, custom_window, expires_at
                FROM tenant_rate_limits
                WHERE tenant_id = $1
                ORDER BY preset
            """
            results = await self._db.fetch_all(query, (tenant_id,))
        else:
            query = """
                SELECT id, tenant_id, tier, preset, custom_limit, custom_window, expires_at
                FROM tenant_rate_limits
                ORDER BY tenant_id, preset
            """
            results = await self._db.fetch_all(query)

        return [
            TenantRateLimitOverride(
                id=str(row["id"]),
                tenant_id=row["tenant_id"],
                tier=row["tier"],
                preset=row["preset"],
                custom_limit=row["custom_limit"],
                custom_window=row["custom_window"],
                expires_at=row["expires_at"],
            )
            for row in results
        ]

    async def cleanup_expired_overrides(self) -> int:
        """Remove expired tenant overrides."""
        query = """
            DELETE FROM tenant_rate_limits
            WHERE expires_at IS NOT NULL AND expires_at < NOW()
        """
        return await self._db.execute(query)
