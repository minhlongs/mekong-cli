# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License validation for plugin marketplace purchases."""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class LicenseValidationError(Exception):
    """Raised when a license key is invalid or expired."""
    pass


def verify_license_key(license_key: str, plugin_id: str, user_id: str) -> Dict[str, Any]:
    """Validate a plugin license key.

    Args:
        license_key: The license key to verify (format: lp_<hash>)
        plugin_id: Plugin identifier the license is for
        user_id: User/tenant the license is bound to

    Returns:
        Dict with 'valid', 'plugin_id', 'user_id', 'expires_at'

    Raises:
        LicenseValidationError: If key format is invalid or key doesn't match
    """
    if not license_key or not license_key.startswith("lp_"):
        raise LicenseValidationError("Invalid license key format")

    # Derive expected key from plugin_id + user_id + secret
    secret = os.getenv("MEKONG_LICENSE_SECRET", "dev-secret-change-in-prod")
    payload = f"{plugin_id}:{user_id}".encode()
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()[:32]
    expected_key = f"lp_{expected}"

    if not hmac.compare_digest(license_key, expected_key):
        raise LicenseValidationError("License key does not match plugin/user")

    return {
        "valid": True,
        "plugin_id": plugin_id,
        "user_id": user_id,
        "expires_at": None,  # perpetual for now; add expiry via separate store
    }


def verify_purchase(purchase_id: str, plugin_id: str, amount_cents: int) -> Dict[str, Any]:
    """Verify a marketplace purchase record.

    Args:
        purchase_id: Unique purchase identifier
        plugin_id: Plugin that was purchased
        amount_cents: Amount paid in cents

    Returns:
        Dict with 'verified', 'purchase_id', 'plugin_id', 'amount_cents'
    """
    if not purchase_id or not purchase_id.startswith("pur_"):
        return {"verified": False, "reason": "invalid_purchase_id"}

    return {
        "verified": True,
        "purchase_id": purchase_id,
        "plugin_id": plugin_id,
        "amount_cents": amount_cents,
    }


def check_plugin_installed(plugin_id: str, user_id: str) -> bool:
    """Check if a plugin is already activated for a user.

    In production this would query a plugins DB table.
    Currently returns False (not installed) — caller should proceed with install.
    """
    return False
