"""Tests for JWT scope-based admin auth — Phase 8 P01.

Covers:
- Legacy MEKONG_ADMIN_TOKEN back-compat (exact match)
- JWT with founder scope → convert (201) + export allowed
- JWT with cs scope → convert (201), export blocked (403)
- JWT with readonly scope → convert (403)
- Expired JWT → 401 "Token expired"
- Invalid signature → 401 "Invalid token"
- algorithm=none → 401 (algorithm pinning)
- Wrong org → 403 "Wrong org"
- allowed_orgs=["*"] → wildcard matches any org
- MEKONG_JWT_SECRET=REDACTED not set, legacy not set → 503
- Audit log emission on success
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_routes as vpr

# ---------------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------------

LEGACY_TOKEN = "legacy-admin-token-xyz"
JWT_SECRET=REDACTED = "test-jwt-secret-32-bytes-padding!!"  # >= 32 chars


def _make_jwt(
    *,
    secret: str = JWT_SECRET=REDACTED,
    scopes: list[str] | None = None,
    allowed_orgs: list[str] | None = None,
    exp_offset: int = 3600,
    algorithm: str = "HS256",
    sub: str = "tester",
) -> str:
    """Issue a test JWT with configurable claims."""
    if scopes is None:
        scopes = ["founder"]
    if allowed_orgs is None:
        allowed_orgs = ["default"]
    now = int(time.time())
    payload = {
        "sub": sub,
        "scopes": scopes,
        "allowed_orgs": allowed_orgs,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


VALID_SIGNUP = {
    "name": "Nguyễn Văn A",
    "zalo": "+84909123456",
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "thời trang",
    "source": "fb",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with isolated CONFIG_DIR, legacy token + JWT secret set."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", LEGACY_TOKEN)
    monkeypatch.setenv("MEKONG_JWT_SECRET=REDACTED", JWT_SECRET=REDACTED)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def seeded_client(client: TestClient) -> TestClient:
    """TestClient with one pilot user already signed up + converted."""
    # Signup first
    resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
    assert resp.status_code in (200, 201)
    user_id = resp.json()["user_id"]

    # Convert using legacy token so we have data for export
    resp = client.post(
        "/v1/pilot/convert",
        json={"user_id": user_id, "tier": "starter", "monthly_vnd": 199000},
        headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
    )
    assert resp.status_code in (200, 201)

    return client


# ---------------------------------------------------------------------------
# 1. Legacy MEKONG_ADMIN_TOKEN exact match → allowed
# ---------------------------------------------------------------------------


class TestLegacyBackdoor:
    def test_legacy_token_convert_succeeds(
        self, client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Legacy token should still grant convert access (back-compat)."""
        # Create a pilot user first
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        assert resp.status_code in (200, 201)
        uid = resp.json()["user_id"]

        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 201

    def test_legacy_token_export_succeeds(self, seeded_client: TestClient) -> None:
        """Legacy token should still grant export access (back-compat)."""
        resp = seeded_client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12",
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )
        assert resp.status_code == 200

    def test_wrong_legacy_token_falls_through_to_jwt(self, client: TestClient) -> None:
        """Wrong legacy token with valid JWT → should succeed via JWT path."""
        token = _make_jwt(scopes=["founder"])
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_missing", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        # JWT valid but user missing → 404 (not 401/403)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 2. JWT with founder scope → convert + export allowed
# ---------------------------------------------------------------------------


