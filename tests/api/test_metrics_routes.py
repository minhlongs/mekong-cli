# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for the Prometheus /metrics endpoint (src/api/metrics_routes.py).

Covers:
- Bearer-token gate behaviour (absent token, wrong token, valid token)
- Prometheus exposition-format output (HELP/TYPE lines, label rendering)
- Subsystem failure tolerance (MCU billing error, PEV collector error)
"""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.metrics_routes import _build_metrics_text, _prom_line, router

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def _make_app() -> TestClient:
    """Mount the metrics router on a fresh FastAPI app.

    The router functions import ``src.gateway`` lazily inside the request
    handler, so the app itself stays cheap to construct.
    """
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# --------------------------------------------------------------------------- #
# _prom_line — Prometheus text format building blocks
# --------------------------------------------------------------------------- #


def test_prom_line_without_labels():
    line = _prom_line("up", None, 1.0, "Service is up", "gauge")

    assert line == "# HELP up Service is up\n# TYPE up gauge\nup 1.0\n"


def test_prom_line_with_labels():
    line = _prom_line(
        "pipelines_total", {"status": "success"}, 3.0,
        "Total pipelines", "counter",
    )

    assert '# HELP pipelines_total Total pipelines\n' in line
    assert '# TYPE pipelines_total counter\n' in line
    assert 'pipelines_total{status="success"} 3.0\n' in line


def test_prom_line_with_multiple_labels():
    line = _prom_line(
        "jobs", {"tenant": "acme", "state": "done"}, 2.0, "Jobs", "gauge",
    )

    assert 'jobs{tenant="acme",state="done"} 2.0\n' in line


# --------------------------------------------------------------------------- #
# Token gate on GET /metrics
# --------------------------------------------------------------------------- #


@pytest.fixture
def _no_auth_token(monkeypatch):
    monkeypatch.delenv("METRICS_AUTH_TOKEN", raising=False)


@pytest.fixture
def _auth_token(monkeypatch):
    monkeypatch.setenv("METRICS_AUTH_TOKEN", "sekret")


def test_metrics_open_without_token_set(_no_auth_token):
    client = _make_app()

    resp = client.get("/metrics")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == CONTENT_TYPE
    assert "# HELP mekong_mcu_tenant_count" in resp.text


def test_metrics_rejects_missing_bearer(_auth_token):
    client = _make_app()

    resp = client.get("/metrics")

    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthorized"}


def test_metrics_rejects_wrong_bearer(_auth_token):
    client = _make_app()

    resp = client.get(
        "/metrics", headers={"Authorization": "Bearer nope"}
    )

    assert resp.status_code == 401
    assert resp.json() == {"error": "unauthorized"}


def test_metrics_rejects_non_bearer_scheme(_auth_token):
    client = _make_app()

    resp = client.get("/metrics", headers={"Authorization": "Basic sekret"})

    assert resp.status_code == 401


def test_metrics_accepts_valid_bearer(_auth_token):
    client = _make_app()

    resp = client.get("/metrics", headers={"Authorization": "Bearer sekret"})

    assert resp.status_code == 200
    assert "# HELP mekong_gateway_uptime_seconds" in resp.text


# --------------------------------------------------------------------------- #
# _build_metrics_text — subsystem collection
# --------------------------------------------------------------------------- #


def _fake_gateway(start_time: float = 0.0, tenant_count: int = 4):
    """Build a fake ``src.gateway`` module with the attrs the builder reads."""
    mod = MagicMock()
    mod._APP_START_TIME = start_time
    mod.mcu_billing = MagicMock(tenant_count=tenant_count)
    return mod


def _fake_pev_collector(successful=5, failed=1, rate=0.83, avg_ms=120.5):
    collector = MagicMock()
    collector.get_global_metrics.return_value = {
        "total_successful": successful,
        "total_failed": failed,
        "overall_success_rate": rate,
        "avg_duration_ms": avg_ms,
    }
    collector_mod = MagicMock()
    collector_mod.get_pev_metrics.return_value = collector
    return collector_mod


def test_build_metrics_text_includes_all_core_blocks():
    with patch.dict(
        "sys.modules", {"src.gateway": _fake_gateway(tenant_count=7)}
    ), patch.dict(
        "sys.modules", {"src.core.pev_metrics_collector": _fake_pev_collector()}
    ):
        text = _build_metrics_text(start_time=0.0)

    assert "# HELP mekong_mcu_tenant_count" in text
    assert "mekong_mcu_tenant_count 7.0" in text
    assert "# HELP mekong_gateway_uptime_seconds" in text
    assert '# TYPE mekong_pev_pipelines_total counter' in text
    assert 'mekong_pev_pipelines_total{status="success"} 5.0' in text
    assert 'mekong_pev_pipelines_total{status="failed"} 1.0' in text
    assert "mekong_pev_success_rate 0.83" in text
    assert "mekong_pev_avg_duration_ms 120.5" in text


def test_build_metrics_text_survives_billing_failure():
    broken_billing = MagicMock()
    broken_billing.mcu_billing = MagicMock()
    broken_billing.mcu_billing.tenant_count = PropertyMock(
        side_effect=RuntimeError("db gone")
    )

    with patch.dict(
        "sys.modules", {"src.gateway": broken_billing}
    ), patch.dict(
        "sys.modules", {"src.core.pev_metrics_collector": _fake_pev_collector()}
    ):
        text = _build_metrics_text(start_time=0.0)

    # Tenant count falls back to 0 rather than crashing the endpoint.
    assert "mekong_mcu_tenant_count 0.0" in text


def test_build_metrics_text_survives_pev_failure():
    broken_pev = MagicMock()
    broken_pev.get_pev_metrics.side_effect = RuntimeError("collector down")

    with patch.dict(
        "sys.modules", {"src.gateway": _fake_gateway()}
    ), patch.dict(
        "sys.modules", {"src.core.pev_metrics_collector": broken_pev}
    ):
        text = _build_metrics_text(start_time=0.0)

    # PEV lines are omitted but core metrics still render.
    assert "mekong_mcu_tenant_count" in text
    assert "mekong_pev_pipelines_total" not in text
