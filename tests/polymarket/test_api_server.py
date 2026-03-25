"""Tests for CashClaw API server — auth, rate limiting, endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.polymarket.api_server import router, _rate_limit_store


@pytest.fixture
def client():
    """Create test client."""
    app = FastAPI()
    app.include_router(router)
    _rate_limit_store.clear()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Standard auth headers."""
    return {"Authorization": "Bearer test-api-key"}


class TestHealthCheck:
    """Test /v1/health endpoint."""

    def test_health_no_auth(self, client: TestClient) -> None:
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "timestamp" in data


class TestPublicSignals:
    """Test /public/signals endpoint."""

    def test_public_signals_no_auth(self, client: TestClient) -> None:
        resp = client.get("/public/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert "upgrade_url" in data

    def test_public_signals_rate_limited(self, client: TestClient) -> None:
        for _ in range(10):
            client.get("/public/signals")
        resp = client.get("/public/signals")
        assert resp.status_code == 429


class TestAuthentication:
    """Test API key authentication."""

    def test_no_auth_header_401(self, client: TestClient) -> None:
        resp = client.get("/v1/markets")
        assert resp.status_code == 401

    def test_empty_bearer_401(self, client: TestClient) -> None:
        resp = client.get("/v1/markets", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401

    def test_valid_bearer_succeeds(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/markets", headers=auth_headers)
        assert resp.status_code == 200

    def test_invalid_format_401(self, client: TestClient) -> None:
        resp = client.get("/v1/markets", headers={"Authorization": "Basic abc"})
        assert resp.status_code == 401


class TestRateLimiting:
    """Test tier-based rate limiting."""

    def test_within_limit_succeeds(self, client: TestClient, auth_headers: dict) -> None:
        for _ in range(5):
            resp = client.get("/v1/markets", headers=auth_headers)
            assert resp.status_code == 200

    def test_exceeds_limit_429(self, client: TestClient) -> None:
        headers = {"Authorization": "Bearer rate-test-key"}
        # Starter limit is 100/hr, flood it
        for _ in range(100):
            client.get("/v1/markets", headers=headers)
        resp = client.get("/v1/markets", headers=headers)
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()


class TestMarkets:
    """Test /v1/markets endpoint."""

    def test_returns_markets(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/markets", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "markets" in data
        assert "tier" in data


class TestSignals:
    """Test /v1/signals endpoint."""

    def test_returns_signals(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/signals", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "signals" in data
        assert "tier" in data

    def test_limit_parameter(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/signals?limit=3", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["max_signals"] <= 5  # Starter limit


class TestPredict:
    """Test /v1/predict/{market_id} endpoint."""

    def test_predict_market(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/predict/m1", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["market_id"] == "m1"
        assert "tier" in data


class TestPaperTrading:
    """Test paper trading endpoints."""

    def test_paper_start(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post("/v1/paper/start", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["mode"] == "paper"

    def test_paper_status(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/paper/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert "capital" in data

    def test_paper_stop(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.post("/v1/paper/stop", headers=auth_headers)
        assert resp.status_code == 200


class TestPipelineStatus:
    """Test /v1/status endpoint."""

    def test_status(self, client: TestClient, auth_headers: dict) -> None:
        resp = client.get("/v1/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "PAPER"
        assert "circuit_breaker" in data
