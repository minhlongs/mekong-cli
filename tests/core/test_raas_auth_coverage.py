"""
Additional coverage tests for RaaS Auth Client.

Targets uncovered branches:
- _get_certificate_headers
- get_certificate_status
- rotate_certificate
- verify_gateway (all branches)
- get_session (refresh path, fresh validate path)
- rotate_key
- get_tenant_context
- is_authenticated
- sync_to_dashboard (all branches)
- get_gateway_health (all branches)
- session_cache_path setter
- _save_credentials (no token path)
- _load_credentials (JSON error path)
"""

import os
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import requests

from src.core.raas_auth import RaaSAuthClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(tmp_path=None, **kwargs):
    """Create a client with secure storage & cert auth disabled for speed."""
    defaults = {"use_secure_storage": False, "use_certificate_auth": False}
    defaults.update(kwargs)
    if tmp_path is not None:
        creds = tmp_path / "credentials.json"
        defaults.setdefault("credentials_file", str(creds))
    return RaaSAuthClient(**defaults)


# ---------------------------------------------------------------------------
# _save_credentials — no token branch
# ---------------------------------------------------------------------------

class TestSaveCredentialsEdgeCases:
    def test_save_credentials_no_token_is_noop(self, tmp_path):
        client = _make_client(tmp_path)
        client._save_credentials({})  # no "token" key → should not raise or write
        assert not (tmp_path / "credentials.json").exists()

    def test_save_credentials_writes_file_with_permissions(self, tmp_path):
        client = _make_client(tmp_path)
        client._save_credentials({"token": "mk_abc1234567890"})
        creds_file = client.credentials_path
        assert creds_file.exists()
        data = json.loads(creds_file.read_text())
        assert data["token"] == "mk_abc1234567890"
        # File should be mode 600
        assert oct(creds_file.stat().st_mode)[-3:] == "600"


# ---------------------------------------------------------------------------
# _load_credentials — JSON error + empty path
# ---------------------------------------------------------------------------

class TestLoadCredentialsEdgeCases:
    def test_load_credentials_corrupt_json_returns_empty(self, tmp_path):
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text("NOT_JSON{{}")
        client = _make_client(tmp_path)
        result = client._load_credentials()
        assert result == {}

    def test_load_credentials_missing_file_returns_empty(self, tmp_path):
        client = _make_client(tmp_path)
        result = client._load_credentials()
        assert result == {}


# ---------------------------------------------------------------------------
# _get_certificate_headers
# ---------------------------------------------------------------------------

class TestCertificateHeaders:
    def test_no_cert_auth_returns_none(self, tmp_path):
        client = _make_client(tmp_path)
        assert client._get_certificate_headers() is None

    def test_cert_store_returns_headers(self, tmp_path):
        client = _make_client(tmp_path, use_certificate_auth=False)
        mock_store = MagicMock()
        mock_store.export_for_request.return_value = {
            "X-Cert-ID": "cert-123",
            "X-Cert-Sig": "sig-abc",
        }
        client._certificate_store = mock_store
        client.use_certificate_auth = True
        headers = client._get_certificate_headers()
        assert headers == {"X-Cert-ID": "cert-123", "X-Cert-Sig": "sig-abc"}

    def test_cert_store_exception_returns_none(self, tmp_path):
        client = _make_client(tmp_path, use_certificate_auth=False)
        mock_store = MagicMock()
        mock_store.export_for_request.side_effect = RuntimeError("cert error")
        client._certificate_store = mock_store
        client.use_certificate_auth = True
        result = client._get_certificate_headers()
        assert result is None

    def test_cert_store_returns_none_value(self, tmp_path):
        client = _make_client(tmp_path, use_certificate_auth=False)
        mock_store = MagicMock()
        mock_store.export_for_request.return_value = None
        client._certificate_store = mock_store
        client.use_certificate_auth = True
        result = client._get_certificate_headers()
        assert result is None


