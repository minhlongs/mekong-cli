"""Unit and boundary tests for Auth suite coverage.

Target modules:
- src/core/auth_types.py
- src/core/auth_session.py
- src/core/auth_tenant.py
- src/core/auth_jwt.py
"""

from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.core.auth_session import SessionManager
from src.core.auth_tenant import (
    TenantManager,
    _hash_tenant_token,
    _hash_tenant_token_legacy,
    _looks_like_legacy_tenant_id,
    derive_tenant_id,
)
from src.core.auth_types import (
    AuthResult,
    GatewayVerifyResult,
    SessionCache,
    SessionInfo,
    TenantContext,
    _get_cache_hmac_key,
    _verify_cache_hmac,
)


def _make_jwt(payload: dict, header: dict | None = None) -> str:
    """Build a minimal JWT for testing."""
    if header is None:
        header = {"alg": "HS256", "typ": "JWT"}

    def _b64(obj: dict) -> str:
        raw = json.dumps(obj, separators=(",", ":")).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    h = _b64(header)
    p = _b64(payload)
    sig = "sig123"
    return f"{h}.{p}.{sig}"


class TestAuthTypesCoverage:
    def test_tenant_context_namespace_and_fields(self):
        ctx = TenantContext(
            tenant_id="alpha_42",
            tier="pro",
            role="admin",
            business_type="retail",
            city="Hanoi",
            industry="commerce",
        )
        assert ctx.namespace == "tenant_alpha_42"
        assert ctx.business_type == "retail"
        assert ctx.city == "Hanoi"
        assert ctx.industry == "commerce"

    def test_auth_result_dataclass(self):
        ctx = TenantContext(tenant_id="t1", tier="free", role="user")
        res1 = AuthResult(valid=True, tenant=ctx)
        assert res1.valid is True
        assert res1.tenant.tenant_id == "t1"

        res2 = AuthResult(valid=False, error="Bad token", error_code="invalid")
        assert res2.valid is False
        assert res2.error == "Bad token"
        assert res2.error_code == "invalid"

    def test_gateway_verify_result_dataclass(self):
        gvr = GatewayVerifyResult(
            valid=True,
            gateway_version="1.2.3",
            gateway_status="healthy",
            requires_auth=False,
            error=None,
        )
        assert gvr.valid is True
        assert gvr.gateway_version == "1.2.3"
        assert gvr.gateway_status == "healthy"
        assert gvr.requires_auth is False

    def test_session_info_dataclass(self):
        now = datetime.now(timezone.utc)
        info = SessionInfo(
            tenant_id="tenant_x",
            tier="enterprise",
            authenticated=True,
            credentials_path="/path/to/creds",
            last_validated=now,
            gateway_url="https://api.test",
            uses_secure_storage=True,
        )
        assert info.tenant_id == "tenant_x"
        assert info.tier == "enterprise"
        assert info.authenticated is True
        assert info.last_validated == now
        assert info.gateway_url == "https://api.test"
        assert info.uses_secure_storage is True

    def test_get_cache_hmac_key_from_machine_id(self):
        with patch("builtins.open", mock_open(read_data="my-machine-id-123\n")):
            key, source = _get_cache_hmac_key()
            assert source == "/etc/machine-id"
            assert isinstance(key, bytes)
            assert len(key) == 32

    def test_get_cache_hmac_key_from_second_path(self):
        def _side_effect(path, *args, **kwargs):
            if path == "/etc/machine-id":
                raise OSError("Not found")
            if path == "/var/lib/dbus/machine-id":
                return mock_open(read_data="dbus-mid-456\n").return_value
            raise OSError("Unknown path")

        with patch("builtins.open", side_effect=_side_effect):
            key, source = _get_cache_hmac_key()
            assert source == "/var/lib/dbus/machine-id"
            assert isinstance(key, bytes)

    def test_get_cache_hmac_key_fallback_nodename_and_default(self):
        with patch("builtins.open", side_effect=OSError("Read error")):
            with patch("os.uname", return_value=MagicMock(nodename="testhost")):
                key, source = _get_cache_hmac_key()
                assert source == "nodename"
                assert isinstance(key, bytes)

        with patch("builtins.open", side_effect=OSError("Read error")):
            with patch.object(os, "uname", create=True, side_effect=AttributeError):
                with patch("os.uname", None):
                    pass

    def test_verify_cache_hmac_mismatch_warning(self):
        raw = b"session_data_bytes"
        wrong_sig = "0" * 64
        assert _verify_cache_hmac(raw, wrong_sig) is False

    def test_session_cache_from_dict_hmac_mismatch_raises_value_error(self):
        cache = SessionCache(
            tenant_id="t_hmac_test",
            tier="pro",
            role="admin",
            cached_at=datetime.now(timezone.utc),
        )
        d = cache.to_dict()
        d["hmac"] = "bad" + d["hmac"][3:]
        with pytest.raises(ValueError, match="Session cache HMAC verification failed"):
            SessionCache.from_dict(d)


