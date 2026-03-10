"""
API Key Manager — Generate, Validate, Revoke API Keys per Tenant

Condition C3 (API Bridge) Implementation:
- Generate API keys per tenant (RAAS_LICENSE_KEY)
- Validate API keys with rate limiting
- Revoke API keys on demand
- Integration with gateway mapping

Usage:
    from src.core.api_key_manager import ApiKeyManager

    manager = ApiKeyManager()
    key = manager.generate_key(tenant_id="tenant_123", tier="pro")
    is_valid = manager.validate_key(key.key_id)
    manager.revoke_key(key.key_id)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from enum import Enum

logger = __import__("logging").getLogger(__name__)


class KeyStatus(str, Enum):
    """API key lifecycle states."""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


@dataclass
class ApiKey:
    """API key data structure."""

    key_id: str  # Public identifier (e.g., mk_abc123...)
    key_secret: str  # Secret part (stored securely, never returned)
    tenant_id: str
    tier: str
    status: KeyStatus = KeyStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    last_used_at: Optional[str] = None
    rate_limit: int = 60  # requests per minute
    request_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) >= expiry
        except ValueError:
            return False

    @property
    def is_active(self) -> bool:
        """Check if key is active and usable."""
        return self.status == KeyStatus.ACTIVE and not self.is_expired

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until key expires."""
        if not self.expires_at:
            return None
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            delta = expiry - datetime.now(timezone.utc)
            return max(0, delta.days)
        except ValueError:
            return None

    def to_public_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary without secret."""
        data = asdict(self)
        data.pop("key_secret", None)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ApiKey:
        """Deserialize from dictionary."""
        return cls(
            key_id=data.get("key_id", ""),
            key_secret=data.get("key_secret", ""),
            tenant_id=data.get("tenant_id", ""),
            tier=data.get("tier", "free"),
            status=KeyStatus(data.get("status", "active")),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            expires_at=data.get("expires_at"),
            last_used_at=data.get("last_used_at"),
            rate_limit=data.get("rate_limit", 60),
            request_count=data.get("request_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ValidationResult:
    """Result of API key validation."""

    valid: bool
    key: Optional[ApiKey] = None
    tenant_id: Optional[str] = None
    tier: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    rate_limit_remaining: Optional[int] = None


@dataclass
class RateLimitState:
    """Rate limiting state for a key."""

    window_start: float
    request_count: int
    rate_limit: int


class ApiKeyManager:
    """
    Manager for API key generation, validation, and revocation.

    Storage: ~/.mekong/api_keys.json
    Rate limiting: In-memory sliding window
    """

    KEYS_FILE = "api_keys.json"
    RATE_LIMIT_WINDOW = 60  # 1 minute window

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".mekong"
        self.keys_path = self.config_dir / self.KEYS_FILE
        self._cache: Dict[str, ApiKey] = {}
        self._rate_limits: Dict[str, RateLimitState] = {}
        self._storage = self._get_secure_storage()

    def _get_secure_storage(self):
        """Get secure storage for encryption."""
        try:
            from src.auth.secure_storage import get_secure_storage
            return get_secure_storage()
        except ImportError:
            return None

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _generate_key_pair(self) -> tuple[str, str]:
        """
        Generate a new API key pair.

        Returns:
            (key_id, key_secret) tuple
            - key_id: Public identifier (mk_xxx)
            - key_secret: Secret part (never returned after creation)
        """
        # Create key_id (public, safe to share)
        key_id = "mk_" + secrets.token_urlsafe(24)

        # Create key_secret (never returned after creation)
        key_secret = secrets.token_urlsafe(48)

        return key_id, key_secret

    def _hash_key(self, key_secret: str) -> str:
        """Hash key secret for storage verification."""
        return hashlib.sha256(key_secret.encode()).hexdigest()

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data if storage available."""
        if self._storage:
            try:
                return self._storage.encrypt(data)
            except Exception as e:
                logger.debug("API key encrypt error: %s", e)
        # Fallback: base64 encode (not secure, but better than plaintext)
        return base64.b64encode(data.encode()).decode()

    def _decrypt(self, encrypted: str) -> str:
        """Decrypt sensitive data."""
        if self._storage:
            try:
                return self._storage.decrypt(encrypted)
            except Exception as e:
                logger.debug("API key decrypt error: %s", e)
        # Fallback: base64 decode
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except Exception as e:
            logger.debug("API key base64 decode error: %s", e)
            return encrypted

    def generate_key(
        self,
        tenant_id: str,
        tier: str = "free",
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApiKey:
        """
        Generate a new API key for a tenant.

        Args:
            tenant_id: Unique tenant identifier
            tier: Tier name (free, pro, enterprise)
            expires_in_days: Days until key expires (None = never)
            rate_limit: Requests per minute (default by tier)
            metadata: Additional metadata to store

        Returns:
            ApiKey with key_id and key_secret (return key_secret ONCE!)
        """
        # Generate key pair
        key_id, key_secret = self._generate_key_pair()

        # Set expiry
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat()

        # Set rate limit by tier
        if rate_limit is None:
            rate_limits = {"free": 30, "pro": 100, "enterprise": 500, "unlimited": 9999}
            rate_limit = rate_limits.get(tier.lower(), 60)

        # Create API key
        key = ApiKey(
            key_id=key_id,
            key_secret=key_secret,
            tenant_id=tenant_id,
            tier=tier,
            expires_at=expires_at,
            rate_limit=rate_limit,
            metadata=metadata or {},
        )

        # Encrypt secret before storage
        key.key_secret = self._encrypt(key_secret)

        # Save key
        self._save_key(key)

        logger.info("Generated API key for tenant %s (tier: %s)", tenant_id, tier)

        return key

    def validate_key(
        self,
        key_id: str,
        key_secret: Optional[str] = None,
        check_rate_limit: bool = True,
    ) -> ValidationResult:
        """
        Validate an API key.

        Args:
            key_id: Public key identifier
            key_secret: Secret part (optional, for additional verification)
            check_rate_limit: Whether to check rate limiting

        Returns:
            ValidationResult with validation status and tenant info
        """
        # Load key
        key = self._load_key(key_id)

        if not key:
            return ValidationResult(
                valid=False,
                error="API key not found",
                error_code="KEY_NOT_FOUND",
            )

        # Check status
        if key.status == KeyStatus.REVOKED:
            return ValidationResult(
                valid=False,
                error="API key has been revoked",
                error_code="KEY_REVOKED",
            )

        if key.status == KeyStatus.SUSPENDED:
            return ValidationResult(
                valid=False,
                error="API key has been suspended",
                error_code="KEY_SUSPENDED",
            )

        # Check expiry
        if key.is_expired:
            key.status = KeyStatus.EXPIRED
            self._save_key(key)
            return ValidationResult(
                valid=False,
                error="API key has expired",
                error_code="KEY_EXPIRED",
            )

        # Verify secret if provided
        if key_secret:
            try:
                stored_secret = self._decrypt(key.key_secret)
                if not hmac.compare_digest(stored_secret, key_secret):
                    return ValidationResult(
                        valid=False,
                        error="Invalid API key secret",
                        error_code="INVALID_SECRET",
                    )
            except Exception as e:
                logger.warning("API key secret verification error: %s", e)
                return ValidationResult(
                    valid=False,
                    error="Failed to verify API key secret",
                    error_code="VERIFICATION_ERROR",
                )

        # Check rate limit
        rate_limit_remaining = None
        if check_rate_limit:
            within_limit, remaining = self._check_rate_limit(key_id, key.rate_limit)
            rate_limit_remaining = remaining
            if not within_limit:
                return ValidationResult(
                    valid=False,
                    error="Rate limit exceeded. Try again later.",
                    error_code="RATE_LIMIT_EXCEEDED",
                    rate_limit_remaining=0,
                )

        # Update last used timestamp
        key.last_used_at = datetime.now(timezone.utc).isoformat()
        key.request_count += 1
        self._save_key(key)

        # Update rate limit state
        self._increment_rate_limit(key_id, key.rate_limit)

        return ValidationResult(
            valid=True,
            key=key,
            tenant_id=key.tenant_id,
            tier=key.tier,
            rate_limit_remaining=rate_limit_remaining,
        )

    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: Public key identifier

        Returns:
            True if revocation successful
        """
        key = self._load_key(key_id)

        if not key:
            return False

        key.status = KeyStatus.REVOKED
        self._save_key(key)

        logger.info("Revoked API key %s for tenant %s", key_id, key.tenant_id)

        return True

    def suspend_key(self, key_id: str) -> bool:
        """
        Suspend an API key temporarily.

        Args:
            key_id: Public key identifier

        Returns:
            True if suspension successful
        """
        key = self._load_key(key_id)

        if not key:
            return False

        key.status = KeyStatus.SUSPENDED
        self._save_key(key)

        logger.info("Suspended API key %s for tenant %s", key_id, key.tenant_id)

        return True

    def reactivate_key(self, key_id: str) -> bool:
        """
        Reactivate a suspended API key.

        Args:
            key_id: Public key identifier

        Returns:
            True if reactivation successful
        """
        key = self._load_key(key_id)

        if not key:
            return False

        key.status = KeyStatus.ACTIVE
        self._save_key(key)

        logger.info("Reactivated API key %s for tenant %s", key_id, key.tenant_id)

        return True

    def get_keys_for_tenant(self, tenant_id: str) -> List[ApiKey]:
        """
        Get all API keys for a tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of ApiKey (without secrets)
        """
        keys_data = self._load_all_keys()
        return [
            key for key in keys_data.values()
            if key.tenant_id == tenant_id
        ]

    def get_key(self, key_id: str) -> Optional[ApiKey]:
        """
        Get a single API key by ID.

        Args:
            key_id: Public key identifier

        Returns:
            ApiKey without secret, or None if not found
        """
        key = self._load_key(key_id)
        if key:
            key.key_secret = "***REDACTED***"
        return key

    def delete_key(self, key_id: str) -> bool:
        """
        Permanently delete an API key.

        Args:
            key_id: Public key identifier

        Returns:
            True if deletion successful
        """
        keys_data = self._load_all_keys()

        if key_id not in keys_data:
            return False

        del keys_data[key_id]
        self._save_all_keys(keys_data)
        self._cache.pop(key_id, None)

        logger.info("Deleted API key %s", key_id)

        return True

    def _check_rate_limit(self, key_id: str, rate_limit: int) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            key_id: API key identifier
            rate_limit: Requests per minute allowed

        Returns:
            (within_limit, remaining_requests) tuple
        """
        now = time.time()
        state = self._rate_limits.get(key_id)

        if not state or (now - state.window_start) >= self.RATE_LIMIT_WINDOW:
            # New window
            return True, rate_limit

        remaining = max(0, rate_limit - state.request_count)
        return state.request_count < rate_limit, remaining

    def _increment_rate_limit(self, key_id: str, rate_limit: int) -> None:
        """Increment rate limit counter."""
        now = time.time()
        state = self._rate_limits.get(key_id)

        if not state or (now - state.window_start) >= self.RATE_LIMIT_WINDOW:
            # New window
            self._rate_limits[key_id] = RateLimitState(
                window_start=now,
                request_count=1,
                rate_limit=rate_limit,
            )
        else:
            state.request_count += 1

    def _load_key(self, key_id: str) -> Optional[ApiKey]:
        """Load a single API key from storage."""
        # Check cache first
        if key_id in self._cache:
            return self._cache[key_id]

        # Load from file
        keys_data = self._load_all_keys()
        key = keys_data.get(key_id)

        if key:
            self._cache[key_id] = key

        return key

    def _load_all_keys(self) -> Dict[str, ApiKey]:
        """Load all API keys from storage."""
        if not self.keys_path.exists():
            return {}

        try:
            import json
            with open(self.keys_path, "r") as f:
                data = json.load(f)

            return {k: ApiKey.from_dict(v) for k, v in data.items()}

        except Exception as e:
            logger.warning("Failed to load API keys: %s", e)
            return {}

    def _save_key(self, key: ApiKey) -> None:
        """Save a single API key to storage."""
        keys_data = self._load_all_keys()
        keys_data[key.key_id] = key
        self._save_all_keys(keys_data)

        # Update cache
        self._cache[key.key_id] = key

    def _save_all_keys(self, keys_data: Dict[str, ApiKey]) -> None:
        """Save all API keys to storage."""
        self._ensure_config_dir()

        try:
            import json
            data = {k: v.to_public_dict() for k, v in keys_data.items()}

            with open(self.keys_path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error("Failed to save API keys: %s", e)

    def clear_all_keys(self) -> bool:
        """
        Clear all stored API keys.

        Returns:
            True if clear successful
        """
        try:
            if self.keys_path.exists():
                self.keys_path.unlink()
            self._cache.clear()
            self._rate_limits.clear()
            return True
        except Exception as e:
            logger.warning("API key clear error: %s", e)
            return False


# Global instance
_api_key_manager: Optional[ApiKeyManager] = None


def get_api_key_manager() -> ApiKeyManager:
    """Get global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = ApiKeyManager()
    return _api_key_manager


def generate_api_key(
    tenant_id: str,
    tier: str = "free",
    expires_in_days: Optional[int] = None,
) -> ApiKey:
    """Generate a new API key."""
    return get_api_key_manager().generate_key(tenant_id, tier, expires_in_days)


def validate_api_key(key_id: str, key_secret: Optional[str] = None) -> ValidationResult:
    """Validate an API key."""
    return get_api_key_manager().validate_key(key_id, key_secret)


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key."""
    return get_api_key_manager().revoke_key(key_id)


__all__ = [
    "ApiKey",
    "ApiKeyManager",
    "KeyStatus",
    "ValidationResult",
    "get_api_key_manager",
    "generate_api_key",
    "validate_api_key",
    "revoke_api_key",
]
