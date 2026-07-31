"""Pure policy helpers for tier rate-limit middleware."""

from __future__ import annotations

import os
from typing import Any, Optional

from fastapi import Request

from ..license.jwt_license_generator import validate_jwt_license
from src.services.license_enforcement import LicenseStatus


LICENSE_BLOCK_MESSAGES = {
    LicenseStatus.SUSPENDED: ("license_suspended", "License suspended - contact support to restore access"),
    LicenseStatus.REVOKED: ("license_revoked", "License revoked - access denied"),
    LicenseStatus.EXPIRED: ("license_expired", "License expired - please renew to continue"),
    LicenseStatus.INVALID: ("license_invalid", "Invalid license key - please check your key and try again"),
    LicenseStatus.INSUFFICIENT_TIER: (
        "tier_insufficient",
        "Current tier insufficient - upgrade to access this endpoint",
    ),
}


def extract_license_key(request: Request) -> Optional[str]:
    """Extract a license key from supported request headers."""
    license_key = request.headers.get("X-License-Key")
    if license_key:
        return license_key.strip()

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        if "." in token:
            return token
    return None


def validate_and_get_tier(license_key: str) -> tuple[str, Optional[dict[str, Any]]]:
    """Validate JWT license key and return tier plus payload."""
    if not license_key:
        return "free", None
    try:
        is_valid, payload, _error = validate_jwt_license(license_key)
    except Exception:
        return "free", None
    if is_valid and payload:
        return str(payload.get("tier", "free")).lower(), payload
    return "free", None


def tenant_id_from_license_key(license_key: Optional[str]) -> str:
    """Return display-safe tenant id for logs and enforcement decisions."""
    if not license_key:
        return "anonymous"
    return license_key[:16] + "..." if len(license_key) > 16 else license_key


def get_preset_for_path(path: str) -> str:
    """Map request path to rate limit preset."""
    path_lower = path.lower()
    if "/auth/login" in path_lower or "/auth/dev-login" in path_lower:
        return "auth_login"
    if "/auth/callback" in path_lower:
        return "auth_callback"
    if "/auth/refresh" in path_lower:
        return "auth_refresh"
    if "/auth/" in path_lower:
        return "auth_login"
    return "api_default"


def is_dev_mode(configured_dev_mode: bool) -> bool:
    """Return true when rate limiting should be bypassed for local development."""
    return configured_dev_mode or os.getenv("DISABLE_RATE_LIMITING", "false").lower() == "true"


def request_context(request: Request) -> dict[str, str]:
    """Build safe request context for structured rate-limit logs."""
    return {
        "method": request.method,
        "path": str(request.url.path),
        "user_agent": request.headers.get("user-agent", ""),
        "ip": request.client.host if request.client else "",
    }


def quota_utilization_pct(limit: int, remaining: int) -> float:
    """Calculate quota utilization percentage."""
    return ((limit - remaining) / limit * 100) if limit > 0 else 0


def license_block_message(status: LicenseStatus) -> tuple[str, str]:
    """Return response error type and message for a blocked license status."""
    return LICENSE_BLOCK_MESSAGES.get(status, ("license_blocked", "Access denied due to license issue"))


__all__ = [
    "extract_license_key",
    "get_preset_for_path",
    "is_dev_mode",
    "license_block_message",
    "quota_utilization_pct",
    "request_context",
    "tenant_id_from_license_key",
    "validate_and_get_tier",
]
