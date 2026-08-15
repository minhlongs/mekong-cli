"""
Tests for RaaS API endpoints: raas_router, license_server, quota_status, billing.

Covers:
- POST /v1/tasks — submit task
- GET  /v1/tasks/{id} — poll task status
- GET  /v1/agents — list agents
- POST /v1/agents/{name}/run — run agent
- POST /api/v1/license/validate — validate license
- GET  /health (license server)
- GET  /api/v1/license/stats
- GET  /v1/quota/status
- GET  /v1/quota/tiers
- GET  /v1/quota/history
- GET  /billing/health
- POST /billing/webhook/stripe
- POST /billing/webhook/polar
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from src.raas.auth import TenantContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = TenantContext(
    tenant_id="tenant-test-001",
    tenant_name="Test Tenant",
    api_key="mk_test_key",
)


def _make_require_tenant_override(tenant: TenantContext = _TENANT):
    """Return a dependency override that always resolves to *tenant*."""
    def _override():
        return tenant
    return _override


# ---------------------------------------------------------------------------
# RaaS Router app fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def raas_client():
    """TestClient for the RaaS router mounted on a bare FastAPI app."""
    from src.api.raas_router import router
    from src.api.raas_auth_middleware import require_tenant

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[require_tenant] = _make_require_tenant_override()

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# License server fixture
# ---------------------------------------------------------------------------

class _MockClientMiddleware(BaseHTTPMiddleware):
    """Inject a fake client IP so endpoints that read request.client.host work."""

    async def dispatch(self, request, call_next):
        request.scope["client"] = ("127.0.0.1", 9999)
        return await call_next(request)


@pytest.fixture()
def license_client():
    """TestClient for the license server. TestClient default client=('testclient', 50000)."""
    from src.api.license_server import app as _license_app
    return TestClient(_license_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Quota endpoints fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def quota_client():
    """TestClient for quota_router mounted on a bare FastAPI app."""
    from src.api.quota_status_endpoints import quota_router
    from src.api.raas_auth_middleware import require_tenant

    app = FastAPI()
    app.include_router(quota_router)
    app.dependency_overrides[require_tenant] = _make_require_tenant_override()

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Billing endpoints fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def billing_client():
    """TestClient for billing_router mounted on a bare FastAPI app."""
    from src.api.billing_endpoints import billing_router

    app = FastAPI()
    app.include_router(billing_router)

    return TestClient(app, raise_server_exceptions=False)


# ===========================================================================
# Tests: POST /v1/tasks
# ===========================================================================

class TestSubmitTask:
    """POST /v1/tasks — submit a goal for execution."""

    def test_empty_goal_returns_400_or_422(self, raas_client):
        # Pydantic min_length=1 → 422; our validate_required → 400
        resp = raas_client.post("/v1/tasks", json={"goal": ""})
        assert resp.status_code in (400, 422)

    def test_missing_goal_field_returns_422(self, raas_client):
        resp = raas_client.post("/v1/tasks", json={})
        assert resp.status_code == 422

    def test_goal_too_long_returns_400(self, raas_client):
        resp = raas_client.post("/v1/tasks", json={"goal": "x" * 10001})
        assert resp.status_code == 400

    def test_no_auth_header_returns_401(self):
        """Without dependency override, missing auth → 401."""
        from src.api.raas_router import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/tasks", json={"goal": "deploy app"})
        assert resp.status_code == 401

    def test_happy_path_returns_202_with_task_id(self, raas_client):
        """Valid goal should return 202 with task_id and tenant_id."""
        mock_result = MagicMock()
        mock_result.status = MagicMock()
        mock_result.status.name = "SUCCESS"

        from src.core import orchestrator as orch_mod
        mock_result.status = orch_mod.OrchestrationStatus.SUCCESS
        mock_result.total_steps = 2
        mock_result.completed_steps = 2
        mock_result.failed_steps = 0
        mock_result.success_rate = 1.0
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.step_results = []

        with patch("src.api.raas_router._build_orchestrator") as mock_orch:
            instance = MagicMock()
            instance.run_from_goal.return_value = mock_result
            mock_orch.return_value = instance

            resp = raas_client.post("/v1/tasks", json={"goal": "deploy the app"})

        assert resp.status_code == 202
        body = resp.json()
        assert "task_id" in body
        assert body["tenant_id"] == "tenant-test-001"

    def test_orchestrator_exception_returns_202_with_failed_status(self, raas_client):
        """Orchestrator crash → task persisted as FAILED, still returns 202."""
        with patch("src.api.raas_router._build_orchestrator") as mock_orch:
            instance = MagicMock()
            instance.run_from_goal.side_effect = RuntimeError("LLM unavailable")
            mock_orch.return_value = instance

            resp = raas_client.post("/v1/tasks", json={"goal": "some goal"})

        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "failed"

    def test_whitespace_only_goal_returns_400(self, raas_client):
        """Whitespace-only goal should be rejected."""
        resp = raas_client.post("/v1/tasks", json={"goal": "   "})
        # Pydantic min_length=1 should catch this or our validate_required
        assert resp.status_code in (400, 422)


# ===========================================================================
# Tests: GET /v1/tasks/{task_id}
# ===========================================================================

class TestGetTaskStatus:
    """GET /v1/tasks/{task_id} — poll task status."""

    def test_unknown_task_returns_404(self, raas_client):
        resp = raas_client.get("/v1/tasks/nonexistent-task-id")
        assert resp.status_code == 404

    def test_no_auth_returns_401(self):
        from src.api.raas_router import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/tasks/some-id")
        assert resp.status_code == 401

    def test_existing_task_returns_200_with_correct_fields(self, raas_client):
        """Submit a task then poll for status — should return full status response."""
        mock_result = MagicMock()
        from src.core import orchestrator as orch_mod
        mock_result.status = orch_mod.OrchestrationStatus.SUCCESS
        mock_result.total_steps = 1
        mock_result.completed_steps = 1
        mock_result.failed_steps = 0
        mock_result.success_rate = 1.0
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.step_results = []
        mock_result.structured_output = {"result": "success"}

        with patch("src.api.raas_router._build_orchestrator") as mock_orch:
            instance = MagicMock()
            instance.run_from_goal.return_value = mock_result
            mock_orch.return_value = instance

            submit = raas_client.post("/v1/tasks", json={"goal": "test goal"})
        assert submit.status_code == 202
        task_id = submit.json()["task_id"]

        poll = raas_client.get(f"/v1/tasks/{task_id}")
        assert poll.status_code == 200
        body = poll.json()
        assert body["task_id"] == task_id
        assert body["goal"] == "test goal"
        assert body["tenant_id"] == "tenant-test-001"
        assert "status" in body

    def test_tenant_isolation_returns_404_for_other_tenant(self, raas_client):
        """A task created by one tenant must not be visible to another tenant."""
        mock_result = MagicMock()
        from src.core import orchestrator as orch_mod
        mock_result.status = orch_mod.OrchestrationStatus.SUCCESS
        mock_result.total_steps = 0
        mock_result.completed_steps = 0
        mock_result.failed_steps = 0
        mock_result.success_rate = 1.0
        mock_result.errors = []
        mock_result.warnings = []
        mock_result.step_results = []

        with patch("src.api.raas_router._build_orchestrator") as mock_orch:
            instance = MagicMock()
            instance.run_from_goal.return_value = mock_result
            mock_orch.return_value = instance

            submit = raas_client.post("/v1/tasks", json={"goal": "isolated goal"})
        task_id = submit.json()["task_id"]

        # Create a client for a different tenant
        from src.api.raas_router import router
        from src.api.raas_auth_middleware import require_tenant
        other_tenant = TenantContext(
            tenant_id="tenant-other-999",
            tenant_name="Other Tenant",
            api_key="mk_other",
        )
        app2 = FastAPI()
        app2.include_router(router)
        app2.dependency_overrides[require_tenant] = _make_require_tenant_override(other_tenant)
        other_client = TestClient(app2, raise_server_exceptions=False)

        resp = other_client.get(f"/v1/tasks/{task_id}")
        assert resp.status_code == 404


# ===========================================================================
# Tests: GET /v1/agents
# ===========================================================================

class TestListAgents:
    """GET /v1/agents — list registered agents."""

    def test_returns_200_list(self, raas_client):
        mock_reg = MagicMock()
        mock_reg.list_agents.return_value = ["git", "file"]
        mock_cls = MagicMock()
        mock_cls.__doc__ = "A test agent"
        mock_reg.get.return_value = mock_cls

        with patch("src.agents.registry", mock_reg):
            resp = raas_client.get("/v1/agents")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_no_auth_returns_401(self):
        from src.api.raas_router import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/agents")
        assert resp.status_code == 401

    def test_empty_registry_returns_empty_list(self, raas_client):
        mock_reg = MagicMock()
        mock_reg.list_agents.return_value = []
        with patch("src.agents.registry", mock_reg):
            resp = raas_client.get("/v1/agents")
        assert resp.status_code == 200
        assert resp.json() == []


# ===========================================================================
# Tests: POST /v1/agents/{name}/run
# ===========================================================================

class TestRunAgent:
    """POST /v1/agents/{name}/run — run a named agent."""

    def _make_mock_registry(self, agent_name: str, agent_instance=None):
        """Build a mock AgentRegistry that contains *agent_name*."""
        mock_reg = MagicMock()
        mock_reg.__contains__ = lambda self, x: x == agent_name
        mock_reg.list_agents.return_value = [agent_name]
        if agent_instance is not None:
            mock_reg.get.return_value = MagicMock(return_value=agent_instance)
        return mock_reg

    def test_unknown_agent_returns_404(self, raas_client):
        mock_reg = MagicMock()
        mock_reg.__contains__ = lambda self, x: False
        mock_reg.list_agents.return_value = []

        with patch("src.agents.registry", mock_reg):
            resp = raas_client.post(
                "/v1/agents/no-such-agent/run",
                json={"goal": "do something"},
            )
        assert resp.status_code == 404

    def test_missing_goal_returns_422(self, raas_client):
        resp = raas_client.post("/v1/agents/git/run", json={})
        assert resp.status_code == 422

    def test_empty_goal_returns_400_or_422(self, raas_client):
        # Pydantic min_length=1 → 422, or validate_required → 400
        resp = raas_client.post("/v1/agents/git/run", json={"goal": ""})
        assert resp.status_code in (400, 422)

    def test_no_auth_returns_401(self):
        from src.api.raas_router import router
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/v1/agents/git/run", json={"goal": "run git"})
        assert resp.status_code == 401

    def test_happy_path_returns_200(self, raas_client):
        mock_agent = MagicMock()
        mock_agent.plan.return_value = {"steps": []}
        mock_agent.execute.return_value = "git status output"

        mock_reg = self._make_mock_registry("git", mock_agent)

        with patch("src.agents.registry", mock_reg):
            resp = raas_client.post(
                "/v1/agents/git/run",
                json={"goal": "check git status"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["agent"] == "git"
        assert body["status"] == "success"
        assert "git status output" in body["output"]

    def test_agent_timeout_returns_504(self, raas_client):
        mock_agent = MagicMock()
        mock_agent.plan.side_effect = TimeoutError("agent timed out")

        mock_reg = self._make_mock_registry("slow", mock_agent)

        with patch("src.agents.registry", mock_reg):
            resp = raas_client.post(
                "/v1/agents/slow/run",
                json={"goal": "slow task"},
            )
        assert resp.status_code == 504

    def test_agent_runtime_error_returns_500(self, raas_client):
        mock_agent = MagicMock()
        mock_agent.plan.return_value = {}
        mock_agent.execute.side_effect = RuntimeError("execution blew up")

        mock_reg = self._make_mock_registry("git", mock_agent)

        with patch("src.agents.registry", mock_reg):
            resp = raas_client.post(
                "/v1/agents/git/run",
                json={"goal": "explode"},
            )
        assert resp.status_code == 500


# ===========================================================================
# Tests: License Server
# ===========================================================================

class TestLicenseServerHealth:
    """GET /health — license server health check."""

    def test_health_returns_200(self, license_client):
        resp = license_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert "timestamp" in body


class TestLicenseServerStats:
    """GET /api/v1/license/stats — license validation statistics."""

    def test_stats_returns_200(self, license_client):
        resp = license_client.get("/api/v1/license/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "active_rate_limits" in body
        assert "timestamp" in body


class TestLicenseValidate:
    """POST /api/v1/license/validate — license key validation."""

    def test_missing_body_returns_422(self, license_client):
        resp = license_client.post("/api/v1/license/validate", json={})
        assert resp.status_code == 422

    def test_invalid_license_returns_valid_false(self, license_client):
        import src.api.license_server as _ls
        with patch.object(_ls, "check_rate_limit", return_value=True):
            with patch.object(_ls, "validate_license", return_value=(False, None, "Invalid signature")):
                resp = license_client.post(
                    "/api/v1/license/validate",
                    json={"license_key": "INVALID-KEY"},
                )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is False
        assert body["error"] == "Invalid signature"

    def test_valid_license_returns_tier_info(self, license_client):
        import src.api.license_server as _ls
        with patch.object(_ls, "check_rate_limit", return_value=True):
            with patch.object(_ls, "validate_license", return_value=(True, {"tier": "pro", "key_id": "k1"}, None)):
                with patch.object(_ls, "get_revoked_keys", return_value=set()):
                    with patch.object(_ls, "get_tier_limits", return_value={"commands_per_day": 1000}):
                        resp = license_client.post(
                            "/api/v1/license/validate",
                            json={"license_key": "MK-PRO-123"},
                        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is True
        assert body["tier"] == "pro"
        assert body["key_id"] == "k1"
        assert body["daily_limit"] == 1000

    def test_revoked_license_returns_valid_false(self, license_client):
        import src.api.license_server as _ls
        with patch.object(_ls, "check_rate_limit", return_value=True):
            with patch.object(_ls, "validate_license", return_value=(True, {"tier": "pro", "key_id": "revoked-k"}, None)):
                with patch.object(_ls, "get_revoked_keys", return_value={"revoked-k"}):
                    resp = license_client.post(
                        "/api/v1/license/validate",
                        json={"license_key": "MK-REVOKED"},
                    )
        assert resp.status_code == 200
        body = resp.json()
        assert body["valid"] is False
        assert "revoked" in body["error"].lower()

    def test_wrong_api_token_returns_401(self, license_client):
        import os
        import src.api.license_server as _ls
        with patch.object(_ls, "check_rate_limit", return_value=True):
            with patch.dict(os.environ, {"RAAS_API_TOKEN": "secret-token"}):
                resp = license_client.post(
                    "/api/v1/license/validate",
                    headers={"Authorization": "Bearer wrong-token"},
                    json={"license_key": "MK-TEST"},
                )
        assert resp.status_code == 401

    def test_rate_limit_exceeded_returns_429(self, license_client):
        import src.api.license_server as _ls
        with patch.object(_ls, "check_rate_limit", return_value=False):
            resp = license_client.post(
                "/api/v1/license/validate",
                json={"license_key": "MK-TEST"},
            )
        assert resp.status_code == 429


# ===========================================================================
# Tests: Quota Endpoints
# ===========================================================================

class TestQuotaStatus:
    """GET /v1/quota/status — real-time quota for authenticated tenant."""

    def test_returns_200_with_usage_fields(self, quota_client):
        mock_balance = {
            "plan": "pro",
            "mcu_used": 150,
            "mcu_limit": 1000,
            "mcu_remaining": 850,
            "overage_credits": 0,
            "overage_charges_usd": 0.0,
        }
        mock_overage = MagicMock()
        mock_overage.allow_overage = True
        mock_overage.overage_rate_per_credit = 0.01
        mock_overage.max_overage_credits = 500
        mock_overage.warning_threshold_pct = 80

        with patch("src.api.quota_status_endpoints.get_billing_service") as mock_svc:
            svc = MagicMock()
            svc.get_balance.return_value = mock_balance
            mock_svc.return_value = svc
            with patch("src.api.quota_status_endpoints.get_overage_config") as mock_oc:
                mock_oc.return_value = mock_overage

                resp = quota_client.get("/v1/quota/status")

        assert resp.status_code == 200
        body = resp.json()
        assert body["tenant_id"] == "tenant-test-001"
        assert body["tier"] == "pro"
        assert "usage" in body
        assert "overage" in body
        assert "warnings" in body

    def test_approaching_limit_flag_true_when_near_cap(self, quota_client):
        mock_balance = {
            "plan": "free",
            "mcu_used": 90,
            "mcu_limit": 100,
            "mcu_remaining": 10,
            "overage_credits": 0,
            "overage_charges_usd": 0.0,
        }
        mock_overage = MagicMock()
        mock_overage.allow_overage = False
        mock_overage.overage_rate_per_credit = 0.0
        mock_overage.max_overage_credits = 0
        mock_overage.warning_threshold_pct = 80  # 90% used → should trigger

        with patch("src.api.quota_status_endpoints.get_billing_service") as mock_svc:
            svc = MagicMock()
            svc.get_balance.return_value = mock_balance
            mock_svc.return_value = svc
            with patch("src.api.quota_status_endpoints.get_overage_config") as mock_oc:
                mock_oc.return_value = mock_overage

                resp = quota_client.get("/v1/quota/status")

        assert resp.status_code == 200
        assert resp.json()["warnings"]["approaching_limit"] is True


class TestQuotaTiers:
    """GET /v1/quota/tiers — list all tier limits (public)."""

    def test_returns_200_with_tiers(self, quota_client):

        mock_overage = MagicMock()
        mock_overage.allow_overage = False
        mock_overage.overage_rate_per_credit = 0.0
        mock_overage.max_overage_credits = 0
        mock_overage.warning_threshold_pct = 80

        with patch("src.api.quota_status_endpoints.get_overage_config") as mock_oc:
            mock_oc.return_value = mock_overage
            resp = quota_client.get("/v1/quota/tiers")

        assert resp.status_code == 200
        body = resp.json()
        assert "tiers" in body


class TestQuotaHistory:
    """GET /v1/quota/history — usage history for authenticated tenant."""

    def test_returns_200_with_history(self, quota_client):
        mock_balance = {"plan": "pro"}
        mock_history = [{"event": "api_call", "value": 1}]

        with patch("src.api.quota_status_endpoints.get_billing_service") as mock_svc:
            svc = MagicMock()
            svc.get_balance.return_value = mock_balance
            svc.get_history.return_value = mock_history
            mock_svc.return_value = svc

            resp = quota_client.get("/v1/quota/history")

        assert resp.status_code == 200
        body = resp.json()
        assert body["tenant_id"] == "tenant-test-001"
        assert "entries" in body
        assert body["total_entries"] == 1

    def test_limit_param_forwarded(self, quota_client):
        mock_balance = {"plan": "free"}

        with patch("src.api.quota_status_endpoints.get_billing_service") as mock_svc:
            svc = MagicMock()
            svc.get_balance.return_value = mock_balance
            svc.get_history.return_value = []
            mock_svc.return_value = svc

            quota_client.get("/v1/quota/history?limit=10")
            svc.get_history.assert_called_once_with("tenant-test-001", limit=10)


# ===========================================================================
# Tests: Billing Endpoints
# ===========================================================================

class TestBillingHealth:
    """GET /billing/health — billing service health check."""

    def test_returns_200_healthy(self, billing_client):
        resp = billing_client.get("/billing/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "healthy"
        assert body["service"] == "mekong-billing"


class TestStripeWebhook:
    """POST /billing/webhook/stripe — Stripe webhook handler."""

    def test_valid_payload_returns_received(self, billing_client):
        resp = billing_client.post(
            "/billing/webhook/stripe",
            json={"type": "invoice.payment_succeeded", "data": {}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "received"
        assert body["event_type"] == "invoice.payment_succeeded"

    def test_invalid_json_returns_400(self, billing_client):
        resp = billing_client.post(
            "/billing/webhook/stripe",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    def test_invalid_signature_returns_401(self, billing_client):
        import os

        secret = "test-webhook-secret"
        payload = b'{"type":"invoice.payment_failed"}'
        bad_sig = "sha256=invalidsignature"

        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": secret}):
            resp = billing_client.post(
                "/billing/webhook/stripe",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": bad_sig,
                },
            )
        assert resp.status_code == 401

    def test_valid_signature_accepted(self, billing_client):
        import os
        import hmac
        from hashlib import sha256

        secret = "test-webhook-secret"
        payload = b'{"type": "invoice.payment_succeeded"}'
        sig = f"sha256={hmac.new(secret.encode(), payload, sha256).hexdigest()}"

        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": secret}):
            resp = billing_client.post(
                "/billing/webhook/stripe",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig,
                },
            )
        assert resp.status_code == 200


class TestPolarWebhook:
    """POST /billing/webhook/polar — Polar webhook handler."""

    def test_valid_payload_returns_received(self, billing_client):
        resp = billing_client.post(
            "/billing/webhook/polar",
            json={"type": "order.paid", "data": {}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "received"
        assert body["event_type"] == "order.paid"

    def test_invalid_signature_returns_401(self, billing_client):
        import os

        with patch.dict(os.environ, {"POLAR_WEBHOOK_SECRET": "polar-secret"}):
            resp = billing_client.post(
                "/billing/webhook/polar",
                json={"type": "order.refunded"},
                headers={"webhook-signature": "sha256=bad"},
            )
        assert resp.status_code == 401

    def test_unknown_event_type_still_200(self, billing_client):
        resp = billing_client.post(
            "/billing/webhook/polar",
            json={"type": "some.unknown.event"},
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "some.unknown.event"
