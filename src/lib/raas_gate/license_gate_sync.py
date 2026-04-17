"""
License Gate Sync — Gateway sync and rate-limit status for RaasLicenseGate

Provides:
- sync_license_state: Sync license with RaaS Gateway and AgencyOS dashboard
- get_gateway_status: Current gateway connection status
- get_rate_limit_info: Current rate limit info from gateway or tier defaults
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

import requests

from src.raas.credit_rate_limiter import TIER_LIMITS

logger = logging.getLogger(__name__)


class LicenseGateSyncMixin:
    """Mixin for gateway sync and rate-limit status operations."""

    def sync_license_state(self) -> Tuple[bool, Optional[str]]:
        """
        Sync license state with RaaS Gateway and AgencyOS dashboard.

        Returns:
            Tuple of (success, error_message)

        Side Effects:
            - Updates _gateway_rate_limit with latest from gateway
            - Updates _last_gateway_sync timestamp
            - Syncs usage metering to gateway
        """
        if not self._license_key:
            return False, "No license key to sync"

        try:
            response = requests.post(
                f"{self._remote_url}/v1/auth/validate",
                headers={"Authorization": f"Bearer {self._license_key}"},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self._gateway_rate_limit = data.get("rateLimit")
                self._last_gateway_sync = int(time.time())

                if data.get("valid"):
                    self._license_tier = data.get("tier", self._license_tier)
                    self._validated = True
                    return True, None
                else:
                    return False, "Gateway returned invalid license status"
            else:
                return False, f"Gateway sync failed: HTTP {response.status_code}"

        except requests.RequestException as e:
            return False, f"Gateway sync error: {str(e)}"

    def get_gateway_status(self) -> Dict[str, Any]:
        """
        Get current gateway connection status.

        Returns:
            Dict with url, last_sync, rate_limit, license_synced
        """
        return {
            "url": self._remote_url,
            "last_sync": self._last_gateway_sync,
            "rate_limit": self._gateway_rate_limit,
            "license_synced": self._validated and self._last_gateway_sync is not None,
        }

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit info from gateway or tier defaults.

        Returns:
            Dict with limit, remaining, resetIn
        """
        if self._gateway_rate_limit:
            return self._gateway_rate_limit
        tier_limits = TIER_LIMITS.get(self._license_tier or "free", TIER_LIMITS["free"])
        return {
            "limit": tier_limits.get("daily", 10),
            "remaining": tier_limits.get("daily", 10),
            "resetIn": 60,
        }
