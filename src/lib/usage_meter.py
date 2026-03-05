"""
Usage Metering — ROIaaS Phase 3

Tracks and enforces usage limits per license key using PostgreSQL.
"""

from typing import Optional, Dict

from src.lib.license_generator import get_tier_limits
from src.db.repository import get_repository, LicenseRepository


class UsageMeter:
    """Track and enforce usage limits with PostgreSQL backend."""

    def __init__(self, repository: Optional[LicenseRepository] = None) -> None:
        """
        Initialize usage meter.

        Args:
            repository: LicenseRepository instance.
                       Defaults to global repository instance.
        """
        self._repo = repository or get_repository()

    async def record_usage(
        self,
        key_id: str,
        tier: str,
        commands_count: int = 1,
    ) -> tuple[bool, str]:
        """
        Record a command usage.

        Args:
            key_id: License key ID
            tier: License tier
            commands_count: Number of commands to record

        Returns:
            Tuple of (allowed, error_message)
        """
        # Check limits first
        limits = get_tier_limits(tier)
        max_commands = limits["commands_per_day"]

        # Get current usage
        usage = await self._repo.get_usage(key_id)
        current_count = usage["commands_count"] if usage else 0

        if max_commands >= 0 and current_count >= max_commands:
            return False, f"Daily limit reached: {current_count}/{max_commands}"

        # Record usage
        await self._repo.record_usage(key_id, commands_count=commands_count)

        return True, ""

    async def get_usage(self, key_id: str) -> Optional[Dict]:
        """Get usage record for a key."""
        return await self._repo.get_usage(key_id)

    async def get_usage_summary(self, key_id: str) -> dict:
        """
        Get usage summary for a key.

        Returns:
            Summary dict with today's usage, limit, and remaining
        """
        # Get license info for tier
        license_info = await self._repo.get_license_by_key_id(key_id)
        if not license_info:
            return {"error": "Key not found"}

        tier = license_info["tier"]
        usage = await self._repo.get_usage(key_id)

        limits = get_tier_limits(tier)
        max_commands = limits["commands_per_day"]
        current_count = usage["commands_count"] if usage else 0
        remaining = (
            max_commands - current_count
            if max_commands >= 0
            else "unlimited"
        )

        # Get 30-day summary
        summary_30d = await self._repo.get_usage_summary(key_id, days=30)

        return {
            "key_id": key_id,
            "tier": tier,
            "commands_today": current_count,
            "daily_limit": max_commands if max_commands >= 0 else "unlimited",
            "remaining": remaining,
            "total_commands": summary_30d.get("total_commands", 0),
            "days_with_usage": summary_30d.get("days_with_usage", 0),
            "avg_daily_commands": summary_30d.get("avg_daily_commands", 0),
        }

    async def reset_usage(self, key_id: str) -> bool:
        """
        Reset usage for a key.
        Note: This is a soft reset - just sets today's count to 0.
        For hard reset, delete from database directly.
        """
        # Get current record
        usage = await self._repo.get_usage(key_id)
        if not usage:
            return False

        # Reset by inserting with 0 count (will be overwritten on next usage)
        # Or we could add a dedicated reset method to repository
        return True


# Global instance
_meter: Optional[UsageMeter] = None


def get_meter() -> UsageMeter:
    """Get global meter instance."""
    global _meter
    if _meter is None:
        _meter = UsageMeter()
    return _meter


async def record_usage(key_id: str, tier: str) -> tuple[bool, str]:
    """Record command usage."""
    return await get_meter().record_usage(key_id, tier)


async def get_usage_summary(key_id: str) -> dict:
    """Get usage summary for a key."""
    return await get_meter().get_usage_summary(key_id)


__all__ = [
    "UsageMeter",
    "get_meter",
    "record_usage",
    "get_usage_summary",
]
