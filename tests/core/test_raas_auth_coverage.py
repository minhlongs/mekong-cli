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