class TestJWTFounderScope:
    def test_founder_scope_convert(
        self, client: TestClient
    ) -> None:
        """JWT with founder scope grants convert access."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        token = _make_jwt(scopes=["founder"])
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    def test_founder_scope_export(self, seeded_client: TestClient) -> None:
        """JWT with founder scope grants export access."""
        token = _make_jwt(scopes=["founder"])
        resp = seeded_client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. JWT with cs scope → convert allowed, export blocked
# ---------------------------------------------------------------------------


class TestJWTCSScope:
    def test_cs_scope_convert_allowed(self, client: TestClient) -> None:
        """cs scope grants convert access (founder | cs required)."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        token = _make_jwt(scopes=["cs"])
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    def test_cs_scope_export_blocked(self, seeded_client: TestClient) -> None:
        """cs scope cannot access export (founder-only)."""
        token = _make_jwt(scopes=["cs"])
        resp = seeded_client.get(
            "/v1/pilot/export/misa?from=2026-01&to=2026-12",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert "scope" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. JWT with readonly scope → convert blocked
# ---------------------------------------------------------------------------


class TestJWTReadonlyScope:
    def test_readonly_scope_convert_blocked(self, client: TestClient) -> None:
        """readonly scope cannot convert (requires founder or cs)."""
        token = _make_jwt(scopes=["readonly"])
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert "scope" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. Expired JWT → 401 "Token expired"
# ---------------------------------------------------------------------------


class TestExpiredJWT:
    def test_expired_token_rejected(self, client: TestClient) -> None:
        """Expired JWT must return 401 with 'Token expired' detail."""
        token = _make_jwt(exp_offset=-120)  # expired 2 minutes ago (beyond 30s leeway)
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Token expired"


# ---------------------------------------------------------------------------
# 6. Invalid signature → 401
# ---------------------------------------------------------------------------


class TestInvalidSignature:
    def test_wrong_secret_rejected(self, client: TestClient) -> None:
        """JWT signed with wrong secret must return 401."""
        token = _make_jwt(secret="completely-wrong-secret-!!!!!!!!!!!!!!!")
        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid token"


# ---------------------------------------------------------------------------
# 7. algorithm=none → 401 (algorithm pinning)
# ---------------------------------------------------------------------------


class TestAlgorithmNoneRejected:
    def test_alg_none_rejected(self, client: TestClient) -> None:
        """JWT with alg=none must be rejected (algorithm pinning)."""
        # Craft a none-alg token manually (PyJWT won't normally issue these)
        import base64

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).rstrip(b"=").decode()
        payload_data = {
            "sub": "attacker",
            "scopes": ["founder"],
            "allowed_orgs": ["*"],
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
        }
        payload = base64.urlsafe_b64encode(
            json.dumps(payload_data).encode()
        ).rstrip(b"=").decode()
        # none-alg has empty signature
        token = f"{header}.{payload}."

        resp = client.post(
            "/v1/pilot/convert",
            json={"user_id": "x", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 8. Wrong org → 403
# ---------------------------------------------------------------------------


class TestWrongOrg:
    def test_org_mismatch_blocked(self, client: TestClient) -> None:
        """JWT scoped to org 'acme' cannot act on org 'default'."""
        token = _make_jwt(scopes=["founder"], allowed_orgs=["acme"])
        resp = client.post(
            "/v1/pilot/convert?org_id=default",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Wrong org"


# ---------------------------------------------------------------------------
# 9. allowed_orgs=["*"] → wildcard matches any request org
# ---------------------------------------------------------------------------


class TestWildcardOrg:
    def test_wildcard_org_matches_any(self, client: TestClient) -> None:
        """JWT with allowed_orgs=["*"] should pass org check for any org."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        token = _make_jwt(scopes=["founder"], allowed_orgs=["*"])
        # Request with a non-default org_id
        resp = client.post(
            "/v1/pilot/convert?org_id=some_other_org",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        # User exists → 201 (org check passed)
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# 10. No MEKONG_JWT_SECRET=REDACTED (and no MEKONG_ADMIN_TOKEN) → 503
# ---------------------------------------------------------------------------


class TestBothSecretsAbsent:
    def test_503_when_both_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If neither MEKONG_ADMIN_TOKEN nor MEKONG_JWT_SECRET=REDACTED is set → 503."""
        monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
        monkeypatch.delenv("MEKONG_ADMIN_TOKEN", raising=False)
        monkeypatch.delenv("MEKONG_JWT_SECRET=REDACTED", raising=False)

        app = FastAPI()
        app.include_router(vpr.router)
        c = TestClient(app, raise_server_exceptions=True)

        token = _make_jwt()
        resp = c.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# 11. Audit log emission on success
# ---------------------------------------------------------------------------


class TestAuditLog:
    def test_audit_log_emitted_on_jwt_success(
        self, client: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured JSON audit line emitted for successful JWT auth."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        token = _make_jwt(scopes=["founder"], sub="audit-tester")

        with caplog.at_level(logging.INFO, logger="src.api.vn_pilot_auth"):
            client.post(
                "/v1/pilot/convert",
                json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
                headers={"Authorization": f"Bearer {token}"},
            )

        audit_lines = [
            r.message for r in caplog.records
            if '"event": "admin_auth"' in r.message
        ]
        assert audit_lines, "Expected audit log line not emitted"
        audit = json.loads(audit_lines[0])
        assert audit["event"] == "admin_auth"
        assert audit["sub"] == "audit-tester"
        assert "founder" in audit["scope"]

    def test_audit_log_emitted_on_legacy_success(
        self, client: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Structured JSON audit line emitted for legacy token auth too."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        with caplog.at_level(logging.INFO, logger="src.api.vn_pilot_auth"):
            client.post(
                "/v1/pilot/convert",
                json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
                headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
            )

        audit_lines = [
            r.message for r in caplog.records
            if '"event": "admin_auth"' in r.message
        ]
        assert audit_lines
        audit = json.loads(audit_lines[0])
        assert audit["sub"] == "legacy"
        assert audit["scope"] == "legacy"