# ---------------------------------------------------------------------------
# get_certificate_status
# ---------------------------------------------------------------------------

class TestGetCertificateStatus:
    def test_no_cert_store_returns_none(self, tmp_path):
        client = _make_client(tmp_path)
        assert client.get_certificate_status() is None

    def test_cert_store_no_metadata(self, tmp_path):
        client = _make_client(tmp_path)
        mock_store = MagicMock()
        mock_store.get_metadata.return_value = None
        client._certificate_store = mock_store
        status = client.get_certificate_status()
        assert status["has_certificate"] is False

    def test_cert_store_with_metadata(self, tmp_path):
        client = _make_client(tmp_path)
        mock_store = MagicMock()
        meta = MagicMock()
        meta.certificate_id = "cert-456"
        meta.device_id = "a" * 32
        meta.valid_from = datetime(2024, 1, 1, tzinfo=timezone.utc)
        meta.valid_until = datetime(2025, 1, 1, tzinfo=timezone.utc)
        meta.should_rotate = False
        meta.is_expired = False
        meta.rotated_count = 0
        mock_store.get_metadata.return_value = meta
        client._certificate_store = mock_store
        status = client.get_certificate_status()
        assert status["has_certificate"] is True
        assert status["certificate_id"] == "cert-456"


# ---------------------------------------------------------------------------
# rotate_certificate
# ---------------------------------------------------------------------------

class TestRotateCertificate:
    def test_no_cert_store_returns_error(self, tmp_path):
        client = _make_client(tmp_path)
        result = client.rotate_certificate()
        assert result["success"] is False
        assert "not enabled" in result["error"]

    def test_rotate_success(self, tmp_path):
        client = _make_client(tmp_path)
        mock_store = MagicMock()
        new_cert = MagicMock()
        new_cert.certificate_id = "new-cert-789"
        new_cert.valid_until = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_store.rotate_certificate.return_value = new_cert
        client._certificate_store = mock_store
        result = client.rotate_certificate()
        assert result["success"] is True
        assert result["certificate_id"] == "new-cert-789"

    def test_rotate_not_needed(self, tmp_path):
        client = _make_client(tmp_path)
        mock_store = MagicMock()
        mock_store.rotate_certificate.return_value = None
        client._certificate_store = mock_store
        result = client.rotate_certificate()
        assert result["success"] is True
        assert "not yet due" in result["message"]

    def test_rotate_exception(self, tmp_path):
        client = _make_client(tmp_path)
        mock_store = MagicMock()
        mock_store.rotate_certificate.side_effect = RuntimeError("disk error")
        client._certificate_store = mock_store
        result = client.rotate_certificate()
        assert result["success"] is False
        assert "Rotation failed" in result["error"]


# ---------------------------------------------------------------------------
# verify_gateway
# ---------------------------------------------------------------------------

