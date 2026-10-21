# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Auth Client — Base class + composed RaaSAuthClient."""

from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.auth.secure_storage import SecureStorage, get_secure_storage as _get_secure_storage_base
from src.core.auth_session import SessionManager
from src.core.auth_tenant import TenantManager
from src.core.auth_types import REFRESH_BUFFER_SECONDS, SESSION_TTL_SECONDS, AuthResult, SessionCache, SessionInfo, TenantContext
from src.core.certificate_store import CertificateStore, get_certificate_store

from .auth_certificate_mixin import AuthCertificateMixin
from .auth_credentials_mixin import AuthCredentialsMixin
from .auth_gateway_mixin import AuthGatewayMixin

logger = logging.getLogger(__name__)


class _RaaSAuthClientBase(AuthCredentialsMixin, AuthCertificateMixin, AuthGatewayMixin):
    """RaaS Gateway Authentication Client — base with initialization and lifecycle."""

    DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"
    GATEWAY_URLS = [
        os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc"),
        os.getenv("RAAS_GATEWAY_URL_SECONDARY", "https://api.cashclaw.cc"),
        os.getenv("RAAS_GATEWAY_URL_TERTIARY"),
    ]
    CREDENTIALS_FILE, SESSION_CACHE_FILE = "~/.mekong/raas/credentials.json", "~/.mekong/session.json"
    VERIFY_ENDPOINT, VALIDATION_ENDPOINT_V1, VALIDATION_ENDPOINT_V2 = "/v1/verify", "/v1/auth/validate", "/v2/license/validate"
    SESSION_TTL_SECONDS, REFRESH_BUFFER_SECONDS = 300, 60
    CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT = 3, 60

    def __init__(
        self, gateway_url: Optional[str] = None, credentials_file: Optional[str] = None,
        use_secure_storage: bool = True, use_certificate_auth: bool = True,
    ):
        self.gateway_url = gateway_url or os.getenv("RAAS_GATEWAY_URL", self.DEFAULT_GATEWAY_URL)
        self.credentials_path = Path(credentials_file or os.getenv("RAAS_CREDENTIALS_FILE", self.CREDENTIALS_FILE)).expanduser()
        self.use_secure_storage = use_secure_storage and os.getenv("RAAS_USE_SECURE_STORAGE", "true").lower() != "false"
        self.use_certificate_auth = use_certificate_auth and os.getenv("RAAS_USE_CERTIFICATE_AUTH", "true").lower() != "false"
        self.local_test_mode = os.getenv("RAAS_LOCAL_TEST", "").lower() == "true"

        self._session_manager = SessionManager(
            cache_path="~/.mekong/session.json", ttl_seconds=SESSION_TTL_SECONDS, refresh_buffer=REFRESH_BUFFER_SECONDS,
        )
        self._tenant_manager = TenantManager(local_test_mode=self.local_test_mode)

        _pkg = sys.modules.get("src.core.raas_auth")
        _get_sec = (getattr(_pkg, "get_secure_storage", None) if _pkg else None) or _get_secure_storage_base
        self._secure_storage: Optional[SecureStorage] = None
        if self.use_secure_storage:
            try:
                self._secure_storage = _get_sec()
            except Exception as e:
                logger.debug("Secure storage initialization failed: %s", e)

        self._certificate_store: Optional[CertificateStore] = None
        if self.use_certificate_auth:
            try:
                self._certificate_store = get_certificate_store(use_secure_storage=self.use_secure_storage)
            except Exception as e:
                logger.debug("Certificate store initialization failed: %s", e)

        urls = [u for u in self.GATEWAY_URLS if u]
        self._gateway_failure_counts: Dict[str, int] = {u: 0 for u in urls}
        self._gateway_circuits: Dict[str, bool] = {u: False for u in urls}
        self._gateway_last_failure: Dict[str, float] = {u: 0.0 for u in urls}
        self._session_manager.load()
        self._last_validated: Optional[datetime] = None

    @property
    def _session_cache(self) -> Optional[SessionCache]:
        return self._session_manager.get_cached()

    @_session_cache.setter
    def _session_cache(self, value: Optional[SessionCache]) -> None:
        self._session_manager.clear() if value is None else self._session_manager.save(value)

    @property
    def session_cache_path(self) -> Path:
        return self._session_manager.session_cache_path

    @session_cache_path.setter
    def session_cache_path(self, value: Path | str) -> None:
        p = Path(value).expanduser() if isinstance(value, str) else value
        self._session_manager = SessionManager(cache_path=str(p), ttl_seconds=SESSION_TTL_SECONDS, refresh_buffer=REFRESH_BUFFER_SECONDS)

    def _save_session_cache(self, cache: SessionCache) -> None:
        self._session_manager.save(cache)

    def _load_session_cache(self) -> Optional[SessionCache]:
        return self._session_manager.load()

    def _clear_session_cache(self) -> bool:
        return self._session_manager.clear()

    def _session_cache_to_tenant_context(self, cache: SessionCache) -> TenantContext:
        return TenantContext(
            tenant_id=cache.tenant_id, tier=cache.tier, role=cache.role,
            license_key=cache.license_key, features=cache.features, expires_at=cache.expires_at,
        )

    def get_session(self) -> SessionInfo:
        creds = self._load_credentials()
        token = creds.get("token") or os.getenv("RAAS_LICENSE_KEY")
        uses_secure = creds.get("uses_secure_storage", False) or (self.use_secure_storage and self._secure_storage is not None)
        if cache := self._session_manager.get_cached():
            if self._session_manager.should_refresh(cache) and token:
                self._refresh_session(token)
            return self._session_manager.to_session_info(
                cache=cache, credentials_path=str(self.credentials_path),
                gateway_url=self.gateway_url, last_validated=self._last_validated, uses_secure_storage=uses_secure,
            )
        if token:
            result = self.validate_credentials(token)
            if result.valid and result.tenant:
                return SessionInfo(
                    tenant_id=result.tenant.tenant_id, tier=result.tenant.tier, authenticated=True,
                    credentials_path=str(self.credentials_path), last_validated=self._last_validated,
                    gateway_url=self.gateway_url, uses_secure_storage=uses_secure,
                )
        return self._session_manager.create_anonymous_session(
            credentials_path=str(self.credentials_path), gateway_url=self.gateway_url, uses_secure_storage=uses_secure,
        )

    def _refresh_session(self, token: str) -> None:
        self.validate_credentials(token, use_v2=True)

    def login(self, token: str, persist: bool = True, migrate_to_secure: bool = True) -> AuthResult:
        result = self.validate_credentials(token)
        if result.valid and persist:
            self._save_credentials({"token": token, "updated_at": time.time()})
            if migrate_to_secure and self.use_secure_storage:
                self._migrate_to_secure_storage()
        return result

    def logout(self) -> bool:
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
        if not new_key.startswith("mk_"):
            return AuthResult(valid=False, error="Invalid API key format (must start with mk_)", error_code="invalid_api_key_format")
        result = self.validate_credentials(new_key)
        if result.valid:
            self._save_credentials({"token": new_key, "updated_at": time.time()})
        return result

    def get_tenant_context(self) -> Optional[TenantContext]:
        cache = self._session_manager.get_cached()
        return self._session_cache_to_tenant_context(cache) if cache else None

    def is_authenticated(self) -> bool:
        return self.get_session().authenticated


RaaSAuthClient = _RaaSAuthClientBase
