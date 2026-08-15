"""
Auth Gateway Mixin — Gateway validation and verify for RaaSAuthClient

Handles:
- _call_gateway_validation: POST to /v2/license/validate or /v1/auth/validate
- validate_credentials: Full credential validation flow
- verify_gateway: Lightweight /v1/verify endpoint check
- sync_to_dashboard: Sync license state to AgencyOS dashboard
- get_gateway_health: Check gateway /health
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import sys
import requests as _requests_base

from src.core.auth_types import (
    AuthResult,
    TenantContext,
    GatewayVerifyResult,
    VERIFY_ENDPOINT,
    VALIDATION_ENDPOINT_V1,
    VALIDATION_ENDPOINT_V2,
)

logger = logging.getLogger(__name__)


def _get_requests():
    """
    Return the requests module, looking up through src.core.raas_auth namespace first.
    This allows patch("src.core.raas_auth.requests.post") to work in tests.
    """
    pkg = sys.modules.get("src.core.raas_auth")
    if pkg is not None:
        return getattr(pkg, "requests", _requests_base)
    return _requests_base


class AuthGatewayMixin:
    """Mixin for RaaS Gateway API interactions."""

    def _call_gateway_validation(self, token: str, endpoint: str) -> AuthResult:
        """
        Call gateway validation endpoint with circuit breaker failover.

        Args:
            token: Bearer token
            endpoint: Validation endpoint path

        Returns:
            AuthResult with validation status
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            cert_headers = self._get_certificate_headers()
            if cert_headers:
                headers.update(cert_headers)

            _req = _get_requests()
            response = _req.post(
                f"{self.gateway_url}{endpoint}",
                headers=headers,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                tenant = TenantContext(
                    tenant_id=data.get("tenant_id", "unknown"),
                    tier=data.get("tier", "free"),
                    role=data.get("role", "free"),
                    license_key=token if token.startswith("mk_") else None,
                    features=data.get("features", []),
                    expires_at=(
                        datetime.fromtimestamp(
                            data.get("expires_at", 0), tz=timezone.utc
                        )
                        if data.get("expires_at")
                        else None
                    ),
                )

                cache = self._session_manager.create_from_tenant(tenant, token)
                self._session_manager.save(cache)
                self._last_validated = datetime.now(timezone.utc)

                return AuthResult(valid=True, tenant=tenant)

            elif response.status_code == 404:
                return AuthResult(valid=False, error=f"Endpoint {endpoint} not found", error_code="endpoint_not_found")
            elif response.status_code == 401:
                return AuthResult(valid=False, error="Invalid credentials", error_code="invalid_credentials")
            elif response.status_code == 403:
                return AuthResult(valid=False, error="Credentials expired or revoked", error_code="credentials_revoked")
            else:
                return self._tenant_manager.local_validate(token)

        except _requests_base.RequestException:
            return self._tenant_manager.local_validate(token)

    def validate_credentials(
        self,
        token: Optional[str] = None,
        use_v2: bool = True,
    ) -> AuthResult:
        """
        Validate credentials against RaaS Gateway.

        Args:
            token: Bearer token (JWT or mk_ API key). If None, uses stored or RAAS_LICENSE_KEY.
            use_v2: Use /v2/license/validate endpoint (default: True)

        Returns:
            AuthResult with validation status and tenant context.
        """
        if self.local_test_mode:
            return self._tenant_manager.local_validate(token)

        if not token:
            creds = self._load_credentials()
            token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")

        if not token:
            return AuthResult(valid=False, error="No credentials provided", error_code="missing_credentials")

        is_valid, error, error_code = self._tenant_manager.validate_token_format(token)
        if not is_valid:
            return AuthResult(valid=False, error=error, error_code=error_code)

        endpoint = VALIDATION_ENDPOINT_V2 if use_v2 else VALIDATION_ENDPOINT_V1
        result = self._call_gateway_validation(token, endpoint)

        if result.error_code == "endpoint_not_found" and use_v2:
            result = self._call_gateway_validation(token, VALIDATION_ENDPOINT_V1)

        return result

    def verify_gateway(self, token: Optional[str] = None) -> GatewayVerifyResult:
        """
        Lightweight gateway verification via /v1/verify.

        Returns:
            GatewayVerifyResult with gateway status
        """
        if not token:
            creds = self._load_credentials()
            token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")

        if not token:
            return GatewayVerifyResult(valid=False, error="No credentials provided", requires_auth=True)

        token = token.strip()
        is_valid, error, _ = self._tenant_manager.validate_token_format(token)
        if not is_valid:
            return GatewayVerifyResult(valid=False, error=error, requires_auth=True)

        try:
            headers = {"Authorization": f"Bearer {token}"}
            cert_headers = self._get_certificate_headers()
            if cert_headers:
                headers.update(cert_headers)

            response = _get_requests().get(f"{self.gateway_url}{VERIFY_ENDPOINT}", headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return GatewayVerifyResult(
                    valid=True,
                    gateway_version=data.get("gateway_version"),
                    gateway_status=data.get("status", "operational"),
                    requires_auth=False,
                )
            elif response.status_code == 401:
                return GatewayVerifyResult(valid=False, error="Invalid or expired credentials", requires_auth=True)
            elif response.status_code == 403:
                return GatewayVerifyResult(valid=False, error="Credentials revoked or insufficient permissions", requires_auth=True)
            elif response.status_code == 404:
                return GatewayVerifyResult(valid=False, error="Gateway verify endpoint not found", gateway_status="unreachable")
            else:
                return GatewayVerifyResult(valid=False, error=f"Gateway returned {response.status_code}", gateway_status="error")

        except _requests_base.RequestException as e:
            return GatewayVerifyResult(valid=False, error=f"Gateway unreachable: {str(e)}", gateway_status="unreachable")

    def sync_to_dashboard(self) -> Dict[str, Any]:
        """
        Sync license state to AgencyOS dashboard.

        Returns:
            Dict with sync status and dashboard URL
        """
        session = self.get_session()
        if not session.authenticated:
            return {"synced": False, "error": "Not authenticated", "dashboard_url": "https://www.mekongmind.com/dashboard"}

        try:
            creds = self._load_credentials()
            token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")

            if not token:
                return {"synced": False, "error": "No credentials", "dashboard_url": "https://www.mekongmind.com/dashboard"}

            _req = _get_requests()
            response = _req.post(
                f"{self.gateway_url}{VALIDATION_ENDPOINT_V2}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )

            if response.status_code == 404:
                response = _req.post(
                    f"{self.gateway_url}{VALIDATION_ENDPOINT_V1}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )

            if response.status_code == 200:
                data = response.json()
                tenant_id = data.get("tenant_id", "unknown")
                return {
                    "synced": True,
                    "tenant_id": tenant_id,
                    "tier": data.get("tier"),
                    "dashboard_url": f"https://www.mekongmind.com/dashboard/{tenant_id}",
                    "features": data.get("features", []),
                    "rate_limit": data.get("rateLimit"),
                    "gateway_version": data.get("gateway", {}).get("version"),
                }
            else:
                return {"synced": False, "error": f"Gateway returned {response.status_code}", "dashboard_url": "https://www.mekongmind.com/dashboard"}

        except _requests_base.RequestException as e:
            return {"synced": False, "error": f"Sync failed: {str(e)}", "dashboard_url": "https://www.mekongmind.com/dashboard"}

    def get_gateway_health(self) -> Dict[str, Any]:
        """Check RaaS Gateway health status."""
        try:
            response = _get_requests().get(f"{self.gateway_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {"status": data.get("status"), "version": data.get("version"), "url": self.gateway_url, "healthy": True}
            else:
                return {"healthy": False, "error": f"Gateway returned {response.status_code}", "url": self.gateway_url}
        except _requests_base.RequestException as e:
            return {"healthy": False, "error": f"Gateway unreachable: {str(e)}", "url": self.gateway_url}