class TestVerifyGateway:
    @pytest.fixture
    def client(self, tmp_path):
        return _make_client(tmp_path)

    def test_no_credentials_returns_requires_auth(self, client):
        result = client.verify_gateway()
        assert result.valid is False
        assert result.requires_auth is True

    def test_invalid_format_returns_error(self, client):
        result = client.verify_gateway("bad_token_format")
        assert result.valid is False
        assert result.requires_auth is True

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_200(self, mock_get, client):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"gateway_version": "2.1.0", "status": "operational"}
        mock_get.return_value = resp
        result = client.verify_gateway("mk_valid_key_123")
        assert result.valid is True
        assert result.gateway_version == "2.1.0"
        assert result.requires_auth is False

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_401(self, mock_get, client):
        resp = MagicMock()
        resp.status_code = 401
        mock_get.return_value = resp
        result = client.verify_gateway("mk_invalid_key123")
        assert result.valid is False
        assert result.requires_auth is True

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_403(self, mock_get, client):
        resp = MagicMock()
        resp.status_code = 403
        mock_get.return_value = resp
        result = client.verify_gateway("mk_revoked_key123")
        assert result.valid is False
        assert result.requires_auth is True

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_404(self, mock_get, client):
        resp = MagicMock()
        resp.status_code = 404
        mock_get.return_value = resp
        result = client.verify_gateway("mk_valid_key_123")
        assert result.valid is False
        assert result.gateway_status == "unreachable"

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_500(self, mock_get, client):
        resp = MagicMock()
        resp.status_code = 500
        mock_get.return_value = resp
        result = client.verify_gateway("mk_valid_key_123")
        assert result.valid is False
        assert result.gateway_status == "error"

    @patch("src.core.raas_auth.requests.get")
    def test_gateway_network_error(self, mock_get, client):
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")
        result = client.verify_gateway("mk_valid_key_123")
        assert result.valid is False
        assert result.gateway_status == "unreachable"

    def test_verify_uses_stored_credentials(self, tmp_path):
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_stored_key_123"}))
        client = _make_client(tmp_path)
        with patch("src.core.raas_auth.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {}
            mock_get.return_value = resp
            result = client.verify_gateway()  # no token arg
        assert result.valid is True


# ---------------------------------------------------------------------------
# get_session — auto-refresh and fresh validate paths
# ---------------------------------------------------------------------------

class TestGetSessionPaths:
    @patch("src.core.raas_auth.requests.post")
    def test_get_session_fresh_validate_success(self, mock_post, tmp_path):
        """No cache + token → calls validate_credentials."""
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_fresh_key_123"}))
        client = _make_client(tmp_path)
        client._session_cache = None

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tenant_id": "fresh_tenant",
            "tier": "pro",
            "role": "owner",
        }
        mock_post.return_value = resp
        session = client.get_session()
        assert session.authenticated is True
        assert session.tenant_id == "fresh_tenant"

    @patch("src.core.raas_auth.requests.post")
    def test_get_session_refresh_triggered(self, mock_post, tmp_path):
        """Cache near expiry triggers background refresh."""
        from src.core.raas_auth import SessionCache
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_refresh_key_123"}))
        client = _make_client(tmp_path)

        # Put a cache that should_refresh → True (cached_at far enough back)
        near_expiry = datetime.now(timezone.utc)
        cache = SessionCache(
            tenant_id="refresh_tenant",
            tier="pro",
            role="owner",
            cached_at=near_expiry,
            ttl_seconds=1,  # expires in 1s → should_refresh = True
        )
        client._session_cache = cache

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tenant_id": "refresh_tenant",
            "tier": "pro",
            "role": "owner",
        }
        mock_post.return_value = resp
        session = client.get_session()
        # Session should still be returned from cache
        assert session.tenant_id == "refresh_tenant"


# ---------------------------------------------------------------------------
# rotate_key
# ---------------------------------------------------------------------------

class TestRotateKey:
    def test_rotate_key_wrong_format(self, tmp_path):
        client = _make_client(tmp_path)
        result = client.rotate_key("jwt_not_mk_key")
        assert result.valid is False
        assert result.error_code == "invalid_api_key_format"

    @patch("src.core.raas_auth.requests.post")
    def test_rotate_key_success(self, mock_post, tmp_path):
        client = _make_client(tmp_path)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tenant_id": "rotated_tenant",
            "tier": "pro",
            "role": "owner",
        }
        mock_post.return_value = resp
        result = client.rotate_key("mk_new_key_12345")
        assert result.valid is True
        assert client.credentials_path.exists()

    @patch("src.core.raas_auth.requests.post")
    def test_rotate_key_gateway_failure(self, mock_post, tmp_path):
        client = _make_client(tmp_path)
        resp = MagicMock()
        resp.status_code = 401
        mock_post.return_value = resp
        result = client.rotate_key("mk_invalid_key123")
        assert result.valid is False
        # Credentials should NOT be saved on failure
        assert not client.credentials_path.exists()


# ---------------------------------------------------------------------------
# get_tenant_context
# ---------------------------------------------------------------------------

