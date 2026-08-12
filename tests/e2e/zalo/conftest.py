"""Shared fixtures for Zalo OA E2E tests."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.seed.zalo.client import ZaloOAClient
from src.seed.zalo.models import ZaloOAConfig
from src.seed.zalo.rate_limiter import InMemoryKV, ZaloRateLimiter, create_rate_limiter
from src.seed.zalo.automation import ZaloAutomationEngine, create_common_rules
from src.seed.zalo.templates import ZaloTemplateEngine
from src.seed.zalo.webhook import create_zalo_webhook_router
from src.api import zalo_routes as zalo_routes_module

WEBHOOK_SECRET = "e2e_test_webhook_secret"
OA_ID = "e2e_oa_id"
ACCESS_TOKEN = "e2e_access_token"
REFRESH_TOKEN = "e2e_refresh_token"


@pytest.fixture(scope="session", autouse=True)
def _set_zalo_env():
    """Set Zalo env vars for the API module's lazy globals."""
    os.environ["ZALO_OA_ID"] = OA_ID
    os.environ["ZALO_SECRET_KEY"] = "e2e_secret_key"
    os.environ["ZALO_ACCESS_TOKEN"] = ACCESS_TOKEN
    os.environ["ZALO_REFRESH_TOKEN"] = REFRESH_TOKEN
    os.environ["ZALO_WEBHOOK_SECRET"] = WEBHOOK_SECRET
    os.environ["ZALO_RATE_LIMIT"] = "1000"
    yield
    for key in (
        "ZALO_OA_ID",
        "ZALO_SECRET_KEY",
        "ZALO_ACCESS_TOKEN",
        "ZALO_REFRESH_TOKEN",
        "ZALO_WEBHOOK_SECRET",
        "ZALO_RATE_LIMIT",
    ):
        os.environ.pop(key, None)


@pytest.fixture
def zalo_config() -> ZaloOAConfig:
    """Create E2E Zalo config."""
    return ZaloOAConfig(
        oa_id=OA_ID,
        secret_key="e2e_secret_key",
        access_token=ACCESS_TOKEN,
        refresh_token=REFRESH_TOKEN,
        token_expires_at=datetime.now() + timedelta(hours=1),
        webhook_secret=WEBHOOK_SECRET,
        rate_limit_per_minute=1000,
    )


@pytest.fixture
def e2e_template_dir(tmp_path: Path) -> str:
    """Create temp template dir with test templates."""
    engine = ZaloTemplateEngine(str(tmp_path))
    engine.add_template("welcome", "Chào {{ name }}, chào mừng bạn đến {{ oa_name }}!", "vi_VN")
    engine.add_template("welcome", "Hi {{ name }}, welcome to {{ oa_name }}!", "en_US")
    engine.add_template("help", "Hướng dẫn: {{ commands }}", "vi_VN")
    engine.add_template("help", "Help: {{ commands }}", "en_US")
    engine.add_template("fallback", "Xin lỗi, tôi không hiểu: {{ message }}", "vi_VN")
    engine.add_template("fallback", "Sorry, I don't understand: {{ message }}", "en_US")
    return str(tmp_path)


@pytest.fixture
def automation_engine(e2e_template_dir: str) -> ZaloAutomationEngine:
    """Create automation engine with common rules."""
    template_engine = ZaloTemplateEngine(e2e_template_dir)
    engine = ZaloAutomationEngine(template_engine=template_engine)
    for rule in create_common_rules():
        engine.add_rule(rule)
    return engine


@pytest.fixture
def template_engine_instance(e2e_template_dir: str) -> ZaloTemplateEngine:
    """Create template engine instance for API routes."""
    return ZaloTemplateEngine(e2e_template_dir)


@pytest.fixture
def rate_limiter() -> "ZaloRateLimiter":
    """Create rate limiter with generous limit for E2E."""
    return create_rate_limiter(InMemoryKV(), default_limit=1000, sliding=True)


class FakeZaloResponse:
    """Minimal httpx-like response wrapper around a dict payload."""

    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            from httpx import HTTPStatusError

            raise HTTPStatusError(
                f"HTTP {self.status_code}",
                request=None,  # type: ignore[arg-type]
                response=self,
            )

    def json(self) -> dict:
        return self._data


