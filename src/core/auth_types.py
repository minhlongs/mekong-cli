# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS Auth Types - Dataclasses and Constants

Shared types for RaaS authentication module.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict


_logger = logging.getLogger(__name__)

@dataclass
class TenantContext:
    """
    Tenant context from validated credentials.

    Attributes:
        tenant_id: Unique tenant identifier
        tier: Service tier (free/trial/pro/enterprise)
        role: User role within tenant
        license_key: Optional license key for mk_ API keys
        expires_at: License expiry timestamp
        features: List of enabled features
        lang: Preferred language ("en" default, "vi" for VN users)
        business_type: VN OPC business category (bakery/fashion/service/etc.)
        city: VN city code (HCM/HN/DN) — informs market context
        industry: Industry vertical for agent specialization
    """

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
    """
    Result of credential validation.

    Attributes:
        valid: Whether credentials are valid
        tenant: Tenant context if valid
        error: Error message if invalid
        error_code: Machine-readable error code
    """

    valid: bool
    tenant: Optional[TenantContext] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class GatewayVerifyResult:
    """
    Result from lightweight /v1/verify endpoint.

    Attributes:
        valid: Whether gateway verification succeeded
        gateway_version: Gateway version string
        gateway_status: Gateway operational status
        requires_auth: Whether authentication is required
        error: Error message if failed
    """

    valid: bool
    gateway_version: Optional[str] = None
    gateway_status: Optional[str] = None
    requires_auth: bool = True
    error: Optional[str] = None


@dataclass
class SessionInfo:
    """
    Current session information.

    Attributes:
        tenant_id: Current tenant ID
        tier: Current tier
        authenticated: Whether session is authenticated
        credentials_path: Path to credentials file
        last_validated: Last validation timestamp
        gateway_url: Current gateway URL
        uses_secure_storage: Whether secure storage is enabled
    """

    tenant_id: str
    tier: str
    authenticated: bool
    credentials_path: str
    last_validated: Optional[datetime] = None
    gateway_url: Optional[str] = None
    uses_secure_storage: bool = False


@dataclass
class SessionCache:
    """
    Session cache with TTL support.

    Stored in ~/.mekong/session.json for cross-invocation caching.
    TTL: 5 minutes (300 seconds)
    Refresh buffer: 1 minute (60 seconds)

    Attributes:
        tenant_id: Cached tenant ID
        tier: Cached tier
        role: Cached role
        license_key: Cached license key
        features: Cached features list
        expires_at: License expiry timestamp
        cached_at: Cache creation timestamp
        ttl_seconds: Cache TTL in seconds
        refresh_token: Refresh token for future use
    """

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
        """Calculate session cache expiry time."""
        return self.cached_at + timedelta(seconds=self.ttl_seconds)

    @property
    def refresh_boundary(self) -> datetime:
        """Calculate when to start refresh (1 minute before expiry)."""
        return self.session_expires_at - timedelta(seconds=60)

    def is_valid(self) -> bool:
        """Check if cache is still valid (not expired)."""
        return datetime.now(timezone.utc) < self.session_expires_at

    def should_refresh(self) -> bool:
        """Check if we should refresh (within 1 minute of expiry)."""
        now = datetime.now(timezone.utc)
        return now >= self.refresh_boundary and now < self.session_expires_at

    def is_expired(self) -> bool:
        """Check if cache has expired."""
        return datetime.now(timezone.utc) >= self.session_expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary with HMAC-SHA256 signature."""
        payload = {
            "tenant_id": self.tenant_id,
            "tier": self.tier,
            "role": self.role,
            "license_key": self.license_key,
            "features": self.features,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cached_at": self.cached_at.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "refresh_token": self.refresh_token,
        }
        raw = json.dumps(payload, sort_keys=True).encode()
        payload["hmac"] = _compute_cache_hmac(raw)
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionCache":
        """Deserialize from dictionary, verifying HMAC first."""
        hmac_sig = data.pop("hmac", None)
        if hmac_sig:
            raw = json.dumps(data, sort_keys=True).encode()
            if not _verify_cache_hmac(raw, hmac_sig):
                raise ValueError("Session cache HMAC verification failed — rejecting")
        return cls(
            tenant_id=data["tenant_id"],
            tier=data["tier"],
            role=data["role"],
            license_key=data.get("license_key"),
            features=data.get("features", []),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            cached_at=datetime.fromisoformat(data["cached_at"]),
            ttl_seconds=data.get("ttl_seconds", 300),
            refresh_token=data.get("refresh_token"),
        )


# Module constants
_CACHE_HMAC_SALT = b"mekong-cli-session-cache-v1"


def _get_cache_hmac_key() -> tuple[bytes, str]:
    """Derive HMAC-SHA256 key from machine-specific entropy.

    Returns (key, source_label) so callers can identify which
    entropy source was used for logging.

    Sources (in priority order):
      1. /etc/machine-id
      2. /var/lib/dbus/machine-id
      3. os.uname().nodename
      4. "default" (fallback)
    """
    machine_id = ""
    source_label = "default"
    mid_paths = ["/etc/machine-id", "/var/lib/dbus/machine-id"]
    for p in mid_paths:
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
    key = hashlib.sha256(machine_id.encode() + _CACHE_HMAC_SALT).digest()
    return key, source_label


def _compute_cache_hmac(data: bytes) -> str:
    """Compute HMAC-SHA256 hex digest for session cache data."""
    key, _ = _get_cache_hmac_key()
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def _verify_cache_hmac(data: bytes, expected: str) -> bool:
    """Constant-time HMAC verification for session cache data.

    Logs a warning when the HMAC key source has changed (machine-id
    or hostname differs), indicating a VM migration or container
    restart rather than tampering.
    """
    current_key, current_source = _get_cache_hmac_key()
    computed = hmac.new(current_key, data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, expected):
        _logger.warning(
            "HMAC key mismatch: cache was signed with a different machine "
            "identifier (current source: %s). "
            "This typically happens after VM migration or container restart.",
            current_source,
        )
        return False
    return True


DEFAULT_GATEWAY_URL = "https://api.cashclaw.cc"
VERIFY_ENDPOINT = "/v1/verify"
VALIDATION_ENDPOINT_V1 = "/v1/auth/validate"
VALIDATION_ENDPOINT_V2 = "/v2/license/validate"
SESSION_TTL_SECONDS = 300  # 5 minutes
REFRESH_BUFFER_SECONDS = 60  # 1 minute before expiry

# Circuit breaker configuration
CIRCUIT_FAILURE_THRESHOLD = 3
CIRCUIT_RECOVERY_TIMEOUT = 60