class TestGetTenantContext:
    def test_no_cache_returns_none(self, tmp_path):
        client = _make_client(tmp_path)
        client._session_cache = None
        ctx = client.get_tenant_context()
        assert ctx is None

    def test_returns_tenant_context_from_cache(self, tmp_path):
        from src.core.raas_auth import SessionCache
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="ctx_tenant",
            tier="enterprise",
            role="admin",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache
        ctx = client.get_tenant_context()
        assert ctx is not None
        assert ctx.tenant_id == "ctx_tenant"
        assert ctx.tier == "enterprise"


# ---------------------------------------------------------------------------
# is_authenticated
# ---------------------------------------------------------------------------

class TestIsAuthenticated:
    def test_not_authenticated_without_session(self, tmp_path):
        client = _make_client(tmp_path)
        client._session_cache = None
        assert client.is_authenticated() is False

    def test_authenticated_with_valid_cache(self, tmp_path):
        from src.core.raas_auth import SessionCache
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="auth_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache
        assert client.is_authenticated() is True


# ---------------------------------------------------------------------------
# sync_to_dashboard
# ---------------------------------------------------------------------------

class TestSyncToDashboard:
    def test_not_authenticated_returns_error(self, tmp_path):
        client = _make_client(tmp_path)
        client._session_cache = None
        result = client.sync_to_dashboard()
        assert result["synced"] is False
        assert "Not authenticated" in result["error"]

    @patch("src.core.raas_auth.requests.post")
    def test_sync_success_v2(self, mock_post, tmp_path):
        from src.core.raas_auth import SessionCache
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_sync_key_12345"}))
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="sync_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache

        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tenant_id": "sync_tenant",
            "tier": "pro",
            "features": ["f1"],
        }
        mock_post.return_value = resp
        result = client.sync_to_dashboard()
        assert result["synced"] is True
        assert result["tenant_id"] == "sync_tenant"

    @patch("src.core.raas_auth.requests.post")
    def test_sync_v2_404_fallback_v1(self, mock_post, tmp_path):
        from src.core.raas_auth import SessionCache
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_sync_key_12345"}))
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="sync_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache

        resp_404 = MagicMock()
        resp_404.status_code = 404
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {"tenant_id": "v1_sync_tenant", "tier": "free"}
        mock_post.side_effect = [resp_404, resp_200]

        result = client.sync_to_dashboard()
        assert result["synced"] is True
        assert mock_post.call_count == 2

    @patch("src.core.raas_auth.requests.post")
    def test_sync_gateway_error(self, mock_post, tmp_path):
        from src.core.raas_auth import SessionCache
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_sync_key_12345"}))
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="sync_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache

        resp = MagicMock()
        resp.status_code = 500
        mock_post.return_value = resp
        result = client.sync_to_dashboard()
        assert result["synced"] is False

    @patch("src.core.raas_auth.requests.post")
    def test_sync_network_error(self, mock_post, tmp_path):
        from src.core.raas_auth import SessionCache
        creds_file = tmp_path / "credentials.json"
        creds_file.write_text(json.dumps({"token": "mk_sync_key_12345"}))
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="sync_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache

        mock_post.side_effect = requests.exceptions.ConnectionError("net error")
        result = client.sync_to_dashboard()
        assert result["synced"] is False
        assert "Sync failed" in result["error"]

    def test_sync_no_token(self, tmp_path):
        from src.core.raas_auth import SessionCache
        client = _make_client(tmp_path)  # no credentials file
        cache = SessionCache(
            tenant_id="sync_tenant",
            tier="pro",
            role="owner",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._session_cache = cache
        result = client.sync_to_dashboard()
        assert result["synced"] is False
        assert "No credentials" in result["error"]


# ---------------------------------------------------------------------------
# get_gateway_health
# ---------------------------------------------------------------------------

class TestGetGatewayHealth:
    @patch("src.core.raas_auth.requests.get")
    def test_health_success(self, mock_get, tmp_path):
        client = _make_client(tmp_path)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"status": "healthy", "version": "2.1.0"}
        mock_get.return_value = resp
        result = client.get_gateway_health()
        assert result["healthy"] is True
        assert result["version"] == "2.1.0"

    @patch("src.core.raas_auth.requests.get")
    def test_health_non_200(self, mock_get, tmp_path):
        client = _make_client(tmp_path)
        resp = MagicMock()
        resp.status_code = 503
        mock_get.return_value = resp
        result = client.get_gateway_health()
        assert result["healthy"] is False
        assert "503" in result["error"]

    @patch("src.core.raas_auth.requests.get")
    def test_health_network_error(self, mock_get, tmp_path):
        client = _make_client(tmp_path)
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")
        result = client.get_gateway_health()
        assert result["healthy"] is False
        assert "unreachable" in result["error"].lower()


