"""Tests for public signals API — free tier, rate limiting, performance data."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.polymarket.public_signals import router, _ip_requests


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    _ip_requests.clear()
    return TestClient(app)


class TestPublicSignals:
    """Test /public/signals endpoint."""

    def test_returns_signal(self, client: TestClient) -> None:
        resp = client.get("/public/signals")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "free"
        assert data["signals_shown"] == 1
        assert "upgrade_cta" in data
        assert "pricing_url" in data

    def test_rate_limited(self, client: TestClient) -> None:
        for _ in range(10):
            client.get("/public/signals")
        resp = client.get("/public/signals")
        assert resp.status_code == 429
        assert "rate limit" in resp.json()["detail"].lower()


class TestPublicPerformance:
    """Test /public/performance endpoint."""

    def test_returns_performance(self, client: TestClient) -> None:
        resp = client.get("/public/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "performance" in data
        perf = data["performance"]
        assert "total_trades" in perf
        assert "win_rate" in perf

    def test_rate_limited(self, client: TestClient) -> None:
        for _ in range(30):
            client.get("/public/performance")
        resp = client.get("/public/performance")
        assert resp.status_code == 429


class TestPublicCalibration:
    """Test /public/calibration endpoint."""

    def test_returns_calibration(self, client: TestClient) -> None:
        resp = client.get("/public/calibration")
        assert resp.status_code == 200
        data = resp.json()
        assert "calibration" in data
        cal = data["calibration"]
        assert "bins" in cal
        assert "sample_size" in cal

    def test_empty_calibration(self, client: TestClient) -> None:
        resp = client.get("/public/calibration")
        data = resp.json()
        assert data["calibration"]["sample_size"] == 0
