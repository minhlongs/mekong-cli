# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Sync Client package — public API re-exports.

Usage:
    from src.raas.sync_client import SyncClient, SyncResult, UsageSummary
    from src.raas.sync_client import get_sync_client, reset_sync_client
"""

from .models import SyncResult, UsageSummary
from .sync_core import SyncClient

# Re-export dependencies so existing patch() targets remain valid
from src.core.gateway_client import GatewayClient, GatewayError
from src.lib.raas_gate_validator import RaasGateValidator

# Global singleton helpers
from typing import Optional

_sync_client: Optional[SyncClient] = None


def get_sync_client() -> SyncClient:
    """Get global sync client instance."""
    global _sync_client
    if _sync_client is None:
        _sync_client = SyncClient()
    return _sync_client


def reset_sync_client() -> None:
    """Reset global sync client (for testing)."""
    global _sync_client
    _sync_client = None


__all__ = [
    "SyncClient",
    "SyncResult",
    "UsageSummary",
    "get_sync_client",
    "reset_sync_client",
    "GatewayClient",
    "GatewayError",
    "RaasGateValidator",
]