# ---------------------------------------------------------------------------
# session_cache_path setter
# ---------------------------------------------------------------------------

class TestSessionCachePathSetter:
    def test_setter_accepts_string(self, tmp_path):
        client = _make_client(tmp_path)
        new_path = str(tmp_path / "new_session.json")
        client.session_cache_path = new_path
        assert "new_session.json" in str(client.session_cache_path)

    def test_setter_accepts_path_object(self, tmp_path):
        client = _make_client(tmp_path)
        new_path = tmp_path / "path_session.json"
        client.session_cache_path = new_path
        assert "path_session.json" in str(client.session_cache_path)


# ---------------------------------------------------------------------------
# local_test_mode
# ---------------------------------------------------------------------------

class TestLocalTestMode:
    @patch.dict(os.environ, {"RAAS_LOCAL_TEST": "true"})
    def test_local_test_mode_skips_gateway(self, tmp_path):
        client = _make_client(tmp_path)
        assert client.local_test_mode is True
        result = client.validate_credentials("mk_local_test_key_12345")
        # Local validation returns valid for mk_ keys without calling gateway
        assert result.valid is True

    @patch.dict(os.environ, {"RAAS_LOCAL_TEST": "false"})
    def test_local_test_mode_off(self, tmp_path):
        client = _make_client(tmp_path)
        assert client.local_test_mode is False


# ---------------------------------------------------------------------------
# _session_cache_to_tenant_context
# ---------------------------------------------------------------------------

class TestSessionCacheToTenantContext:
    def test_conversion(self, tmp_path):
        from src.core.raas_auth import SessionCache
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="conv_tenant",
            tier="trial",
            role="user",
            license_key="mk_conv_key",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        ctx = client._session_cache_to_tenant_context(cache)
        assert ctx.tenant_id == "conv_tenant"
        assert ctx.tier == "trial"
        assert ctx.license_key == "mk_conv_key"


# ---------------------------------------------------------------------------
# _call_gateway_validation — non-200/401/403/404 fallback to local
# ---------------------------------------------------------------------------

class TestCallGatewayValidationFallback:
    @patch("src.core.raas_auth.requests.post")
    def test_non_200_401_403_404_falls_back_local(self, mock_post, tmp_path):
        client = _make_client(tmp_path)
        resp = MagicMock()
        resp.status_code = 500
        mock_post.return_value = resp
        result = client._call_gateway_validation("mk_some_key12345", "/v2/license/validate")
        # Should fall back to local validation (valid for mk_ keys)
        assert result.valid is True


# ---------------------------------------------------------------------------
# Edge branches: Cert headers, cert store init, login migration, logout OSError
# ---------------------------------------------------------------------------

