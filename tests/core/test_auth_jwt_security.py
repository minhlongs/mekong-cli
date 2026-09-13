"""Security tests for JWT authentication and session management.

Tests REAL logic in src/core/auth_jwt.py and src/core/auth_session.py.
External I/O (filesystem) is mocked where necessary.
"""

from __future__ import annotations

import base64
import json
import os
import tempfile
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


from src.core.auth_jwt import (
    decode_jwt,
    validate_jwt_expiry,
    extract_tenant_from_jwt,
    validate_jwt_format,
)
from src.core.auth_types import TenantContext, SessionCache
from src.core.auth_session import SessionManager


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_jwt(payload: dict, header: dict | None = None) -> str:
    """Build a minimal (unsigned) JWT for testing."""
    if header is None:
        header = {"alg": "HS256", "typ": "JWT"}

    def _b64(obj: dict) -> str:
        raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    h = _b64(header)
    p = _b64(payload)
    sig = "fakesignature"
    return f"{h}.{p}.{sig}"


def _future_exp(seconds: int = 3600) -> int:
    """Return a future Unix timestamp."""
    return int(time.time()) + seconds


def _past_exp(seconds: int = 3600) -> int:
    """Return a past Unix timestamp."""
    return int(time.time()) - seconds


# ═══════════════════════════════════════════════════════════════════════════════
#  decode_jwt
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecodeJwt:
    """decode_jwt: base64url decoding without signature verification."""

    def test_valid_jwt_returns_payload(self):
        payload = {"sub": "user-123", "exp": _future_exp()}
        token = _make_jwt(payload)
        result = decode_jwt(token)
        assert result is not None
        assert result["sub"] == "user-123"

    def test_returns_none_for_non_jwt_string(self):
        assert decode_jwt("not-a-jwt") is None

    def test_returns_none_for_two_part_token(self):
        assert decode_jwt("header.payload") is None

    def test_returns_none_for_empty_string(self):
        assert decode_jwt("") is None

    def test_returns_none_for_invalid_base64(self):
        assert decode_jwt("!!!.!!!.!!!") is None

    def test_returns_none_for_invalid_json_payload(self):
        # Manually build token with non-JSON payload
        h = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        p = base64.urlsafe_b64encode(b"NOT_JSON").rstrip(b"=").decode()
        token = f"{h}.{p}.sig"
        assert decode_jwt(token) is None

    def test_handles_padding_correctly(self):
        # Payloads of various lengths to exercise padding logic
        for extra_chars in range(4):
            payload = {"k": "v" * extra_chars, "exp": _future_exp()}
            token = _make_jwt(payload)
            result = decode_jwt(token)
            assert result is not None

    def test_all_payload_fields_preserved(self):
        payload = {
            "sub": "u1",
            "exp": _future_exp(),
            "tenant_id": "t1",
            "app_metadata": {"role": "pro"},
        }
        token = _make_jwt(payload)
        result = decode_jwt(token)
        assert result["tenant_id"] == "t1"
        assert result["app_metadata"]["role"] == "pro"


# ═══════════════════════════════════════════════════════════════════════════════
#  validate_jwt_expiry
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateJwtExpiry:
    """validate_jwt_expiry: reject expired / missing exp claims."""

    def test_future_exp_is_valid(self):
        payload = {"exp": _future_exp(3600)}
        assert validate_jwt_expiry(payload) is True

    def test_past_exp_is_invalid(self):
        payload = {"exp": _past_exp(3600)}
        assert validate_jwt_expiry(payload) is False

    def test_exp_exactly_now_is_invalid(self):
        # exp == current time → token has already expired
        payload = {"exp": int(time.time()) - 1}
        assert validate_jwt_expiry(payload) is False

    def test_missing_exp_is_invalid(self):
        assert validate_jwt_expiry({}) is False

    def test_none_exp_is_invalid(self):
        assert validate_jwt_expiry({"exp": None}) is False

    def test_zero_exp_is_invalid(self):
        assert validate_jwt_expiry({"exp": 0}) is False


