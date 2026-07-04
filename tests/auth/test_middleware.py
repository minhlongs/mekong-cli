"""
Unit tests for src/auth/middleware.py

Tests SessionMiddleware, OptionalAuthMiddleware, and create_auth_middleware factory.
All external dependencies (SessionManager, UserRepository, RateLimiter, AuthConfig)
are mocked so tests run in isolation.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

os.environ.setdefault("AUTH_ENVIRONMENT", "dev")
os.environ.setdefault("TESTING", "true")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_rate_limiter(allowed: bool = True, headers: dict | None = None):
    """Return a RateLimiter mock whose check_limit resolves to (allowed, headers)."""
    rl = MagicMock()
    rl.check_limit = AsyncMock(return_value=(allowed, headers or {}))
    return rl


def _make_mock_session_manager(token: str | None = "valid-token"):
    """Return a SessionManager mock that returns the given token from get_session_cookie."""
    sm = MagicMock()
    sm.get_session_cookie = MagicMock(return_value=token)
    sm.decode_token = MagicMock(
        return_value=(True, {"sub": "00000000-0000-0000-0000-000000000001", "email": "user@test.com", "role": "member"}, None)
    )
    return sm


def _make_mock_user():
    user = MagicMock()
    user.id = UUID("00000000-0000-0000-0000-000000000001")
    user.email = "user@test.com"
    user.role = "member"
    return user


def _make_test_app(middleware_class, **middleware_kwargs):
    """Build a minimal FastAPI app with the given middleware attached."""
    app = FastAPI()

    @app.get("/ping")
    async def ping(request: Request):
        return {
            "authenticated": getattr(request.state, "authenticated", None),
            "user_id": getattr(request.state, "user_id", None),
            "user_role": getattr(request.state, "user_role", None),
            "is_dev_mode": getattr(request.state, "is_dev_mode", None),
        }

    app.add_middleware(middleware_class, **middleware_kwargs)
    return app


# ---------------------------------------------------------------------------
# SessionMiddleware — rate limit
# ---------------------------------------------------------------------------

class TestSessionMiddlewareRateLimit:
    """Rate limit enforcement in SessionMiddleware."""

    def test_rate_limit_exceeded_returns_429(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter(
            allowed=False,
            headers={"Retry-After": "60", "X-RateLimit-Limit": "5"},
        )
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/auth/login")

        assert resp.status_code == 429
        body = resp.json()
        assert body["error"] == "rate_limit_exceeded"
        assert body["retry_after"] == 60

    def test_non_rate_limited_request_returns_200(self):
        """Allowed requests pass through middleware and return 200."""
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter(allowed=True, headers={})
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/ping")

        assert resp.status_code == 200

    def test_non_auth_path_not_rate_limited(self):
        """Non-auth paths should have no rate limit check (returns True, {})."""
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter(allowed=True, headers={})
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/ping")

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# SessionMiddleware — dev mode
# ---------------------------------------------------------------------------

class TestSessionMiddlewareDevMode:
    """Dev mode auto-authentication behaviour."""

    def test_dev_mode_injects_test_user(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = True

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert data["user_id"] == "test-user-id"
        assert data["user_role"] == "owner"
        assert data["is_dev_mode"] is True

    def test_dev_mode_still_enforces_rate_limit(self):
        """Rate limit check runs even in dev mode (security requirement)."""
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter(
            allowed=False,
            headers={"Retry-After": "30"},
        )
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = True

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app, raise_server_exceptions=False)
            # Auth endpoint triggers rate limit
            resp = client.get("/auth/login")

        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# SessionMiddleware — production auth flow
# ---------------------------------------------------------------------------

class TestSessionMiddlewareProductionAuth:
    """Production/staging authentication via JWT cookies."""

    def test_valid_token_authenticates_user(self):
        from src.auth.middleware import SessionMiddleware

        mock_user = _make_mock_user()
        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="jwt.token.here")
        sm.decode_token = MagicMock(
            return_value=(True, {"sub": str(mock_user.id), "email": mock_user.email, "role": "member"}, None)
        )

        with patch("src.auth.middleware.AuthConfig") as MockConfig, \
             patch("src.auth.middleware.UserRepository") as MockRepo:
            MockConfig.return_value.is_dev_mode.return_value = False
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id = AsyncMock(return_value=mock_user)

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert data["user_role"] == "member"
        assert data["is_dev_mode"] is False

    def test_no_token_sets_unauthenticated(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is False
        assert data["user_id"] is None
        assert data["user_role"] is None

    def test_invalid_token_sets_unauthenticated(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="bad-token")
        sm.decode_token = MagicMock(return_value=(False, {}, "invalid"))

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.status_code == 200
        assert resp.json()["authenticated"] is False

    def test_token_with_no_sub_sets_unauthenticated(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="token-no-sub")
        sm.decode_token = MagicMock(return_value=(True, {}, None))  # no "sub"

        with patch("src.auth.middleware.AuthConfig") as MockConfig:
            MockConfig.return_value.is_dev_mode.return_value = False

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.status_code == 200
        assert resp.json()["authenticated"] is False

    def test_user_not_found_in_db_sets_unauthenticated(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="valid-jwt")
        sm.decode_token = MagicMock(
            return_value=(True, {"sub": "00000000-0000-0000-0000-000000000099"}, None)
        )

        with patch("src.auth.middleware.AuthConfig") as MockConfig, \
             patch("src.auth.middleware.UserRepository") as MockRepo:
            MockConfig.return_value.is_dev_mode.return_value = False
            repo_instance = MockRepo.return_value
            repo_instance.find_by_id = AsyncMock(return_value=None)

            app = _make_test_app(
                SessionMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        assert resp.json()["authenticated"] is False


# ---------------------------------------------------------------------------
# SessionMiddleware — _check_rate_limit IP extraction
# ---------------------------------------------------------------------------

class TestCheckRateLimit:
    """IP extraction and preset resolution in _check_rate_limit."""

    @pytest.mark.asyncio
    async def test_x_forwarded_for_takes_first_ip(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        mw = SessionMiddleware.__new__(SessionMiddleware)
        mw._session_manager = sm
        mw._rate_limiter = rate_limiter
        mw._user_repo = MagicMock()

        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        request.url.path = "/auth/login"
        request.client = None

        allowed, headers = await mw._check_rate_limit(request)
        # check_limit called with key containing first IP
        call_args = rate_limiter.check_limit.call_args
        assert "1.2.3.4" in call_args[1].get("key", call_args[0][0] if call_args[0] else "")

    @pytest.mark.asyncio
    async def test_x_real_ip_fallback(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        mw = SessionMiddleware.__new__(SessionMiddleware)
        mw._session_manager = sm
        mw._rate_limiter = rate_limiter
        mw._user_repo = MagicMock()

        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "9.9.9.9"}
        request.url.path = "/auth/login"
        request.client = None

        await mw._check_rate_limit(request)
        call_args = rate_limiter.check_limit.call_args
        key_arg = call_args[1].get("key", call_args[0][0] if call_args[0] else "")
        assert "9.9.9.9" in key_arg

    @pytest.mark.asyncio
    async def test_non_auth_path_returns_allowed_no_check(self):
        from src.auth.middleware import SessionMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        mw = SessionMiddleware.__new__(SessionMiddleware)
        mw._session_manager = sm
        mw._rate_limiter = rate_limiter
        mw._user_repo = MagicMock()

        request = MagicMock(spec=Request)
        request.headers = {}
        request.url.path = "/api/data"
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        allowed, headers = await mw._check_rate_limit(request)

        assert allowed is True
        assert headers == {}
        rate_limiter.check_limit.assert_not_called()


# ---------------------------------------------------------------------------
# OptionalAuthMiddleware
# ---------------------------------------------------------------------------

class TestOptionalAuthMiddleware:
    """OptionalAuthMiddleware never rejects unauthenticated requests."""

    def test_unauthenticated_request_still_gets_200(self):
        from src.auth.middleware import OptionalAuthMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token=None)

        app = _make_test_app(
            OptionalAuthMiddleware,
            session_manager=sm,
            rate_limiter=rate_limiter,
        )
        client = TestClient(app)
        resp = client.get("/ping")

        assert resp.status_code == 200
        assert resp.json()["authenticated"] is False

    def test_valid_token_populates_user_state(self):
        from src.auth.middleware import OptionalAuthMiddleware

        mock_user = _make_mock_user()
        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="jwt.token")
        sm.decode_token = MagicMock(
            return_value=(True, {"sub": str(mock_user.id), "email": mock_user.email, "role": "admin"}, None)
        )

        with patch("src.auth.middleware.UserRepository") as MockRepo:
            MockRepo.return_value.find_by_id = AsyncMock(return_value=mock_user)

            app = _make_test_app(
                OptionalAuthMiddleware,
                session_manager=sm,
                rate_limiter=rate_limiter,
            )
            client = TestClient(app)
            resp = client.get("/ping")

        data = resp.json()
        assert data["authenticated"] is True
        assert data["user_role"] == "admin"

    def test_rate_limit_exceeded_returns_429(self):
        from src.auth.middleware import OptionalAuthMiddleware

        rate_limiter = _make_mock_rate_limiter(
            allowed=False,
            headers={"Retry-After": "45"},
        )
        sm = _make_mock_session_manager(token=None)

        app = _make_test_app(
            OptionalAuthMiddleware,
            session_manager=sm,
            rate_limiter=rate_limiter,
        )
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/auth/login")

        assert resp.status_code == 429
        assert resp.json()["retry_after"] == 45

    def test_invalid_token_sets_authenticated_false(self):
        from src.auth.middleware import OptionalAuthMiddleware

        rate_limiter = _make_mock_rate_limiter()
        sm = _make_mock_session_manager(token="bad-token")
        sm.decode_token = MagicMock(return_value=(False, {}, "invalid"))

        app = _make_test_app(
            OptionalAuthMiddleware,
            session_manager=sm,
            rate_limiter=rate_limiter,
        )
        client = TestClient(app)
        resp = client.get("/ping")

        assert resp.json()["authenticated"] is False


# ---------------------------------------------------------------------------
# create_auth_middleware factory
# ---------------------------------------------------------------------------

class TestCreateAuthMiddleware:
    """create_auth_middleware factory function."""

    def test_dev_mode_true_returns_bypass_middleware(self):
        from src.auth.middleware import create_auth_middleware, SessionMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware

        cls = create_auth_middleware(dev_mode=True)
        assert cls is not SessionMiddleware
        assert issubclass(cls, BaseHTTPMiddleware)

    def test_dev_mode_false_returns_session_middleware(self):
        from src.auth.middleware import create_auth_middleware, SessionMiddleware

        cls = create_auth_middleware(dev_mode=False)
        assert cls is SessionMiddleware

    def test_dev_bypass_middleware_sets_authenticated_true(self):
        from src.auth.middleware import create_auth_middleware

        DevBypass = create_auth_middleware(dev_mode=True)
        app = _make_test_app(DevBypass)
        client = TestClient(app)
        resp = client.get("/ping")

        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert data["user_role"] == "owner"
