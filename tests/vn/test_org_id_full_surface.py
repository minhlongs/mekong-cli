"""
Tests for Phase 8 P02 — org_id wiring on convert/revenue/export surfaces.

Covers:
- POST /convert?org_id=acme writes acme-scoped record
- POST /convert without org_id defaults to "default"
- GET /revenue?org_id=acme returns acme MRR only (no cross-tenant)
- GET /revenue without org_id defaults to "default"
- GET /export/misa?org_id=acme exports acme rows only + org in filename
- JWT with allowed_orgs=["acme"] calling ?org_id=other → 403
- JWT with allowed_orgs=["*"] → can write to any org
- Legacy token (no org constraint) → writes to requested org_id
- Cross-tenant user_id collision: acme/user_x and beta/user_x are isolated
- Revenue response includes "org_id" field
- Legacy conversions (no org_id field) counted in "default" org
- MISA export filename includes org_id segment
- Invalid org_id query param → 422
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_routes as vpr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEGACY_TOKEN = "legacy-admin-token-xyz"
JWT_SECRET=REDACTED = "test-jwt-secret-32-bytes-padding!!"

SIGNUP_BASE: dict[str, Any] = {
    "name": "Test User",
    "zalo": "+84909000001",  # overridden per-call
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "test",
    "source": "smoke_test",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jwt(
    *,
    scopes: list[str] | None = None,
    allowed_orgs: list[str] | None = None,
    exp_offset: int = 3600,
) -> str:
    """Issue a test JWT with configurable claims."""
    if scopes is None:
        scopes = ["founder"]
    if allowed_orgs is None:
        allowed_orgs = ["default"]
    now = int(time.time())
    payload = {
        "sub": "tester",
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(payload, JWT_SECRET=REDACTED, algorithm="HS256")


def _signup(
    client: TestClient,
    zalo: str,
    name: str = "User",
    org_id: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {**SIGNUP_BASE, "zalo": zalo, "name": name}
    if org_id is not None:
        payload["org_id"] = org_id
    r = client.post("/v1/pilot/signup", json=payload)
    assert r.status_code == 201, f"signup failed: {r.status_code} {r.text[:200]}"
    return r.json()


def _convert(
    client: TestClient,
    user_id: str,
    tier: str = "starter",
    monthly_vnd: int = 199000,
    org_id: str | None = None,
    token: str = LEGACY_TOKEN,
) -> "requests.Response":  # type: ignore[name-defined]  # noqa: F821
    params = {}
    if org_id is not None:
        params["org_id"] = org_id
    return client.post(
        "/v1/pilot/convert",
        json={"user_id": user_id, "tier": tier, "monthly_vnd": monthly_vnd},
        params=params,
        headers={"Authorization": f"Bearer {token}"},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Isolated CONFIG_DIR, legacy token + JWT secret configured."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", LEGACY_TOKEN)
    monkeypatch.setenv("MEKONG_JWT_SECRET=REDACTED", JWT_SECRET=REDACTED)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# TestConvertOrgId
# ---------------------------------------------------------------------------

class TestConvertOrgId:
    def test_convert_with_org_id_writes_scoped_record(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """convert?org_id=acme writes conversion with org_id=acme."""
        body = _signup(client, "+84909100001", org_id="acme")
        uid = body["user_id"]

        resp = _convert(client, uid, org_id="acme")
        assert resp.status_code == 201

        data = resp.json()
        assert data["org_id"] == "acme"
        assert data["is_new"] is True

        # Verify file contents
        conv_file = tmp_path / "conversions.jsonl"
        record = json.loads(conv_file.read_text(encoding="utf-8").strip())
        assert record["org_id"] == "acme"
        assert record["user_id"] == uid

    def test_convert_without_org_id_defaults_to_default(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """convert without org_id param → record gets org_id='default'."""
        body = _signup(client, "+84909100002")  # default org
        uid = body["user_id"]

        resp = _convert(client, uid)  # no org_id
        assert resp.status_code == 201
        assert resp.json()["org_id"] == "default"

    def test_convert_cross_org_user_id_returns_404(
        self, client: TestClient
    ) -> None:
        """User in acme org is unknown to beta org → 404 with informative detail."""
        body = _signup(client, "+84909100003", org_id="acme")
        uid = body["user_id"]

        # Try to convert acme user under beta org
        resp = _convert(client, uid, org_id="beta")
        assert resp.status_code == 404
        assert "beta" in resp.json()["detail"]

    def test_invalid_org_id_pattern_returns_422(self, client: TestClient) -> None:
        """org_id with uppercase → 422 validation error."""
        body = _signup(client, "+84909100004")
        uid = body["user_id"]
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            params={"org_id": "INVALID_ORG"},
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 422

    def test_jwt_wrong_org_returns_403(self, client: TestClient) -> None:
        """JWT with allowed_orgs=['acme'] calling ?org_id=beta → 403."""
        body = _signup(client, "+84909100005", org_id="acme")
        uid = body["user_id"]

        token = _make_jwt(scopes=["founder"], allowed_orgs=["acme"])
        resp = _convert(client, uid, org_id="beta", token=token)
        assert resp.status_code == 403

    def test_jwt_wildcard_org_allows_any_org(self, client: TestClient) -> None:
        """JWT with allowed_orgs=['*'] can convert into any org."""
        body = _signup(client, "+84909100006", org_id="acme")
        uid = body["user_id"]

        token = _make_jwt(scopes=["founder"], allowed_orgs=["*"])
        resp = _convert(client, uid, org_id="acme", token=token)
        assert resp.status_code == 201
        assert resp.json()["org_id"] == "acme"

    def test_legacy_token_writes_to_requested_org(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Legacy token (no org constraint in JWT) writes to org passed in query."""
        body = _signup(client, "+84909100007", org_id="myorg")
        uid = body["user_id"]

        resp = _convert(client, uid, org_id="myorg", token=LEGACY_TOKEN)
        assert resp.status_code == 201
        assert resp.json()["org_id"] == "myorg"

    def test_cross_tenant_user_id_collision_isolation(
        self, client: TestClient
    ) -> None:
        """Same Zalo in acme and beta → different user_ids; each scoped independently."""
        body_a = _signup(client, "+84909100008", name="Acme User", org_id="acme")
        body_b = _signup(client, "+84909100008", name="Beta User", org_id="beta")
        assert body_a["user_id"] != body_b["user_id"]

        # Convert acme user under acme org — succeeds
        resp_a = _convert(client, body_a["user_id"], org_id="acme")
        assert resp_a.status_code == 201

        # Convert acme user under beta org — 404 (wrong org boundary)
        resp_b = _convert(client, body_a["user_id"], org_id="beta")
        assert resp_b.status_code == 404