# ═══════════════════════════════════════════════════════════════════════════════
#  extract_tenant_from_jwt
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtractTenantFromJwt:
    """extract_tenant_from_jwt: tenant context extraction from JWT claims."""

    def test_top_level_tenant_id(self):
        payload = {"tenant_id": "acme", "exp": _future_exp()}
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.tenant_id == "acme"

    def test_app_metadata_tenant_id(self):
        payload = {
            "sub": "user-abc",
            "app_metadata": {"tenant_id": "nestled-tenant"},
            "exp": _future_exp(),
        }
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.tenant_id == "nestled-tenant"

    def test_falls_back_to_sub_when_no_tenant(self):
        payload = {"sub": "sub-user-id", "exp": _future_exp()}
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.tenant_id == "sub-user-id"

    def test_falls_back_to_unknown(self):
        ctx = extract_tenant_from_jwt({})
        assert ctx.tenant_id == "unknown"

    def test_top_level_role(self):
        payload = {"role": "pro", "exp": _future_exp()}
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.tier == "pro"
        assert ctx.role == "pro"

    def test_app_metadata_role(self):
        payload = {
            "app_metadata": {"role": "enterprise"},
            "exp": _future_exp(),
        }
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.tier == "enterprise"

    def test_defaults_to_free_tier(self):
        ctx = extract_tenant_from_jwt({"sub": "u"})
        assert ctx.tier == "free"

    def test_expires_at_populated(self):
        exp = _future_exp(7200)
        payload = {"sub": "u", "exp": exp}
        ctx = extract_tenant_from_jwt(payload)
        assert ctx.expires_at is not None
        assert ctx.expires_at.tzinfo is not None

    def test_expires_at_none_when_no_exp(self):
        ctx = extract_tenant_from_jwt({"sub": "u"})
        assert ctx.expires_at is None

    def test_returns_tenant_context_type(self):
        payload = {"sub": "u", "exp": _future_exp()}
        ctx = extract_tenant_from_jwt(payload)
        assert isinstance(ctx, TenantContext)


# ═══════════════════════════════════════════════════════════════════════════════
#  validate_jwt_format
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateJwtFormat:
    """validate_jwt_format: combined format + expiry check."""

    def test_valid_token_returns_true_and_payload(self):
        payload = {"sub": "u1", "exp": _future_exp()}
        token = _make_jwt(payload)
        is_valid, error, decoded = validate_jwt_format(token)
        assert is_valid is True
        assert error is None
        assert decoded is not None
        assert decoded["sub"] == "u1"

    def test_missing_dot_returns_invalid_format(self):
        is_valid, error, decoded = validate_jwt_format("nodots")
        assert is_valid is False
        assert "Invalid JWT format" in error
        assert decoded is None

    def test_malformed_base64_returns_invalid_format(self):
        is_valid, error, decoded = validate_jwt_format("aaa.!!!.bbb")
        assert is_valid is False
        assert decoded is None

    def test_expired_token_returns_token_expired(self):
        payload = {"sub": "u1", "exp": _past_exp()}
        token = _make_jwt(payload)
        is_valid, error, decoded = validate_jwt_format(token)
        assert is_valid is False
        assert "expired" in error.lower()
        assert decoded is None

    def test_valid_payload_returned_in_tuple(self):
        payload = {"sub": "u2", "tenant_id": "t2", "exp": _future_exp()}
        token = _make_jwt(payload)
        is_valid, error, decoded = validate_jwt_format(token)
        assert is_valid
        assert decoded["tenant_id"] == "t2"

    def test_tampered_payload_with_invalid_base64_fails(self):
        # Build valid token, tamper middle part
        token = _make_jwt({"sub": "u", "exp": _future_exp()})
        parts = token.split(".")
        parts[1] = "!!TAMPERED!!"
        tampered = ".".join(parts)
        is_valid, error, decoded = validate_jwt_format(tampered)
        assert is_valid is False
        assert decoded is None


