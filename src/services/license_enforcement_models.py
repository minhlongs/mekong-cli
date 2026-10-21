# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License enforcement models, status enum, and tier comparison helpers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

TIER_HIERARCHY: list[str] = ["free", "trial", "pro", "enterprise"]


class LicenseStatus(str, Enum):
    """License status enumeration."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"
    INVALID = "invalid"
    INSUFFICIENT_TIER = "insufficient_tier"


@dataclass
class LicenseInfo:
    """License information data class."""

    key_id: str
    tier: str
    status: str
    email: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def determine_license_status(license_info: LicenseInfo) -> LicenseStatus:
    """Determine license status from license info."""
    status = license_info.status.lower() if license_info.status else "active"

    if status == "suspended":
        return LicenseStatus.SUSPENDED
    if status == "revoked":
        return LicenseStatus.REVOKED

    if license_info.expires_at:
        now = datetime.now(timezone.utc)
        expires_at = license_info.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            return LicenseStatus.EXPIRED

    return LicenseStatus.ACTIVE


def check_tier_sufficiency(
    current_tier: str,
    required_tier: str,
    hierarchy: list[str] | None = None,
) -> bool:
    """Check if current tier meets or exceeds required tier."""
    tiers = hierarchy if hierarchy is not None else TIER_HIERARCHY
    curr = current_tier.lower()
    req = required_tier.lower()

    if " (" in curr:
        curr = curr.split(" (")[0].strip()

    try:
        current_index = tiers.index(curr)
    except ValueError:
        current_index = 0

    try:
        required_index = tiers.index(req)
    except ValueError:
        required_index = 0

    return current_index >= required_index


__all__ = [
    "TIER_HIERARCHY",
    "LicenseStatus",
    "LicenseInfo",
    "determine_license_status",
    "check_tier_sufficiency",
]