# ---------------------------------------------------------------------------
# TestRevenueOrgId
# ---------------------------------------------------------------------------

class TestRevenueOrgId:
    def _seed(
        self,
        client: TestClient,
        zalo: str,
        org_id: str,
        monthly_vnd: int = 199000,
    ) -> str:
        body = _signup(client, zalo, org_id=org_id)
        uid = body["user_id"]
        r = _convert(client, uid, monthly_vnd=monthly_vnd, org_id=org_id)
        assert r.status_code == 201
        return uid

    def test_revenue_includes_org_id_field(self, client: TestClient) -> None:
        """Revenue response always includes org_id field."""
        resp = client.get("/v1/pilot/revenue")
        assert resp.status_code == 200
        assert "org_id" in resp.json()
        assert resp.json()["org_id"] == "default"

    def test_revenue_scoped_to_org(self, client: TestClient) -> None:
        """Revenue for acme only counts acme conversions."""
        self._seed(client, "+84909200001", org_id="acme", monthly_vnd=199000)
        self._seed(client, "+84909200002", org_id="beta", monthly_vnd=299000)

        r_acme = client.get("/v1/pilot/revenue?org_id=acme")
        assert r_acme.status_code == 200
        body_acme = r_acme.json()
        assert body_acme["mrr_vnd"] == 199000
        assert body_acme["conversions"] == 1
        assert body_acme["org_id"] == "acme"

        r_beta = client.get("/v1/pilot/revenue?org_id=beta")
        assert r_beta.json()["mrr_vnd"] == 299000
        assert r_beta.json()["org_id"] == "beta"

    def test_revenue_no_cross_tenant_leak(self, client: TestClient) -> None:
        """Querying beta revenue returns 0 even when acme has conversions."""
        self._seed(client, "+84909200003", org_id="acme", monthly_vnd=499000)

        r = client.get("/v1/pilot/revenue?org_id=beta")
        assert r.status_code == 200
        assert r.json()["mrr_vnd"] == 0
        assert r.json()["conversions"] == 0

    def test_revenue_default_without_param(self, client: TestClient) -> None:
        """Revenue without ?org_id only counts default org."""
        self._seed(client, "+84909200004", org_id="default")
        self._seed(client, "+84909200005", org_id="acme")

        r = client.get("/v1/pilot/revenue")  # no param
        assert r.status_code == 200
        body = r.json()
        assert body["mrr_vnd"] == 199000  # acme NOT included
        assert body["org_id"] == "default"

    def test_revenue_legacy_conversions_in_default(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Legacy conversion records (no org_id) appear under 'default' org."""
        legacy_conv = {
            "user_id": "opc_001_legacy",
            "tier": "starter",
            "monthly_vnd": 199000,
            "started_at": "2026-01-01",
            "recorded_at": "2026-01-01T00:00:00+00:00",
            # No org_id field
        }
        (tmp_path / "conversions.jsonl").write_text(
            json.dumps(legacy_conv) + "\n", encoding="utf-8"
        )

        r = client.get("/v1/pilot/revenue?org_id=default")
        assert r.status_code == 200
        assert r.json()["mrr_vnd"] == 199000


# ---------------------------------------------------------------------------
# TestExportMisaOrgId
# ---------------------------------------------------------------------------

class TestExportMisaOrgId:
    def _seed_and_convert(
        self,
        client: TestClient,
        zalo: str,
        org_id: str,
        monthly_vnd: int = 199000,
    ) -> None:
        body = _signup(client, zalo, org_id=org_id)
        uid = body["user_id"]
        r = _convert(client, uid, monthly_vnd=monthly_vnd, org_id=org_id)
        assert r.status_code == 201

    def test_export_filename_includes_org_id(
        self, client: TestClient
    ) -> None:
        """Export filename contains org_id: misa-pilots-{org}-{from}-{to}.csv"""
        self._seed_and_convert(client, "+84909300001", org_id="acme")
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12&org_id=acme",
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 200
        disposition = resp.headers["content-disposition"]
        assert "misa-pilots-acme-2026-01-2026-12.csv" in disposition

    def test_export_filters_by_org(self, client: TestClient) -> None:
        """Export?org_id=acme CSV contains only acme rows, not beta."""
        self._seed_and_convert(client, "+84909300002", org_id="acme")
        self._seed_and_convert(client, "+84909300003", org_id="beta")

        resp = client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12&org_id=acme",
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 200
        content = resp.content.decode("utf-8-sig")  # strip BOM
        rows = list(filter(None, content.strip().split("\n")))
        # header + 1 data row for acme only (not 2)
        assert len(rows) == 2

    def test_export_default_org_without_param(
        self, client: TestClient
    ) -> None:
        """Export without org_id defaults to 'default' org only."""
        self._seed_and_convert(client, "+84909300004", org_id="default")
        self._seed_and_convert(client, "+84909300005", org_id="acme")

        resp = client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12",
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 200
        content = resp.content.decode("utf-8-sig")
        rows = list(filter(None, content.strip().split("\n")))
        # header + 1 data row (default org only)
        assert len(rows) == 2
        assert "misa-pilots-default-2026-01-2026-12.csv" in resp.headers["content-disposition"]

    def test_export_jwt_wrong_org_403(self, client: TestClient) -> None:
        """Founder JWT scoped to acme cannot export beta org data."""
        token = _make_jwt(scopes=["founder"], allowed_orgs=["acme"])
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12&org_id=beta",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