# ═══════════════════════════════════════════════════════════════════════════════
#  SessionManager
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionManager:
    """SessionManager: TTL, persistence, clear, refresh logic."""

    def setup_method(self):
        # Use a temp dir so tests don't pollute real ~/.mekong/
        self.tmp = tempfile.mkdtemp()
        self.cache_path = os.path.join(self.tmp, "session.json")
        self.sm = SessionManager(cache_path=self.cache_path, ttl_seconds=300)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_cache(self, ttl_seconds: int = 300) -> SessionCache:
        return SessionCache(
            tenant_id="tenant-1",
            tier="pro",
            role="pro",
            ttl_seconds=ttl_seconds,
            cached_at=datetime.now(timezone.utc),
        )

    # --- save / load ---

    def test_save_and_load_round_trip(self):
        cache = self._make_cache()
        self.sm.save(cache)
        loaded = self.sm.load()
        assert loaded is not None
        assert loaded.tenant_id == "tenant-1"
        assert loaded.tier == "pro"

    def test_load_returns_none_when_no_file(self):
        assert self.sm.load() is None

    def test_load_returns_none_for_expired_cache(self):
        # SessionManager.load() overrides ttl_seconds from its own config.
        # Use a manager with ttl=1 and a cache cached 10 s ago — clearly expired.
        sm_tiny = SessionManager(cache_path=self.cache_path, ttl_seconds=1)
        cache = SessionCache(
            tenant_id="t",
            tier="free",
            role="free",
            ttl_seconds=1,
            cached_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        sm_tiny.save(cache)
        assert sm_tiny.load() is None

    def test_load_clears_expired_cache_file(self):
        sm_tiny = SessionManager(cache_path=self.cache_path, ttl_seconds=1)
        cache = SessionCache(
            tenant_id="t",
            tier="free",
            role="free",
            ttl_seconds=1,
            cached_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        sm_tiny.save(cache)
        sm_tiny.load()
        assert not Path(self.cache_path).exists()

    def test_load_returns_none_for_corrupted_json(self):
        Path(self.cache_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.cache_path).write_text("NOT JSON")
        assert self.sm.load() is None

    def test_save_sets_secure_permissions(self):
        cache = self._make_cache()
        self.sm.save(cache)
        mode = os.stat(self.cache_path).st_mode & 0o777
        assert mode == 0o600

    # --- clear ---

    def test_clear_removes_file(self):
        cache = self._make_cache()
        self.sm.save(cache)
        result = self.sm.clear()
        assert result is True
        assert not Path(self.cache_path).exists()

    def test_clear_returns_false_when_no_file(self):
        result = self.sm.clear()
        assert result is False

    def test_clear_invalidates_in_memory_cache(self):
        cache = self._make_cache()
        self.sm.save(cache)
        self.sm.clear()
        assert self.sm.get_cached() is None

    # --- get_cached ---

    def test_get_cached_returns_none_initially(self):
        assert self.sm.get_cached() is None

    def test_get_cached_after_save(self):
        cache = self._make_cache()
        self.sm.save(cache)
        assert self.sm.get_cached() is not None

    # --- should_refresh ---

    def test_should_refresh_when_near_expiry(self):
        # Cache expires in 30 s — within 60 s refresh buffer
        cache = SessionCache(
            tenant_id="t",
            tier="pro",
            role="pro",
            ttl_seconds=30,
            cached_at=datetime.now(timezone.utc),
        )
        assert self.sm.should_refresh(cache) is True

    def test_should_not_refresh_when_fresh(self):
        cache = SessionCache(
            tenant_id="t",
            tier="pro",
            role="pro",
            ttl_seconds=300,
            cached_at=datetime.now(timezone.utc),
        )
        assert self.sm.should_refresh(cache) is False

    # --- create_from_tenant ---

    def test_create_from_tenant_populates_fields(self):
        tenant = TenantContext(
            tenant_id="acme",
            tier="enterprise",
            role="admin",
            license_key="mk_abc",
        )
        cache = self.sm.create_from_tenant(tenant, "mk_abc")
        assert cache.tenant_id == "acme"
        assert cache.tier == "enterprise"
        assert cache.license_key == "mk_abc"

    # --- anonymous session ---

    def test_create_anonymous_session(self):
        info = self.sm.create_anonymous_session(
            credentials_path="/fake/path",
            gateway_url="https://gateway.example.com",
        )
        assert info.authenticated is False
        assert info.tenant_id == "anonymous"
        assert info.tier == "free"

    # --- to_session_info ---

    def test_to_session_info_returns_authenticated(self):
        cache = self._make_cache()
        self.sm.save(cache)
        info = self.sm.to_session_info(
            cache,
            credentials_path="/fake",
            gateway_url="https://gw.example.com",
        )
        assert info.authenticated is True
        assert info.tenant_id == "tenant-1"


# ═══════════════════════════════════════════════════════════════════════════════
#  SessionCache dataclass
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionCacheDataclass:
    """Direct tests of SessionCache helper methods."""

    def test_is_valid_when_fresh(self):
        cache = SessionCache(
            tenant_id="t", tier="pro", role="pro",
            ttl_seconds=300,
            cached_at=datetime.now(timezone.utc),
        )
        assert cache.is_valid() is True

    def test_is_expired_when_old(self):
        cache = SessionCache(
            tenant_id="t", tier="pro", role="pro",
            ttl_seconds=1,
            cached_at=datetime.now(timezone.utc) - timedelta(seconds=10),
        )
        assert cache.is_expired() is True
        assert cache.is_valid() is False

    def test_to_dict_and_from_dict_round_trip(self):
        now = datetime.now(timezone.utc)
        cache = SessionCache(
            tenant_id="t1",
            tier="pro",
            role="admin",
            license_key="mk_test",
            features=["feature_a"],
            cached_at=now,
            ttl_seconds=300,
        )
        d = cache.to_dict()
        restored = SessionCache.from_dict(d)
        assert restored.tenant_id == "t1"
        assert restored.tier == "pro"
        assert restored.features == ["feature_a"]
        assert restored.license_key == "mk_test"

    def test_refresh_boundary_is_before_expiry(self):
        cache = SessionCache(
            tenant_id="t", tier="pro", role="pro",
            ttl_seconds=300,
            cached_at=datetime.now(timezone.utc),
        )
        assert cache.refresh_boundary < cache.session_expires_at

    def test_should_refresh_false_when_just_created(self):
        cache = SessionCache(
            tenant_id="t", tier="pro", role="pro",
            ttl_seconds=300,
            cached_at=datetime.now(timezone.utc),
        )
        assert cache.should_refresh() is False

    def test_from_dict_handles_missing_optional_fields(self):
        data = {
            "tenant_id": "t",
            "tier": "free",
            "role": "free",
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        cache = SessionCache.from_dict(data)
        assert cache.license_key is None
        assert cache.features == []
        assert cache.expires_at is None
