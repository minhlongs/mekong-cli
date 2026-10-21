# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Gateway Login Client Models & Configuration."""

import os
from dataclasses import dataclass
from typing import Optional

DEFAULT_GATEWAY_URL = os.environ.get(
    "RAAS_GATEWAY_URL",
    "https://www.mekongmind.com",
)
REQUEST_TIMEOUT = int(os.environ.get("RAAS_REQUEST_TIMEOUT", "5"))


def _get_version() -> str:
    """Get Mekong CLI version."""
    try:
        import importlib.metadata
        return importlib.metadata.version("mekong-cli")
    except Exception:
        return "3.0.0"


USER_AGENT = f"mekong-cli/{_get_version()}"


@dataclass
class LicenseInfo:
    """License information returned from gateway verification."""

    valid: bool
    tier: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[str] = None
    features: Optional[list] = None
    error: Optional[str] = None


@dataclass
class VerifyRequest:
    """Request payload for license verification."""

    license_key: str
    email: Optional[str] = None
    action: str = "verify"


class GatewayClientError(Exception):
    """Error communicating with RaaS Gateway."""