class FakeZaloHTTPTransport:
    """Fake HTTP transport for Zalo API requests in E2E tests."""

    def __init__(self):
        self.sent_messages: list[dict] = []
        self.sent_messages_count = 0

    async def handle_request(self, method: str, url: str, **kwargs) -> FakeZaloResponse:
        """Simulate Zalo API responses."""
        if "getaccesstoken" in url:
            return FakeZaloResponse(
                {
                    "access_token": "fresh_token",
                    "refresh_token": REFRESH_TOKEN,
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }
            )
        if "message" in url:
            self.sent_messages_count += 1
            payload = kwargs.get("json") or {}
            self.sent_messages.append(payload)
            return FakeZaloResponse(
                {
                    "error": 0,
                    "message": "Success",
                    "msg_id": f"msg_{self.sent_messages_count}",
                    "timestamp": 1234567890,
                }
            )
        if "getprofile" in url:
            return FakeZaloResponse(
                {
                    "error": 0,
                    "message": "Success",
                    "data": {
                        "user_id": "user_123",
                        "name": "E2E User",
                        "gender": 1,
                        "birthday": "01/01/1990",
                        "phone": "0901234567",
                        "avatar": "https://example.com/avatar.jpg",
                        "locale": "vi_VN",
                    },
                }
            )
        if "getfollowers" in url:
            return FakeZaloResponse(
                {
                    "error": 0,
                    "message": "Success",
                    "data": {
                        "followers": [
                            {
                                "user_id": "user_123",
                                "name": "E2E User",
                                "gender": 1,
                                "birthday": "01/01/1990",
                                "phone": "0901234567",
                                "avatar": "https://example.com/avatar.jpg",
                                "locale": "vi_VN",
                            }
                        ]
                    },
                }
            )
        return FakeZaloResponse({"error": -1, "message": "Unknown endpoint"})


@pytest.fixture
def fake_transport() -> FakeZaloHTTPTransport:
    """Create fake transport for Zalo API."""
    return FakeZaloHTTPTransport()


@pytest.fixture
def zalo_client(zalo_config: ZaloOAConfig, fake_transport: FakeZaloHTTPTransport) -> ZaloOAClient:
    """Create Zalo client with fake transport."""

    client = ZaloOAClient(zalo_config)

    async def fake_request(method, url, **kwargs):
        return await fake_transport.handle_request(method, str(url), **kwargs)

    client._client.request = fake_request
    client._client.get = lambda url, **kwargs: fake_transport.handle_request("GET", str(url), **kwargs)
    client._client.post = lambda url, **kwargs: fake_transport.handle_request("POST", str(url), **kwargs)

    return client


@pytest.fixture
def webhook_app(
    zalo_config: ZaloOAConfig,
    zalo_client: ZaloOAClient,
    automation_engine: ZaloAutomationEngine,
    template_engine_instance: ZaloTemplateEngine,
    rate_limiter,
) -> FastAPI:
    """Create FastAPI app with webhook and API routers, wiring fixtures into deps."""
    app = FastAPI()

    # Automation engine sends replies through the same mocked client.
    automation_engine.client = zalo_client

    webhook_router = create_zalo_webhook_router(
        zalo_config, zalo_client, automation_engine, rate_limiter
    )
    app.include_router(webhook_router)

    from src.api.zalo_routes import router as zalo_api_router
    app.include_router(zalo_api_router)

    # Wire fixture instances into the API module's dependencies.
    app.dependency_overrides[zalo_routes_module.get_zalo_client] = lambda: zalo_client
    app.dependency_overrides[zalo_routes_module.get_automation_engine] = lambda: automation_engine
    app.dependency_overrides[zalo_routes_module.get_template_engine_instance] = lambda: template_engine_instance
    app.dependency_overrides[zalo_routes_module.get_rate_limiter] = lambda: rate_limiter

    return app


@pytest.fixture
def webhook_test_client(webhook_app: FastAPI) -> TestClient:
    """Create test client for webhook app."""
    return TestClient(webhook_app)


def make_signature(payload: dict | bytes, secret: str = WEBHOOK_SECRET) -> str:
    """Generate HMAC-SHA256 signature for payload."""
    if isinstance(payload, dict):
        body = json.dumps(payload, separators=(",", ":")).encode()
    else:
        body = payload
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def make_webhook_payload(**overrides) -> dict:
    """Create a standard webhook payload."""
    payload = {
        "event_name": "message",
        "timestamp": 1700000000000,
        "sender": {
            "user_id": "user_123",
            "name": "E2E User",
            "locale": "vi_VN",
        },
        "message": {
            "message_type": "text",
            "content": "help",
            "recipient_id": OA_ID,
        },
    }
    payload.update(overrides)
    return payload