# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Tier Configuration Repository — ROIaaS Phase 6

Repository layer for tier rate limiting configuration with database operations.
"""

from typing import Optional, Dict

from src.db.database import get_database, DatabaseConnection
from src.db.tier_tenant_overrides import (
    TierConfig,
    TenantRateLimitOverride,
    TenantOverrideRepositoryMixin,
)


class TierConfigRepository(TenantOverrideRepositoryMixin):
    """Repository for tier configuration operations."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()

    async def get_config(self, tier: str, preset: str) -> Optional[TierConfig]:
        """Get tier configuration from database."""
        query = """
            SELECT id, tier, preset, rate_limit, window_seconds
            FROM tier_configs
            WHERE tier = $1 AND preset = $2
        """
        result = await self._db.fetch_one(query, (tier.lower(), preset.lower()))

        if not result:
            return None

        return TierConfig(
            id=str(result["id"]),
            tier=result["tier"],
            preset=result["preset"],
            rate_limit=result["rate_limit"],
            window_seconds=result["window_seconds"],
        )

    async def update_config(
        self,
        tier: str,
        preset: str,
        rate_limit: int,
        window_seconds: Optional[int] = None,
    ) -> Optional[TierConfig]:
        """Update or insert tier configuration."""
        if window_seconds is None:
            window_seconds = 60

        query = """
            INSERT INTO tier_configs (tier, preset, rate_limit, window_seconds)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (tier, preset) DO UPDATE
            SET rate_limit = EXCLUDED.rate_limit,
                window_seconds = EXCLUDED.window_seconds,
                updated_at = NOW()
            RETURNING id, tier, preset, rate_limit, window_seconds
        """
        result = await self._db.fetch_one(
            query, (tier.lower(), preset.lower(), rate_limit, window_seconds)
        )

        if not result:
            return None

        return TierConfig(
            id=str(result["id"]),
            tier=result["tier"],
            preset=result["preset"],
            rate_limit=result["rate_limit"],
            window_seconds=result["window_seconds"],
        )

    async def get_all_configs(self) -> Dict[str, Dict[str, TierConfig]]:
        """Get all tier configurations."""
        query = """
            SELECT id, tier, preset, rate_limit, window_seconds
            FROM tier_configs
            ORDER BY tier, preset
        """
        results = await self._db.fetch_all(query)

        configs: Dict[str, Dict[str, TierConfig]] = {}

        for row in results:
            tier = row["tier"]
            preset = row["preset"]

            if tier not in configs:
                configs[tier] = {}

            configs[tier][preset] = TierConfig(
                id=str(row["id"]),
                tier=tier,
                preset=preset,
                rate_limit=row["rate_limit"],
                window_seconds=row["window_seconds"],
            )

        return configs

    async def delete_config(self, tier: str, preset: str) -> bool:
        """Delete a tier configuration."""
        query = "DELETE FROM tier_configs WHERE tier = $1 AND preset = $2"
        result = await self._db.execute(query, (tier.lower(), preset.lower()))
        return result > 0


_repository: Optional[TierConfigRepository] = None


def get_repository() -> TierConfigRepository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = TierConfigRepository()
    return _repository


async def init_repository() -> TierConfigRepository:
    """Initialize repository with database connection."""
    from src.db.database import init_database
    await init_database()
    return get_repository()


__all__ = [
    "TierConfig",
    "TenantRateLimitOverride",
    "TierConfigRepository",
    "get_repository",
    "init_repository",
]