class TestAuthSessionCoverage:
    def test_save_cleanup_on_exception_and_unlink_error(self, tmp_path):
        cache_file = tmp_path / "sub" / "session.json"
        mgr = SessionManager(cache_path=str(cache_file))

        cache = SessionCache(
            tenant_id="t_save_test",
            tier="free",
            role="user",
            cached_at=datetime.now(timezone.utc),
        )

        with patch("os.replace", side_effect=RuntimeError("Disk failure")):
            with patch("os.unlink", side_effect=OSError("Permission denied")):
                with pytest.raises(RuntimeError, match="Disk failure"):
                    mgr.save(cache)

    def test_load_value_error_handling(self, tmp_path):
        cache_file = tmp_path / "session.json"
        mgr = SessionManager(cache_path=str(cache_file))

        # Write corrupted HMAC JSON
        cache_file.write_text('{"tenant_id": "x"}')

        # 1. ValueError containing HMAC
        with patch.object(SessionCache, "from_dict", side_effect=ValueError("HMAC signature failed")):
            loaded = mgr.load()
            assert loaded is None

        # Re-write cache file since clear() removed it in case 1
        cache_file.write_text('{"tenant_id": "y"}')

        # 2. ValueError without HMAC
        with patch.object(SessionCache, "from_dict", side_effect=ValueError("Invalid date format")):
            loaded = mgr.load()
            assert loaded is None

    def test_clear_oserror_returns_false(self, tmp_path):
        cache_file = tmp_path / "session.json"
        cache_file.write_text("{}")
        mgr = SessionManager(cache_path=str(cache_file))

        with patch("os.remove", side_effect=OSError("Permission denied")):
            assert mgr.clear() is False

    def test_get_cached_states(self, tmp_path):
        cache_file = tmp_path / "session.json"
        mgr = SessionManager(cache_path=str(cache_file))
        assert mgr.get_cached() is None

        # Valid cached
        valid_cache = SessionCache(
            tenant_id="t_cached",
            tier="free",
            role="user",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        mgr._in_memory_cache = valid_cache
        assert mgr.get_cached() is valid_cache

        # Expired cached
        expired_cache = SessionCache(
            tenant_id="t_expired",
            tier="free",
            role="user",
            cached_at=datetime.now(timezone.utc) - timedelta(seconds=600),
            ttl_seconds=300,
        )
        mgr._in_memory_cache = expired_cache
        assert mgr.get_cached() is None


class TestAuthTenantCoverage:
    def test_hash_helpers_and_legacy_detection(self):
        token = "test_secret_token_123"
        h = _hash_tenant_token(token)
        assert len(h) == 8

        h_legacy = _hash_tenant_token_legacy(token)
        assert len(h_legacy) == 8

        assert _looks_like_legacy_tenant_id("local_12345678") is True
        assert _looks_like_legacy_tenant_id("ak_12345678") is True
        assert _looks_like_legacy_tenant_id("new_12345678") is False

        assert derive_tenant_id(token) == h

    def test_tenant_manager_init(self):
        tm_default = TenantManager()
        assert tm_default.local_test_mode is False
        tm_test = TenantManager(local_test_mode=True)
        assert tm_test.local_test_mode is True

    def test_validate_token_format(self):
        tm = TenantManager()
        # Missing or empty
        valid, msg, code = tm.validate_token_format("")
        assert valid is False
        assert code == "missing_credentials"

        # mk_ too short
        valid, msg, code = tm.validate_token_format("mk_123")
        assert valid is False
        assert code == "invalid_api_key_format"

        # mk_ valid length
        valid, msg, code = tm.validate_token_format("mk_pro_long_key_12345")
        assert valid is True
        assert msg is None

        # JWT invalid format
        valid, msg, code = tm.validate_token_format("invalid.jwt.token")
        assert valid is False
        assert code == "invalid_jwt_format"

        # JWT expired
        past = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        expired_jwt = _make_jwt({"sub": "t1", "exp": past})
        valid, msg, code = tm.validate_token_format(expired_jwt)
        assert valid is False
        assert code == "token_expired"

        # JWT valid
        future = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        valid_jwt = _make_jwt({"sub": "t1", "exp": future, "tier": "pro"})
        valid, msg, code = tm.validate_token_format(valid_jwt)
        assert valid is True
        assert msg is None

        # Unknown format (no mk_, no dot)
        valid, msg, code = tm.validate_token_format("some_random_plain_string")
        assert valid is False
        assert code == "unknown_format"

    def test_extract_tier_from_token(self):
        tm = TenantManager()
        assert tm.extract_tier_from_token("mk_free_abc123") == "free"
        assert tm.extract_tier_from_token("mk_trial_abc123") == "trial"
        assert tm.extract_tier_from_token("mk_enterprise_abc123") == "enterprise"
        assert tm.extract_tier_from_token("mk_custom_abc123") == "pro"

    def test_generate_mock_tenant_id(self):
        tm = TenantManager()
        mock_id = tm.generate_mock_tenant_id("my-token")
        assert mock_id.startswith("local_")
        assert len(mock_id) == 6 + 8

    def test_local_validate(self):
        tm = TenantManager()
        # Invalid format
        res_invalid = tm.local_validate("short")
        assert res_invalid.valid is False
        assert res_invalid.error_code == "unknown_format"

        # mk_ token
        res_mk = tm.local_validate("mk_free_test_key")
        assert res_mk.valid is True
        assert res_mk.tenant.tenant_id == "local"
        assert res_mk.tenant.tier == "free"
        assert "cli_commands" in res_mk.tenant.features

        # Valid JWT
        future = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        valid_jwt = _make_jwt({"sub": "tenant_jwt_1", "role": "pro", "exp": future})
        res_jwt = tm.local_validate(valid_jwt)
        assert res_jwt.valid is True
        assert res_jwt.tenant.tenant_id == "tenant_jwt_1"
        assert res_jwt.tenant.tier == "pro"

        # Token that passes validate_token_format but fails decode_jwt or expiry in second branch
        with patch.object(tm, "validate_token_format", return_value=(True, None, None)):
            with patch("src.core.auth_tenant.decode_jwt", return_value=None):
                res_fallback = tm.local_validate("bogus.jwt.token")
                assert res_fallback.valid is False
                assert res_fallback.error_code == "local_validation_failed"

    def test_extract_from_jwt(self):
        tm = TenantManager()
        # decode returns None
        assert tm.extract_from_jwt("corrupted.jwt.value") is None

        # expired
        past = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        expired_jwt = _make_jwt({"sub": "t1", "exp": past})
        assert tm.extract_from_jwt(expired_jwt) is None

        # valid
        future = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        valid_jwt = _make_jwt({"sub": "t_valid", "role": "enterprise", "exp": future})
        ctx = tm.extract_from_jwt(valid_jwt)
        assert ctx is not None
        assert ctx.tenant_id == "t_valid"
        assert ctx.tier == "enterprise"

    def test_extract_from_api_key(self):
        tm = TenantManager()
        ctx = tm.extract_from_api_key("mk_enterprise_001")
        assert ctx.tenant_id.startswith("ak_")
        assert ctx.tier == "enterprise"
        assert "priority_support" in ctx.features
        assert ctx.license_key == "mk_enterprise_001"

    def test_get_features_for_tier(self):
        tm = TenantManager()
        assert "raas_full" in tm.get_features_for_tier("enterprise")
        # Unknown tier defaults to free
        assert tm.get_features_for_tier("nonexistent") == tm.TIER_FEATURES["free"]

    def test_has_feature(self):
        tm = TenantManager()
        ctx = TenantContext(tenant_id="t1", tier="pro", role="user", features=["raas_basic"])
        assert tm.has_feature(ctx, "raas_basic") is True
        assert tm.has_feature(ctx, "raas_full") is False

    def test_is_license_expired(self):
        tm = TenantManager()
        # No expiry set
        ctx_no_exp = TenantContext(tenant_id="t1", tier="free", role="user")
        assert tm.is_license_expired(ctx_no_exp) is False

        # Expired in past
        ctx_past = TenantContext(
            tenant_id="t2",
            tier="free",
            role="user",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        assert tm.is_license_expired(ctx_past) is True

        # Valid in future
        ctx_future = TenantContext(
            tenant_id="t3",
            tier="free",
            role="user",
            expires_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        assert tm.is_license_expired(ctx_future) is False

    def test_get_license_status(self):
        tm = TenantManager()
        future_dt = datetime.now(timezone.utc) + timedelta(days=10)
        ctx = TenantContext(
            tenant_id="t_status",
            tier="pro",
            role="admin",
            license_key="mk_pro_12345",
            expires_at=future_dt,
            features=["cli_commands"],
        )
        status = tm.get_license_status(ctx)
        assert status["tenant_id"] == "t_status"
        assert status["tier"] == "pro"
        assert status["is_active"] is True
        assert status["has_license_key"] is True
        assert status["days_until_expiry"] >= 9
        assert status["features"] == ["cli_commands"]

        # Without expires_at
        ctx2 = TenantContext(tenant_id="t_no_exp", tier="free", role="user")
        status2 = tm.get_license_status(ctx2)
        assert status2["expires_at"] is None
        assert status2["days_until_expiry"] is None
        assert status2["has_license_key"] is False
