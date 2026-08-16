# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Auth package — public API re-exports.

Usage:
    from src.core.raas_auth import RaaSAuthClient, get_auth_client
    from src.core.raas_auth import TenantContext, AuthResult, SessionInfo
"""

from src.core.auth_types import (
    TenantContext,
    AuthResult,
    GatewayVerifyResult,
    SessionInfo,
    SessionCache,
    VERIFY_ENDPOINT,
    VALIDATION_ENDPOINT_V1,
    VALIDATION_ENDPOINT_V2,
    SESSION_TTL_SECONDS,
    REFRESH_BUFFER_SECONDS,
)
from src.core.auth_session import SessionManager
from src.core.auth_tenant import TenantManager

from .raas_auth_client import RaaSAuthClient

# Re-export dependencies so existing patch() targets remain valid:
# patch("src.core.raas_auth.requests.post") and patch("src.core.raas_auth.get_secure_storage")
import requests
from src.auth.secure_storage import get_secure_storage

from typing import Optional

# Singleton instance
_auth_client: Optional[RaaSAuthClient] = None


def get_auth_client(gateway_url: Optional[str] = None) -> RaaSAuthClient:
    """
    Get or create RaaS Auth Client singleton.

    Args:
        gateway_url: Optional custom gateway URL

    Returns:
        RaaSAuthClient instance.
    """
    global _auth_client
    if _auth_client is None:
        _auth_client = RaaSAuthClient(gateway_url=gateway_url)
    return _auth_client


__all__ = [
    "RaaSAuthClient",
    "get_auth_client",
    "TenantContext",
    "AuthResult",
    "GatewayVerifyResult",
    "SessionInfo",
    "SessionCache",
    "SessionManager",
    "TenantManager",
    "VERIFY_ENDPOINT",
    "VALIDATION_ENDPOINT_V1",
    "VALIDATION_ENDPOINT_V2",
    "SESSION_TTL_SECONDS",
    "REFRESH_BUFFER_SECONDS",
    "requests",
    "get_secure_storage",
]
