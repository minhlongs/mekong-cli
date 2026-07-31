"""Shared license tier metadata and parser helpers."""

from __future__ import annotations

from typing import Any, Optional, cast

TIER_LIMITS = {
    "free": {"commands_per_day": 10, "max_days": None},
    "trial": {"commands_per_day": 50, "max_days": 7},
    "pro": {"commands_per_day": 1000, "max_days": None},
    "enterprise": {"commands_per_day": -1, "max_days": None},
}

VALID_LICENSE_TIERS = frozenset(TIER_LIMITS)


def get_tier_limits(tier: str) -> dict[str, Any]:
    """Get usage limits for a tier."""
    return cast(dict[str, Any], TIER_LIMITS.get(tier, TIER_LIMITS["free"]))


def parse_license_key(
    license_key: str,
) -> tuple[bool, Optional[dict], str]:
    """Parse license key to extract key_id and tier."""
    if not license_key:
        return False, None, "Empty license key"

    parts = license_key.split("-", 3)
    if len(parts) < 4:
        return False, None, "Invalid format: expected raas-{tier}-{id}-{signature}"
    if parts[0] != "raas":
        return False, None, "Invalid prefix: must start with 'raas-'"

    tier = parts[1]
    if tier not in VALID_LICENSE_TIERS:
        return False, None, f"Invalid tier: {tier}"

    return True, {"key_id": parts[2], "tier": tier}, ""


__all__ = ["TIER_LIMITS", "VALID_LICENSE_TIERS", "get_tier_limits", "parse_license_key"]
