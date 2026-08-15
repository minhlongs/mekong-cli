"""
RaaS Auth Client — Base class + composed RaaSAuthClient

Manages:
- Client initialization (secure storage, certificate store, circuit breaker)
- Session management (backward-compat wrappers)
- Auth lifecycle: login, logout, rotate_key
- Status queries: get_tenant_context, is_authenticated

Delegates gateway/validation to AuthGatewayMixin,
credential storage to AuthCredentialsMixin,
certificate ops to AuthCertificateMixin.
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import sys
from src.auth.secure_storage import get_secure_storage as _get_secure_storage_base, SecureStorage
from src.core.certificate_store import get_certificate_store, CertificateStore

from src.core.auth_types import (
    TenantContext,
    AuthResult,
    SessionInfo,
    SessionCache,
    SESSION_TTL_SECONDS,
    REFRESH_BUFFER_SECONDS,
)
from src.core.auth_session import SessionManager
from src.core.auth_tenant import TenantManager

from .auth_credentials_mixin import AuthCredentialsMixin
from .auth_certificate_mixin import AuthCertificateMixin
from .auth_gateway_mixin import AuthGatewayMixin

logger = logging.getLogger(__name__)


class _RaaSAuthClientBase(AuthCredentialsMixin, AuthCertificateMixin, AuthGatewayMixin):
    """
    RaaS Gateway Authentication Client — base with initialization and lifecycle.

    Mixin chain (MRO):
    - AuthCredentialsMixin: _save_credentials, _load_credentials, _migrate_to_secure_storage
    - AuthCertificateMixin: _get_certificate_headers, get_certificate_status, rotate_certificate
    - AuthGatewayMixin: _call_gateway_validation, validate_credentials, verify_gateway, sync_to_dashboard, get_gateway_health
    """

    DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"

    GATEWAY_URLS = [
        os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc"),
        os.getenv("RAAS_GATEWAY_URL_SECONDARY", "https://api.cashclaw.cc"),
        os.getenv("RAAS_GATEWAY_URL_TERTIARY"),
    ]

    CREDENTIALS_FILE = "~/.mekong/raas/credentials.json"
    SESSION_CACHE_FILE = "~/.mekong/session.json"

    # Backward-compat endpoint constants
    VERIFY_ENDPOINT = "/v1/verify"
    VALIDATION_ENDPOINT_V1 = "/v1/auth/validate"
    VALIDATION_ENDPOINT_V2 = "/v2/license/validate"

    SESSION_TTL_SECONDS = 300
    REFRESH_BUFFER_SECONDS = 60
    CIRCUIT_FAILURE_THRESHOLD = 3
    CIRCUIT_RECOVERY_TIMEOUT = 60

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        credentials_file: Optional[str] = None,
        use_secure_storage: bool = True,
        use_certificate_auth: bool = True,
    ):
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL)
        self.credentials_path = Path(
            credentials_file or os.getenv("RAAS_CREDENTIALS_FILE", self.CREDENTIALS_FILE)
        ).expanduser()

        self.use_secure_storage = use_secure_storage and os.getenv(
            "RAAS_USE_SECURE_STORAGE", "true"
        ).lower() != "false"
        self.use_certificate_auth = use_certificate_auth and os.getenv(
            "RAAS_USE_CERTIFICATE_AUTH", "true"
        ).lower() != "false"

        self.local_test_mode = os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"

        self._session_manager = SessionManager(
            cache_path="~/.mekong/session.json",
            ttl_seconds=SESSION_TTL_SECONDS,
            refresh_buffer=REFRESH_BUFFER_SECONDS,
        )
        self._tenant_manager = TenantManager(local_test_mode=self.local_test_mode)

        # Look up get_secure_storage via package namespace so patch("src.core.raas_auth.get_secure_storage") works
        _pkg = sys.modules.get("src.core.raas_auth")
        _get_secure_storage = (getattr(_pkg, "get_secure_storage", None) if _pkg else None) or _get_secure_storage_base

        self._secure_storage: Optional[SecureStorage] = None
        if self.use_secure_storage:
            try:
                self._secure_storage = _get_secure_storage()
            except Exception as e:
                logger.debug("Secure storage initialization failed: %s", e)

        self._certificate_store: Optional[CertificateStore] = None
        if self.use_certificate_auth:
            try:
                self._certificate_store = get_certificate_store(use_secure_storage=self.use_secure_storage)
            except Exception as e:
                logger.debug("Certificate store initialization failed: %s", e)

        # Circuit breaker state per gateway URL
        self._gateway_failure_counts: Dict[str, int] = {}
        self._gateway_circuits: Dict[str, bool] = {}
        self._gateway_last_failure: Dict[str, float] = {}

        for url in self.GATEWAY_URLS:
            if url:
                self._gateway_failure_counts[url] = 0
                self._gateway_circuits[url] = False
                self._gateway_last_failure[url] = 0.0

        self._session_manager.load()
        self._last_validated: Optional[datetime] = None

    # ------------------------------------------------------------------ #
    # Backward-compat session cache properties                            #
    # ------------------------------------------------------------------ #

    @property
    def _session_cache(self) -> Optional[SessionCache]:
        return self._session_manager.get_cached()

    @property
    def session_cache_path(self) -> Path:
        return self._session_manager.session_cache_path

    @session_cache_path.setter
    def session_cache_path(self, value: Path | str) -> None:
        if isinstance(value, str):
            value = Path(value).expanduser()
        self._session_manager = SessionManager(
            cache_path=str(value),
            ttl_seconds=SESSION_TTL_SECONDS,
            refresh_buffer=REFRESH_BUFFER_SECONDS,
        )

    @_session_cache.setter
    def _session_cache(self, value: Optional[SessionCache]) -> None:
        if value is None:
            self._session_manager.clear()
        else:
            self._session_manager.save(value)

    def _save_session_cache(self, cache: SessionCache) -> None:
        self._session_manager.save(cache)

    def _load_session_cache(self) -> Optional[SessionCache]:
        return self._session_manager.load()

    def _clear_session_cache(self) -> bool:
        return self._session_manager.clear()

    def _session_cache_to_tenant_context(self, cache: SessionCache) -> TenantContext:
        return TenantContext(
            tenant_id=cache.tenant_id,
            tier=cache.tier,
            role=cache.role,
            license_key=cache.license_key,
            features=cache.features,
            expires_at=cache.expires_at,
        )

    # ------------------------------------------------------------------ #
    # Session / auth lifecycle                                             #
    # ------------------------------------------------------------------ #

    def get_session(self) -> SessionInfo:
        """Get current session information with auto-refresh."""
        creds = self._load_credentials()
        token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")
        uses_secure_storage = creds.get("uses_secure_storage", False) or (
            self.use_secure_storage and self._secure_storage is not None
        )

        cache = self._session_manager.get_cached()
        if cache:
            if self._session_manager.should_refresh(cache) and token:
                self._refresh_session(token)

            return self._session_manager.to_session_info(
                cache=cache,
                credentials_path=str(self.credentials_path),
                gateway_url=self.gateway_url,
                last_validated=self._last_validated,
                uses_secure_storage=uses_secure_storage,
            )

        if token:
            result = self.validate_credentials(token)
            if result.valid and result.tenant:
                return SessionInfo(
                    tenant_id=result.tenant.tenant_id,
                    tier=result.tenant.tier,
                    authenticated=True,
                    credentials_path=str(self.credentials_path),
                    last_validated=self._last_validated,
                    gateway_url=self.gateway_url,
                    uses_secure_storage=uses_secure_storage,
                )

        return self._session_manager.create_anonymous_session(
            credentials_path=str(self.credentials_path),
            gateway_url=self.gateway_url,
            uses_secure_storage=uses_secure_storage,
        )

    def _refresh_session(self, token: str) -> None:
        """Refresh session cache with fresh gateway validation."""
        self.validate_credentials(token, use_v2=True)

    def login(
        self,
        token: str,
        persist: bool = True,
        migrate_to_secure: bool = True,
    ) -> AuthResult:
        """Login with credentials, optionally persisting them."""
        result = self.validate_credentials(token)

        if result.valid and persist:
            self._save_credentials({"token": token, "updated_at": time.time()})
            if migrate_to_secure and self.use_secure_storage:
                self._migrate_to_secure_storage()

        return result

    def logout(self) -> bool:
        """Logout and clear stored credentials and session cache."""
        cleared = False

        if self.credentials_path.exists():
            try:
                os.remove(self.credentials_path)
                cleared = True
            except OSError:
                pass

        self._session_manager.clear()
        self._last_validated = None
        return cleared

    def rotate_key(self, new_key: str) -> AuthResult:
        """Rotate to new API key."""
        if not new_key.startswith("mk_"):
            return AuthResult(
                valid=False,
                error="Invalid API key format (must start with mk_)",
                error_code="invalid_api_key_format",
            )

        result = self.validate_credentials(new_key)
        if result.valid:
            self._save_credentials({"token": new_key, "updated_at": time.time()})
        return result

    def get_tenant_context(self) -> Optional[TenantContext]:
        """Get cached tenant context (if available)."""
        cache = self._session_manager.get_cached()
        if cache:
            return TenantContext(
                tenant_id=cache.tenant_id,
                tier=cache.tier,
                role=cache.role,
                license_key=cache.license_key,
                features=cache.features,
                expires_at=cache.expires_at,
            )
        return None

    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self.get_session().authenticated


class RaaSAuthClient(_RaaSAuthClientBase):
    """
    RaaS Gateway Authentication Client with Multi-Gateway Failover.

    Composes:
    - _RaaSAuthClientBase: initialization, session lifecycle, login/logout/rotate_key
    - AuthCredentialsMixin: credential storage/migration
    - AuthCertificateMixin: device certificate operations
    - AuthGatewayMixin: gateway validation, verify, dashboard sync, health check
    """
