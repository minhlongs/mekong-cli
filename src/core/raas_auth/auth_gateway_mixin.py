# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Gateway Mixin — Gateway validation and verify for RaaSAuthClient."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests as _requests_base

from src.core.auth_types import (
    VALIDATION_ENDPOINT_V1,
    VALIDATION_ENDPOINT_V2,
    VERIFY_ENDPOINT,
    AuthResult,
    GatewayVerifyResult,
    TenantContext,
)

logger = logging.getLogger(__name__)
DASHBOARD_URL = "https://www.mekongmind.com/dashboard"


def _get_requests():
    """Return the requests module, looking up through src.core.raas_auth namespace first."""
    pkg = sys.modules.get("src.core.raas_auth")
    return getattr(pkg, "requests", _requests_base) if pkg is not None else _requests_base


class AuthGatewayMixin:
    """Mixin for RaaS Gateway API interactions."""

    def _call_gateway_validation(self, token: str, endpoint: str) -> AuthResult:
        """Call gateway validation endpoint with circuit breaker failover."""
        try:
            headers = {"Authorization": f"Bearer {token}"}
            if cert_headers := self._get_certificate_headers():
                headers.update(cert_headers)

            response = _get_requests().post(f"{self.gateway_url}{endpoint}", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                exp = data.get("expires_at")
                tenant = TenantContext(
                    tenant_id=data.get("tenant_id", "unknown"),
                    tier=data.get("tier", "free"),
                    role=data.get("role", "free"),
                    license_key=token if token.startswith("mk_") else None,
                    features=data.get("features", []),
                    expires_at=datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None,
                )
                self._session_manager.save(self._session_manager.create_from_tenant(tenant, token))
                self._last_validated = datetime.now(timezone.utc)
                return AuthResult(valid=True, tenant=tenant)
            if response.status_code == 404:
                return AuthResult(valid=False, error=f"Endpoint {endpoint} not found", error_code="endpoint_not_found")
            if response.status_code == 401:
                return AuthResult(valid=False, error="Invalid credentials", error_code="invalid_credentials")
            if response.status_code == 403:
                return AuthResult(valid=False, error="Credentials expired or revoked", error_code="credentials_revoked")
            return self._tenant_manager.local_validate(token)
        except _requests_base.RequestException:
            return self._tenant_manager.local_validate(token)

    def validate_credentials(self, token: Optional[str] = None, use_v2: bool = True) -> AuthResult:
        """Validate credentials against RaaS Gateway."""
        if self.local_test_mode:
            return self._tenant_manager.local_validate(token)
        if not token:
            token = self._load_credentials().get("token") or os.getenv("RAAS_LICENSE_KEY")
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
        """Lightweight gateway verification via /v1/verify."""
        if not token:
            token = self._load_credentials().get("token") or os.getenv("RAAS_LICENSE_KEY")
        if not token:
            return GatewayVerifyResult(valid=False, error="No credentials provided", requires_auth=True)
        token = token.strip()
        is_valid, error, _ = self._tenant_manager.validate_token_format(token)
        if not is_valid:
            return GatewayVerifyResult(valid=False, error=error, requires_auth=True)
        try:
            headers = {"Authorization": f"Bearer {token}"}
            if cert_headers := self._get_certificate_headers():
                headers.update(cert_headers)
            response = _get_requests().get(f"{self.gateway_url}{VERIFY_ENDPOINT}", headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return GatewayVerifyResult(
                    valid=True, gateway_version=data.get("gateway_version"),
                    gateway_status=data.get("status", "operational"), requires_auth=False,
                )
            if response.status_code == 401:
                return GatewayVerifyResult(valid=False, error="Invalid or expired credentials", requires_auth=True)
            if response.status_code == 403:
                return GatewayVerifyResult(valid=False, error="Credentials revoked or insufficient permissions", requires_auth=True)
            if response.status_code == 404:
                return GatewayVerifyResult(valid=False, error="Gateway verify endpoint not found", gateway_status="unreachable")
            return GatewayVerifyResult(valid=False, error=f"Gateway returned {response.status_code}", gateway_status="error")
        except _requests_base.RequestException as e:
            return GatewayVerifyResult(valid=False, error=f"Gateway unreachable: {e}", gateway_status="unreachable")

    def sync_to_dashboard(self) -> Dict[str, Any]:
        """Sync license state to AgencyOS dashboard."""
        if not self.get_session().authenticated:
            return {"synced": False, "error": "Not authenticated", "dashboard_url": DASHBOARD_URL}
        try:
            token = self._load_credentials().get("token") or os.getenv("RAAS_LICENSE_KEY")
            if not token:
                return {"synced": False, "error": "No credentials", "dashboard_url": DASHBOARD_URL}
            _req = _get_requests()
            hdrs = {"Authorization": f"Bearer {token}"}
            response = _req.post(f"{self.gateway_url}{VALIDATION_ENDPOINT_V2}", headers=hdrs, timeout=10)
            if response.status_code == 404:
                response = _req.post(f"{self.gateway_url}{VALIDATION_ENDPOINT_V1}", headers=hdrs, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tid = data.get("tenant_id", "unknown")
                return {
                    "synced": True, "tenant_id": tid, "tier": data.get("tier"),
                    "dashboard_url": f"{DASHBOARD_URL}/{tid}", "features": data.get("features", []),
                    "rate_limit": data.get("rateLimit"), "gateway_version": data.get("gateway", {}).get("version"),
                }
            return {"synced": False, "error": f"Gateway returned {response.status_code}", "dashboard_url": DASHBOARD_URL}
        except _requests_base.RequestException as e:
            return {"synced": False, "error": f"Sync failed: {e}", "dashboard_url": DASHBOARD_URL}

    def get_gateway_health(self) -> Dict[str, Any]:
        """Check RaaS Gateway health status."""
        try:
            response = _get_requests().get(f"{self.gateway_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {"status": data.get("status"), "version": data.get("version"), "url": self.gateway_url, "healthy": True}
            return {"healthy": False, "error": f"Gateway returned {response.status_code}", "url": self.gateway_url}
        except _requests_base.RequestException as e:
            return {"healthy": False, "error": f"Gateway unreachable: {e}", "url": self.gateway_url}
