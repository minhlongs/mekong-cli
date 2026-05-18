"""Phase 8 P05 — Storage backend parity tests (parametrized over jsonl + sqlite).

Asserts that the full signup→convert→revenue→poll→export flow produces
identical observable HTTP responses + persisted shapes under both backends.

Isolation: each test gets a fresh tmp_path, fresh DB (sqlite) / fresh JSONL dir.
Backend cache is reset between parametrize runs via _reset_backend_cache().
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_routes as vpr
import src.api.vn_pilot_state as _state
from src.services.sqlite_migrations import ensure_schema
from src.services.storage_backend import _reset_backend_cache

# ---------- Constants ----------

VALID_SIGNUP = {
    "name": "Nguyễn Văn Parity",
    "zalo": "+84909888777",
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "thời trang",
    "source": "fb",
}

JWT_SECRET=REDACTED = "test-parity-secret-32bytes-padding"

# ---------- Fixtures ----------


def _make_jwt(
    scopes: list[str] | None = None,
    allowed_orgs: list[str] | None = None,
    sub: str = "founder@test.cc",
) -> str:
    import time
    import jwt  # type: ignore[import]

    if scopes is None:
        scopes = ["founder"]
    if allowed_orgs is None:
        allowed_orgs = ["*"]
    payload = {
        "sub": sub,
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, JWT_SECRET=REDACTED, algorithm="HS256")


@pytest.fixture(params=["jsonl", "sqlite"])
def client_backend(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[tuple[TestClient, str], None, None]:
    """Return (TestClient, backend_name) for both backends."""
    backend_name: str = request.param

    monkeypatch.setattr(_state, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_PILOT_DIR", str(tmp_path))
    monkeypatch.setenv("MEKONG_PILOT_STORAGE", backend_name)
    monkeypatch.setenv("MEKONG_JWT_SECRET=REDACTED", JWT_SECRET=REDACTED)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", "legacy-admin-token")
    monkeypatch.setenv("MEKONG_SIGNUP_WEBHOOK_URL", "")  # disable webhook

    if backend_name == "sqlite":
        import sqlite3
        db = tmp_path / "pilot.db"
        conn = sqlite3.connect(str(db))
        ensure_schema(conn)
        conn.close()

    _reset_backend_cache()

    app = FastAPI()
    app.include_router(vpr.router)
    client = TestClient(app)
    yield client, backend_name


# ---------- Helper ----------

def _auth_header(scopes: list[str] | None = None) -> dict[str, str]:
    token = _make_jwt(scopes or ["founder"])
    return {"Authorization": f"Bearer {token}"}


# ---------- Parity Tests ----------

class TestSignupParity:
    def test_signup_returns_201_is_new(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        assert resp.status_code == 201, f"[{backend}] {resp.text}"
        body = resp.json()
        assert body["is_new"] is True
        assert body["credits"] == 50
        assert body["user_id"].startswith("opc_")

    def test_signup_idempotent_returns_is_new_false(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        r1 = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        r2 = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r2.json()["is_new"] is False
        assert r1.json()["user_id"] == r2.json()["user_id"]


class TestConvertRevenueParity:
    def test_revenue_increments_mrr(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        # First signup
        signup_resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        user_id = signup_resp.json()["user_id"]

        # Convert
        headers = _auth_header(["founder"])
        conv_resp = client.post(
            "/v1/pilot/convert",
            json={
                "user_id": user_id,
                "tier": "starter",
                "monthly_vnd": 199000,
                "started_at": "2026-05-17",
            },
            headers=headers,
        )
        assert conv_resp.status_code == 201, f"[{backend}] {conv_resp.text}"
        assert conv_resp.json()["is_new"] is True

        # Revenue
        rev_resp = client.get("/v1/pilot/revenue")
        assert rev_resp.status_code == 200
        body = rev_resp.json()
        assert body["mrr_vnd"] == 199000
        assert body["conversions"] == 1

    def test_convert_idempotent(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        signup_resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        user_id = signup_resp.json()["user_id"]

        headers = _auth_header(["founder"])
        payload = {
            "user_id": user_id,
            "tier": "starter",
            "monthly_vnd": 199000,
            "started_at": "2026-05-17",
        }
        r1 = client.post("/v1/pilot/convert", json=payload, headers=headers)
        r2 = client.post("/v1/pilot/convert", json=payload, headers=headers)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r2.json()["is_new"] is False

        # Revenue should still be 199000, not doubled
        rev_body = client.get("/v1/pilot/revenue").json()
        assert rev_body["mrr_vnd"] == 199000


class TestPollParity:
    def test_poll_response_recorded(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        signup_resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        user_id = signup_resp.json()["user_id"]

        poll_resp = client.post(
            "/v1/pilot/response",
            json={"user_id": user_id, "score": 4, "comment": "good", "iso_week": "2026-W20"},
        )
        assert poll_resp.status_code == 201, f"[{backend}] {poll_resp.text}"
        body = poll_resp.json()
        assert body["recorded"] is True
        assert body["score"] == 4
        assert body["iso_week"] == "2026-W20"


class TestOrgIsolationParity:
    def test_cross_tenant_isolation(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        """Pilots in org-a must not appear in org-b revenue."""
        client, backend = client_backend

        signup_a = dict(VALID_SIGNUP, org_id="org-a")
        signup_b = dict(VALID_SIGNUP, zalo="+84909111000", org_id="org-b")
        ra = client.post("/v1/pilot/signup", json=signup_a)
        client.post("/v1/pilot/signup", json=signup_b)
        user_a = ra.json()["user_id"]

        # Use JWT with wildcard orgs so the /convert org check passes
        import time, jwt as _jwt
        token = _jwt.encode(
            {
                "sub": "founder@test.cc",
                "scopes": ["founder"],
                "allowed_orgs": ["*"],
                "exp": int(time.time()) + 3600,
            },
            JWT_SECRET=REDACTED,
            algorithm="HS256",
        )
        headers = {"Authorization": f"Bearer {token}"}
        conv = client.post(
            "/v1/pilot/convert",
            json={"user_id": user_a, "tier": "starter", "monthly_vnd": 199000, "started_at": "2026-05-17"},
            params={"org_id": "org-a"},
            headers=headers,
        )
        assert conv.status_code == 201, f"[{backend}] convert failed: {conv.text}"

        rev_a = client.get("/v1/pilot/revenue", params={"org_id": "org-a"}).json()
        rev_b = client.get("/v1/pilot/revenue", params={"org_id": "org-b"}).json()

        assert rev_a["mrr_vnd"] == 199000
        assert rev_b["mrr_vnd"] == 0


class TestHealthStatsParity:
    def test_health_ok(self, client_backend: tuple[TestClient, str]) -> None:
        client, backend = client_backend
        resp = client.get("/v1/pilot/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_stats_counts_after_signup(
        self, client_backend: tuple[TestClient, str]
    ) -> None:
        client, backend = client_backend
        client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        stats = client.get("/v1/pilot/stats").json()
        assert stats["total_pilots"] == 1
        assert stats["active_pilots"] == 1
        assert stats["converted_pilots"] == 0
