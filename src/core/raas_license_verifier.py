"""Cryptographic RAAS_LICENSE_KEY verifier and signer (Step 11b).

Stdlib-pure implementation (< 185 LOC) satisfying tests/test_core_boundary.py.
Signs and verifies HMAC-SHA256 tokens for MEKONG-RAAS-v1 and SOPHIA-RAAS-v1.
"""
from __future__ import annotations

import base64
from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

ALLOWED_PREFIXES: tuple[str, ...] = ("MEKONG-RAAS-v1", "SOPHIA-RAAS-v1")
_DEFAULT_TEST_SECRET = "mekong-raas-test-hmac-sha256-secret-baseline-2026"


class CanonicalLicenseTier(str, Enum):
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"
    MASTER = "MASTER"


TIER_FEATURES: dict[CanonicalLicenseTier, tuple[str, ...]] = {
    CanonicalLicenseTier.BASIC: ("cli:basic", "cli:cook", "byok:standard"),
    CanonicalLicenseTier.PREMIUM: (
        "cli:basic", "cli:cook", "byok:standard", "cloud:queue", "telemetry:sync"
    ),
    CanonicalLicenseTier.ENTERPRISE: (
        "cli:basic", "cli:cook", "byok:standard", "cloud:queue", "telemetry:sync",
        "rbac:multi_tenant", "audit:ledger", "vault:kms"
    ),
    CanonicalLicenseTier.MASTER: (
        "cli:basic", "cli:cook", "byok:standard", "cloud:queue", "telemetry:sync",
        "rbac:multi_tenant", "audit:ledger", "vault:kms", "whitelabel:portal",
        "daemon:always_on", "unlimited:mcu"
    ),
}

_TIER_NORMALIZATION: dict[str, CanonicalLicenseTier] = {
    "basic": CanonicalLicenseTier.BASIC,
    "starter": CanonicalLicenseTier.BASIC,
    "starter_vn": CanonicalLicenseTier.BASIC,
    "trial": CanonicalLicenseTier.BASIC,
    "free": CanonicalLicenseTier.BASIC,
    "premium": CanonicalLicenseTier.PREMIUM,
    "growth": CanonicalLicenseTier.PREMIUM,
    "growth_vn": CanonicalLicenseTier.PREMIUM,
    "pro": CanonicalLicenseTier.PREMIUM,
    "pro_vn": CanonicalLicenseTier.PREMIUM,
    "team": CanonicalLicenseTier.PREMIUM,
    "enterprise": CanonicalLicenseTier.ENTERPRISE,
    "enterprise_plus": CanonicalLicenseTier.ENTERPRISE,
    "master": CanonicalLicenseTier.MASTER,
    "master_vn": CanonicalLicenseTier.MASTER,
}


def normalize_commercial_tier(raw: str) -> CanonicalLicenseTier:
    key = raw.strip().lower()
    return _TIER_NORMALIZATION.get(key, CanonicalLicenseTier.BASIC)


def _resolve_secret(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    env_secret = os.getenv("RAAS_LICENSE_SECRET") or os.getenv("JWT_SECRET") or os.getenv("MEKONG_JWT_SECRET")
    if env_secret:
        return env_secret
    # Only allow test secret fallback when explicitly running under pytest
    if os.getenv("PYTEST_CURRENT_TEST"):
        return _DEFAULT_TEST_SECRET
    raise RuntimeError("RAAS_LICENSE_SECRET must be configured in production")


@dataclass(frozen=True)
class LicensePayload:
    tenant_id: str
    tier: str
    issued_at: int
    expires_at: int
    features: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LicenseVerificationResult:
    valid: bool
    tier: Optional[CanonicalLicenseTier] = None
    tenant_id: Optional[str] = None
    expires_at: Optional[int] = None
    features: tuple[str, ...] = ()
    error: Optional[str] = None


def sign_license_key(
    tenant_id: str,
    tier: str | CanonicalLicenseTier,
    expires_in_days: int = 30,
    secret: Optional[str] = None,
    prefix: str = "MEKONG-RAAS-v1",
) -> str:
    if prefix not in ALLOWED_PREFIXES:
        raise ValueError(f"Unsupported prefix '{prefix}'. Allowed: {ALLOWED_PREFIXES}")
    norm_tier = tier if isinstance(tier, CanonicalLicenseTier) else normalize_commercial_tier(tier)
    now = int(time.time())
    payload = {
        "tenant_id": tenant_id,
        "tier": norm_tier.value,
        "issued_at": now,
        "expires_at": now + (expires_in_days * 86400),
        "features": list(TIER_FEATURES[norm_tier]),
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_raw).decode("ascii").rstrip("=")
    signing_input = f"{prefix}.{payload_b64}".encode("utf-8")
    key = _resolve_secret(secret).encode("utf-8")
    sig = hmac.new(key, signing_input, hashlib.sha256).hexdigest()
    return f"{prefix}.{payload_b64}.{sig}"


def verify_license_key(
    token: str,
    secret: Optional[str] = None,
    now: Optional[int] = None,
) -> LicenseVerificationResult:
    if not token or not isinstance(token, str):
        return LicenseVerificationResult(valid=False, error="empty_token")
    parts = token.strip().split(".")
    if len(parts) != 3:
        return LicenseVerificationResult(valid=False, error="invalid_token_format")
    prefix, payload_b64, sig = parts
    if prefix not in ALLOWED_PREFIXES:
        return LicenseVerificationResult(valid=False, error=f"invalid_prefix_{prefix}")
    try:
        key = _resolve_secret(secret).encode("utf-8")
    except RuntimeError as exc:
        return LicenseVerificationResult(valid=False, error=str(exc))
    signing_input = f"{prefix}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(key, signing_input, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return LicenseVerificationResult(valid=False, error="signature_mismatch")
    padding = "=" * (-len(payload_b64) % 4)
    try:
        raw_bytes = base64.urlsafe_b64decode(f"{payload_b64}{padding}")
        data = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        return LicenseVerificationResult(valid=False, error="malformed_payload")
    current_ts = now if now is not None else int(time.time())
    exp = int(data.get("expires_at", 0))
    if current_ts >= exp:
        return LicenseVerificationResult(valid=False, error="license_expired")
    raw_tier = str(data.get("tier", "BASIC"))
    tier_enum = normalize_commercial_tier(raw_tier)
    features = tuple(data.get("features", TIER_FEATURES[tier_enum]))
    return LicenseVerificationResult(
        valid=True,
        tier=tier_enum,
        tenant_id=str(data.get("tenant_id", "")),
        expires_at=exp,
        features=features,
    )