class TestAuthGatewayMixinEdgeBranches:
    def test_get_requests_pkg_none(self):
        import sys
        from src.core.raas_auth.auth_gateway_mixin import _get_requests, _requests_base
        with patch.dict(sys.modules, {"src.core.raas_auth": None}):
            assert _get_requests() is _requests_base

    def test_call_gateway_validation_with_cert_headers(self, tmp_path):
        client = _make_client(tmp_path)
        with patch.object(client, "_get_certificate_headers", return_value={"X-Cert": "c123"}), \
             patch("src.core.raas_auth.requests.post") as mock_post:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"tenant_id": "t1", "tier": "pro"}
            mock_post.return_value = resp
            res = client._call_gateway_validation("mk_test_key12345", "/v1/validate")
            assert res.valid is True
            assert mock_post.call_args[1]["headers"]["X-Cert"] == "c123"

    def test_verify_gateway_with_cert_headers(self, tmp_path):
        client = _make_client(tmp_path)
        with patch.object(client, "_get_certificate_headers", return_value={"X-Cert": "c123"}), \
             patch("src.core.raas_auth.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"status": "ok"}
            mock_get.return_value = resp
            res = client.verify_gateway(token="mk_valid1234567890")
            assert res.valid is True
            assert mock_get.call_args[1]["headers"]["X-Cert"] == "c123"

    def test_call_gateway_validation_404_and_403(self, tmp_path):
        client = _make_client(tmp_path)
        with patch("src.core.raas_auth.requests.post") as mock_post:
            resp404 = MagicMock(status_code=404)
            mock_post.return_value = resp404
            r404 = client._call_gateway_validation("mk_12345678", "/v1/test")
            assert r404.error_code == "endpoint_not_found"

            resp403 = MagicMock(status_code=403)
            mock_post.return_value = resp403
            r403 = client._call_gateway_validation("mk_12345678", "/v1/test")
            assert r403.error_code == "credentials_revoked"

    def test_call_gateway_validation_request_exception_falls_back_local(self, tmp_path):
        import requests
        client = _make_client(tmp_path)
        with patch("src.core.raas_auth.requests.post", side_effect=requests.RequestException("boom")):
            res = client._call_gateway_validation("mk_12345678", "/v1/test")
            assert res.valid is True

    def test_validate_credentials_missing_token(self, tmp_path):
        client = _make_client(tmp_path)
        with patch.dict("os.environ", {}, clear=True):
            res = client.validate_credentials(token=None)
            assert res.valid is False
            assert res.error_code == "missing_credentials"

    def test_validate_credentials_from_stored_creds(self, tmp_path):
        client = _make_client(tmp_path)
        client.credentials_path.write_text(json.dumps({"token": "mk_stored_12345678"}))
        with patch.object(client, "_call_gateway_validation") as mock_val:
            mock_val.return_value = MagicMock(valid=True, error_code=None)
            res = client.validate_credentials(token=None)
            assert res.valid is True

    def test_validate_credentials_invalid_format(self, tmp_path):
        client = _make_client(tmp_path)
        res = client.validate_credentials(token="invalid_key")
        assert res.valid is False
        assert res.error_code == "unknown_format"

    def test_validate_credentials_v2_404_falls_back_v1(self, tmp_path):
        client = _make_client(tmp_path)
        with patch.object(client, "_call_gateway_validation") as mock_val:
            mock_val.side_effect = [
                MagicMock(valid=False, error_code="endpoint_not_found"),
                MagicMock(valid=True, error_code=None),
            ]
            res = client.validate_credentials("mk_12345678", use_v2=True)
            assert res.valid is True
            assert mock_val.call_count == 2


class TestRaaSAuthClientEdgeBranches:
    def test_init_secure_storage_exception_logged(self, tmp_path):
        with patch("src.core.raas_auth.get_secure_storage", side_effect=RuntimeError("secure fail")):
            client = _make_client(tmp_path, use_secure_storage=True)
            assert client._secure_storage is None

    def test_init_certificate_store_exception_logged(self, tmp_path):
        with patch("src.core.raas_auth.raas_auth_client.get_certificate_store", side_effect=RuntimeError("cert fail")):
            client = _make_client(tmp_path, use_certificate_auth=True)
            assert client._certificate_store is None

    def test_session_cache_methods(self, tmp_path):
        from src.core.raas_auth import SessionCache
        client = _make_client(tmp_path)
        cache = SessionCache(
            tenant_id="t_test",
            tier="pro",
            role="admin",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=300,
        )
        client._save_session_cache(cache)
        loaded = client._load_session_cache()
        assert loaded is not None
        assert loaded.tenant_id == "t_test"
        assert client._session_cache is not None
        assert client._session_cache.tenant_id == "t_test"
        assert client._clear_session_cache() is True

    def test_save_credentials_secure_storage_failure_falls_back_to_file(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        mock_storage = MagicMock()
        mock_storage.store_license.side_effect = RuntimeError("store fail")
        client._secure_storage = mock_storage
        client._save_credentials({"token": "mk_test123"})
        assert client.credentials_path.exists()
        assert "mk_test123" in client.credentials_path.read_text()

    def test_load_credentials_secure_storage_failure_falls_back_to_file(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        mock_storage = MagicMock()
        mock_storage.get_license.side_effect = RuntimeError("get fail")
        client._secure_storage = mock_storage
        client.credentials_path.write_text(json.dumps({"token": "mk_file_token"}))
        creds = client._load_credentials()
        assert creds.get("token") == "mk_file_token"

    def test_migrate_to_secure_storage_failure_returns_false(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        mock_storage = MagicMock()
        mock_storage.store_license.side_effect = RuntimeError("migration fail")
        client._secure_storage = mock_storage
        client.credentials_path.write_text(json.dumps({"token": "mk_file_token"}))
        assert client._migrate_to_secure_storage() is False

    def test_save_and_load_credentials_secure_storage_success(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        mock_storage = MagicMock()
        mock_storage.get_license.return_value = "mk_secure_token"
        client._secure_storage = mock_storage
        client._save_credentials({"token": "mk_secure_token"})
        mock_storage.store_license.assert_called_once_with("mk_secure_token")
        creds = client._load_credentials()
        assert creds["token"] == "mk_secure_token"
        assert creds["uses_secure_storage"] is True

    def test_migrate_to_secure_storage_success(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        mock_storage = MagicMock()
        client._secure_storage = mock_storage
        client.credentials_path.write_text(json.dumps({"token": "mk_plain_token"}))
        assert client._migrate_to_secure_storage() is True
        mock_storage.store_license.assert_called_once_with("mk_plain_token")
        assert not client.credentials_path.exists()

    def test_migrate_to_secure_storage_no_secure_storage_returns_false(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=False)
        assert client._migrate_to_secure_storage() is False

    def test_login_migrates_to_secure_storage(self, tmp_path):
        client = _make_client(tmp_path, use_secure_storage=True)
        with patch.object(client, "validate_credentials", return_value=MagicMock(valid=True)), \
             patch.object(client, "_save_credentials"), \
             patch.object(client, "_migrate_to_secure_storage") as mock_migrate:
            client.login("mk_valid1234567890", persist=True, migrate_to_secure=True)
            mock_migrate.assert_called_once()

    def test_logout_oserror_swallowed(self, tmp_path):
        client = _make_client(tmp_path)
        client.credentials_path.write_text("dummy")
        with patch("os.remove", side_effect=OSError("permission denied")):
            cleared = client.logout()
            assert cleared is False

    def test_logout_success_when_file_exists(self, tmp_path):
        client = _make_client(tmp_path)
        client.credentials_path.write_text(json.dumps({"token": "mk_test"}))
        assert client.credentials_path.exists()
        assert client.logout() is True
        assert not client.credentials_path.exists()

    def test_get_auth_client_singleton(self):
        import src.core.raas_auth as raas_auth_module
        orig = raas_auth_module._auth_client
        try:
            raas_auth_module._auth_client = None
            client1 = raas_auth_module.get_auth_client("https://gateway.example.com")
            assert client1 is not None
            client2 = raas_auth_module.get_auth_client()
            assert client2 is client1
        finally:
            raas_auth_module._auth_client = orig

