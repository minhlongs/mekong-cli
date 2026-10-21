# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Auth Session - Session Management."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import tempfile
from typing import Optional

from .auth_types import SessionCache, SessionInfo, TenantContext


class SessionManager:
    """Session cache manager with TTL support."""

    DEFAULT_TTL_SECONDS = 900  # 15 minutes
    DEFAULT_REFRESH_BUFFER = 300  # 5 minutes

    _logger: logging.Logger = logging.getLogger(__name__)

    def __init__(
        self,
        cache_path: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        refresh_buffer: Optional[int] = None,
    ):
        self.session_cache_path = Path(cache_path or "~/.mekong/session.json").expanduser()
        self.ttl_seconds = ttl_seconds or self.DEFAULT_TTL_SECONDS
        self.refresh_buffer = refresh_buffer or self.DEFAULT_REFRESH_BUFFER
        self._in_memory_cache: Optional[SessionCache] = None

    def _ensure_cache_dir(self) -> None:
        self.session_cache_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.session_cache_path.parent, 0o700)

    def save(self, cache: SessionCache) -> None:
        """Save session cache to disk using atomic write."""
        self._ensure_cache_dir()
        fd, tmp_path = tempfile.mkstemp(dir=str(self.session_cache_path.parent), prefix=".session_cache_tmp_")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(cache.to_dict(), f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp_path, 0o600)
            os.replace(tmp_path, str(self.session_cache_path))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        self._in_memory_cache = cache

    def load(self) -> Optional[SessionCache]:
        """Load session cache from disk."""
        if not self.session_cache_path.exists():
            return None
        try:
            with open(self.session_cache_path, "r") as f:
                data = json.load(f)
            data["ttl_seconds"] = self.ttl_seconds
            cache = SessionCache.from_dict(data)
            if cache.is_valid():
                self._in_memory_cache = cache
                return cache
            self.clear()
            return None
        except (json.JSONDecodeError, IOError, KeyError) as exc:
            self._logger.warning("Session cache corrupted: %s", exc)
            self.clear()
            return None
        except ValueError as exc:
            if "HMAC" in str(exc):
                self._logger.warning(
                    "Session cache invalidated: machine identifier changed (VM migration or container restart). "
                    "User will need to re-authenticate."
                )
            else:
                self._logger.warning("Session cache validation error: %s", exc)
            self.clear()
            return None

    def clear(self) -> bool:
        """Clear session cache file and in-memory cache."""
        if self.session_cache_path.exists():
            try:
                os.remove(self.session_cache_path)
                self._in_memory_cache = None
                return True
            except OSError:
                return False
        self._in_memory_cache = None
        return False

    def get_cached(self) -> Optional[SessionCache]:
        if self._in_memory_cache and self._in_memory_cache.is_valid():
            return self._in_memory_cache
        return None

    def should_refresh(self, cache: SessionCache) -> bool:
        return cache.should_refresh()

    def create_from_tenant(self, tenant: TenantContext, token: str) -> SessionCache:
        return SessionCache(
            tenant_id=tenant.tenant_id, tier=tenant.tier, role=tenant.role,
            license_key=tenant.license_key or token, features=tenant.features,
            expires_at=tenant.expires_at, cached_at=datetime.now(timezone.utc),
            ttl_seconds=self.ttl_seconds,
        )

    def to_session_info(
        self, cache: SessionCache, credentials_path: str, gateway_url: str,
        last_validated: Optional[datetime] = None, uses_secure_storage: bool = False,
    ) -> SessionInfo:
        return SessionInfo(
            tenant_id=cache.tenant_id, tier=cache.tier, authenticated=True,
            credentials_path=credentials_path, last_validated=last_validated,
            gateway_url=gateway_url, uses_secure_storage=uses_secure_storage,
        )

    def create_anonymous_session(
        self, credentials_path: str, gateway_url: str, uses_secure_storage: bool = False,
    ) -> SessionInfo:
        return SessionInfo(
            tenant_id="anonymous", tier="free", authenticated=False,
            credentials_path=credentials_path, gateway_url=gateway_url,
            uses_secure_storage=uses_secure_storage,
        )
