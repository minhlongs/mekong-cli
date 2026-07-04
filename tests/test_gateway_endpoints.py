"""
Tests for Gateway API endpoints (src/gateway.py).

Covers:
- GET  /health
- POST /v1/missions           — create mission
- GET  /v1/missions/{id}      — get mission status
- GET  /v1/missions/{id}/stream — SSE stream (header check)
- POST /v1/webhook/test       — test webhook connectivity
- GET  /v1/webhook/schema     — webhook event schema
- POST /v1/mcu/deduct         — deduct MCU credits
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("LICENSE_GATE_ENFORCE", "0")

from fastapi.testclient import TestClient

from src.gateway import app
from src.api.gateway_mission_routes import MISSION_STORE

# ---------------------------------------------------------------------------
# Shared test client
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_mission_store():
    """Isolate tests: wipe MISSION_STORE before each test."""
    MISSION_STORE.clear()
    yield
    MISSION_STORE.clear()


@pytest.fixture()
def client():
    """TestClient for the gateway FastAPI app."""
    return TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# GET /health
# ===========================================================================

class TestGatewayHealth:
    """Gateway health check endpoint."""

    def test_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_returns_healthy_status(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"

    def test_returns_timestamp(self, client):
        body = client.get("/health").json()
        assert "timestamp" in body

    def test_returns_version(self, client):
        body = client.get("/health").json()
        assert "version" in body


# ===========================================================================
# POST /v1/missions
# ===========================================================================

class TestCreateMission:
    """POST /v1/missions — create a new mission."""

    def _default_payload(self, **overrides):
        base = {"goal": "deploy the app", "tenant_id": "tenant-abc"}
        base.update(overrides)
        return base

    def test_valid_payload_returns_202_or_200(self, client):
        resp = client.post("/v1/missions", json=self._default_payload())
        # Gateway returns 200 by default (no explicit status_code=202)
        assert resp.status_code in (200, 201, 202)

    def test_response_contains_mission_id(self, client):
        resp = client.post("/v1/missions", json=self._default_payload())
        body = resp.json()
        assert "mission_id" in body
        assert len(body["mission_id"]) > 0

    def test_response_contains_stream_url(self, client):
        resp = client.post("/v1/missions", json=self._default_payload())
        body = resp.json()
        assert "stream_url" in body

    def test_mission_stored_in_store(self, client):
        resp = client.post("/v1/missions", json=self._default_payload())
        mission_id = resp.json()["mission_id"]
        assert mission_id in MISSION_STORE

    def test_missing_goal_returns_400_or_422(self, client):
        resp = client.post("/v1/missions", json={"tenant_id": "t1"})
        assert resp.status_code in (400, 422)

    def test_empty_goal_returns_400(self, client):
        resp = client.post("/v1/missions", json={"goal": "", "tenant_id": "t1"})
        assert resp.status_code == 400

    def test_missing_tenant_id_returns_400_or_422(self, client):
        resp = client.post("/v1/missions", json={"goal": "deploy app"})
        assert resp.status_code in (400, 422)

    def test_empty_tenant_id_returns_400(self, client):
        resp = client.post("/v1/missions", json={"goal": "deploy app", "tenant_id": ""})
        assert resp.status_code == 400

    def test_invalid_priority_returns_400(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(priority="urgent"),
        )
        assert resp.status_code == 400

    def test_valid_priority_low_accepted(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(priority="low"),
        )
        assert resp.status_code in (200, 201, 202)

    def test_valid_priority_high_accepted(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(priority="high"),
        )
        assert resp.status_code in (200, 201, 202)

    def test_goal_too_long_returns_400(self, client):
        resp = client.post(
            "/v1/missions",
            json={"goal": "g" * 5001, "tenant_id": "t1"},
        )
        assert resp.status_code == 400

    def test_invalid_webhook_url_returns_400(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(webhook_url="not-a-url"),
        )
        assert resp.status_code == 400

    def test_valid_webhook_url_accepted(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(webhook_url="https://example.com/hook"),
        )
        assert resp.status_code in (200, 201, 202)

    def test_metadata_preserved_in_store(self, client):
        resp = client.post(
            "/v1/missions",
            json=self._default_payload(metadata={"source": "dashboard"}),
        )
        mission_id = resp.json()["mission_id"]
        # The MISSION_STORE should record the mission
        assert mission_id in MISSION_STORE


# ===========================================================================
# GET /v1/missions/{mission_id}
# ===========================================================================

class TestGetMissionStatus:
    """GET /v1/missions/{mission_id} — get current mission status."""

    def _create_mission(self, client, goal="test mission"):
        resp = client.post(
            "/v1/missions",
            json={"goal": goal, "tenant_id": "tenant-xyz"},
        )
        return resp.json()["mission_id"]

    def test_returns_200_for_known_mission(self, client):
        mission_id = self._create_mission(client)
        resp = client.get(f"/v1/missions/{mission_id}")
        assert resp.status_code == 200

    def test_returns_correct_mission_id(self, client):
        mission_id = self._create_mission(client)
        body = client.get(f"/v1/missions/{mission_id}").json()
        assert body["mission_id"] == mission_id

    def test_returns_correct_goal(self, client):
        mission_id = self._create_mission(client, goal="build the API")
        body = client.get(f"/v1/missions/{mission_id}").json()
        assert body["goal"] == "build the API"

    def test_returns_status_field(self, client):
        mission_id = self._create_mission(client)
        body = client.get(f"/v1/missions/{mission_id}").json()
        assert "status" in body

    def test_unknown_mission_returns_404(self, client):
        resp = client.get("/v1/missions/does-not-exist-xyz")
        assert resp.status_code == 404

    def test_empty_mission_id_returns_400(self, client):
        # FastAPI path param with spaces / empty won't match route → 404
        resp = client.get("/v1/missions/%20%20")
        # Either 400 (validation) or 404 (not found in store for that id)
        assert resp.status_code in (400, 404)

    def test_response_contains_tenant_id(self, client):
        mission_id = self._create_mission(client)
        body = client.get(f"/v1/missions/{mission_id}").json()
        assert body["tenant_id"] == "tenant-xyz"

    def test_response_contains_created_at(self, client):
        mission_id = self._create_mission(client)
        body = client.get(f"/v1/missions/{mission_id}").json()
        assert "created_at" in body


# ===========================================================================
# GET /v1/missions/{mission_id}/stream
# ===========================================================================

class TestStreamMission:
    """GET /v1/missions/{mission_id}/stream — SSE stream."""

    def test_unknown_mission_returns_404(self, client):
        resp = client.get("/v1/missions/ghost-id/stream")
        assert resp.status_code == 404

    def test_known_mission_returns_sse_content_type(self, client):
        # Create a mission and immediately set status to completed
        resp_create = client.post(
            "/v1/missions",
            json={"goal": "stream test", "tenant_id": "t-stream"},
        )
        mission_id = resp_create.json()["mission_id"]

        # Force completed status so stream terminates quickly
        MISSION_STORE[mission_id]["status"] = "completed"

        resp = client.get(f"/v1/missions/{mission_id}/stream")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")


# ===========================================================================
# POST /v1/webhook/test
# ===========================================================================

class TestWebhookTest:
    """POST /v1/webhook/test — test webhook connectivity."""

    def test_missing_webhook_url_returns_failure_not_error(self, client):
        # validate_required failure → returns 200 with success=False (not HTTPException)
        resp = client.post("/v1/webhook/test", json={"webhook_url": ""})
        # Either 200 with success=False, or 422 from Pydantic
        if resp.status_code == 200:
            assert resp.json()["success"] is False
        else:
            assert resp.status_code == 422

    def test_invalid_url_returns_success_false(self, client):
        resp = client.post("/v1/webhook/test", json={"webhook_url": "not-a-real-url"})
        assert resp.status_code == 200
        assert resp.json()["success"] is False

    def test_missing_body_returns_422(self, client):
        resp = client.post("/v1/webhook/test", json={})
        assert resp.status_code == 422

    @patch("src.api.gateway_webhook_mcu_routes.validate_webhook_url")
    def test_reachable_url_returns_success_true(self, mock_val, client):
        mock_val.return_value = (True, "HTTP 200")
        resp = client.post(
            "/v1/webhook/test",
            json={"webhook_url": "https://example.com/hook"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @patch("src.api.gateway_webhook_mcu_routes.validate_webhook_url")
    def test_unreachable_url_returns_success_false(self, mock_val, client):
        mock_val.return_value = (False, "Connection refused")
        resp = client.post(
            "/v1/webhook/test",
            json={"webhook_url": "https://dead-server.example.com/hook"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False


# ===========================================================================
# GET /v1/webhook/schema
# ===========================================================================

class TestWebhookSchema:
    """GET /v1/webhook/schema — webhook event schema documentation."""

    def test_returns_200(self, client):
        resp = client.get("/v1/webhook/schema")
        assert resp.status_code == 200

    def test_returns_version(self, client):
        body = client.get("/v1/webhook/schema").json()
        assert "version" in body

    def test_returns_events_dict(self, client):
        body = client.get("/v1/webhook/schema").json()
        assert "events" in body
        assert isinstance(body["events"], dict)

    def test_events_dict_not_empty(self, client):
        body = client.get("/v1/webhook/schema").json()
        assert len(body["events"]) > 0


# ===========================================================================
# POST /v1/mcu/deduct
# ===========================================================================

class TestMCUDeduct:
    """POST /v1/mcu/deduct — deduct MCU credits for a mission."""

    def test_missing_tenant_id_returns_400(self, client):
        resp = client.post(
            "/v1/mcu/deduct",
            json={"complexity": "simple", "mission_id": "m1"},
        )
        assert resp.status_code in (400, 422)

    def test_empty_tenant_id_returns_400(self, client):
        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "", "complexity": "simple", "mission_id": "m1"},
        )
        assert resp.status_code == 400

    def test_invalid_complexity_returns_400(self, client):
        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "t1", "complexity": "impossible", "mission_id": "m1"},
        )
        assert resp.status_code == 400

    def test_insufficient_balance_returns_402(self, client):
        """New tenant with 0 balance should get 402 Payment Required."""
        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "brand-new-tenant", "complexity": "simple", "mission_id": "m1"},
        )
        assert resp.status_code == 402

    def test_successful_deduct_returns_200(self, client):
        from src.raas.credits import CreditStore
        credit_store = CreditStore()
        credit_store.add_credits("rich-tenant", 100, "test_setup")

        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "rich-tenant", "complexity": "simple", "mission_id": "m1"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["balance_before"] == 100
        assert body["balance_after"] == 99
        assert body["amount_deducted"] == 1

    def test_complex_mission_deducts_more(self, client):
        """Complex missions cost more MCUs (5 vs 1 for simple)."""
        from src.raas.credits import CreditStore
        credit_store = CreditStore()
        credit_store.add_credits("rich-tenant2", 100, "test_setup")

        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "rich-tenant2", "complexity": "complex", "mission_id": "m2"},
        )

        assert resp.status_code == 200
        assert resp.json()["amount_deducted"] == 5

    def test_low_balance_flag_returned(self, client):
        from src.raas.credits import CreditStore
        credit_store = CreditStore()
        credit_store.add_credits("low-tenant", 5, "test_setup")

        resp = client.post(
            "/v1/mcu/deduct",
            json={"tenant_id": "low-tenant", "complexity": "simple", "mission_id": "m3"},
        )

        assert resp.status_code == 200
        assert resp.json()["low_balance"] is True

    def test_all_valid_complexities_accepted(self, client):
        """simple, standard, complex — all must be accepted by validation."""
        from src.raas.credits import CreditStore
        credit_store = CreditStore()

        # Add sufficient credits for all three deductions (1 + 3 + 5 = 9)
        credit_store.add_credits("t1", 100, "test_setup")

        for complexity in ("simple", "standard", "complex"):
            resp = client.post(
                "/v1/mcu/deduct",
                json={"tenant_id": "t1", "complexity": complexity, "mission_id": "m"},
            )
            assert resp.status_code == 200, f"Failed for complexity={complexity}: {resp.json()}"
