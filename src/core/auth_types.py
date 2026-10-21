# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Auth Types - Dataclasses and Constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Dict, Optional

_logger = logging.getLogger(__name__)


@dataclass
class TenantContext:
    """Tenant context from validated credentials."""
    tenant_id: str
    tier: str
    role: str
    license_key: Optional[str] = None
    expires_at: Optional[datetime] = None
    features: list[str] = field(default_factory=list)
    lang: str = "en"
    business_type: Optional[str] = None
    city: Optional[str] = None
    industry: Optional[str] = None

    @property
    def namespace(self) -> str:
        """KV store namespace prefix for tenant isolation."""
        return f"tenant_{self.tenant_id}"


@dataclass
class AuthResult:
    """Result of credential validation."""
    valid: bool
    tenant: Optional[TenantContext] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class GatewayVerifyResult:
    """Result from lightweight /v1/verify endpoint."""
    valid: bool
    gateway_version: Optional[str] = None
    gateway_status: Optional[str] = None
    requires_auth: bool = True
    error: Optional[str] = None


@dataclass
class SessionInfo:
    """Current session information."""
    tenant_id: str
    tier: str
    authenticated: bool
    credentials_path: str
    last_validated: Optional[datetime] = None
    gateway_url: Optional[str] = None
    uses_secure_storage: bool = False


@dataclass
class SessionCache:
    """Session cache with TTL support stored in ~/.mekong/session.json."""
    tenant_id: str
    tier: str
    role: str
    license_key: Optional[str] = None
    features: list[str] = field(default_factory=list)
    expires_at: Optional[datetime] = None
    cached_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 300
    refresh_token: Optional[str] = None

    @property
    def session_expires_at(self) -> datetime:
        return self.cached_at + timedelta(seconds=self.ttl_seconds)

    @property
    def refresh_boundary(self) -> datetime:
        return self.session_expires_at - timedelta(seconds=60)

    def is_valid(self) -> bool:
        return datetime.now(timezone.utc) < self.session_expires_at

    def should_refresh(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.refresh_boundary <= now < self.session_expires_at

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.session_expires_at

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "tenant_id": self.tenant_id, "tier": self.tier, "role": self.role,
            "license_key": self.license_key, "features": self.features,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cached_at": self.cached_at.isoformat(), "ttl_seconds": self.ttl_seconds,
            "refresh_token": self.refresh_token,
        }
        raw = json.dumps(payload, sort_keys=True).encode()
        payload["hmac"] = _compute_cache_hmac(raw)
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCache":
        hmac_sig = data.pop("hmac", None)
        if hmac_sig:
            raw = json.dumps(data, sort_keys=True).encode()
            if not _verify_cache_hmac(raw, hmac_sig):
                raise ValueError("Session cache HMAC verification failed — rejecting")
        return cls(
            tenant_id=data["tenant_id"], tier=data["tier"], role=data["role"],
            license_key=data.get("license_key"), features=data.get("features", []),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            cached_at=datetime.fromisoformat(data["cached_at"]),
            ttl_seconds=data.get("ttl_seconds", 300), refresh_token=data.get("refresh_token"),
        )


_CACHE_HMAC_SALT = b"mekong-cli-session-cache-v1"


def _get_cache_hmac_key() -> tuple[bytes, str]:
    """Derive HMAC-SHA256 key from machine-specific entropy."""
    machine_id = ""
    source_label = "default"
    for p in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        try:
            with open(p) as f:
                machine_id = f.read().strip()
            if machine_id:
                source_label = p
                break
        except OSError:
            continue
    if not machine_id:
        machine_id = os.uname().nodename if hasattr(os, "uname") else "default"
        source_label = "nodename"
    return hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest(), source_label


def _compute_cache_hmac(data: bytes) -> str:
    key, _ = _get_cache_hmac_key()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def _verify_cache_hmac(data: bytes, expected: str) -> bool:
    current_key, current_source = _get_cache_hmac_key()
    computed = hmac.new(current_key, data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, expected):
        _logger.warning(
            "HMAC key mismatch: cache was signed with a different machine identifier (current source: %s).",
            current_source,
        )
        return False
    return True


DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"
VERIFY_ENDPOINT = "/v1/verify"
VALIDATION_ENDPOINT_V1 = "/v1/auth/validate"
VALIDATION_ENDPOINT_V2 = "/v2/license/validate"
SESSION_TTL_SECONDS = 300
REFRESH_BUFFER_SECONDS = 60
CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT = 60
