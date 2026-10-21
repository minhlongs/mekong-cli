# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Key generation and display helpers for RaaS License CLI."""
from __future__ import annotations

from datetime import datetime
import hashlib
import os
import secrets
from typing import Optional

from src.lib.raas_gate import LicenseTier

TIER_DISPLAY = {
    "free": "🔓 FREE",
    "pro": "💎 PRO",
    "enterprise": "🏢 ENTERPRISE",
}


def _generate_key(tier: LicenseTier, tenant_id: Optional[str] = None) -> str:
    """Generate a license key with embedded tier and timestamp.

    Format: raas_{tier}_{timestamp}_{random}_hmac
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(8)
    tenant_part = tenant_id[:8] if tenant_id else "anon"

    payload = f"{tier}_{timestamp}_{tenant_part}_{random_part}"

    secret = os.getenv("RAAS_KEY_SECRET")
    if not secret:
        raise ValueError(
            "RAAS_KEY_SECRET environment variable is required. "
            "Generate a secure key: openssl rand -hex 32"
        )
    hmac_sig = hashlib.sha256(f"{payload}{secret}".encode()).hexdigest()[:8]

    return f"raas_{payload}_{hmac_sig}"
