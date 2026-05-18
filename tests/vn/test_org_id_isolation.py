"""
Tests for Phase 7 P04 multi-tenant org_id isolation.

Covers signup scoping, per-org cap, stats/recent filtering, and health breakdown.
All tests use isolated tmp_path via MEKONG_PILOT_DIR monkeypatching.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import vn_pilot_routes as vpr


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


TEMPLATE = {
    "name": "Org Test User",
    "zalo": "+84909000000",  # overridden per-call
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "test",
    "source": "smoke_test",
}


def _signup(client: TestClient, zalo: str, name: str = "User",
            org_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {**TEMPLATE, "zalo": zalo, "name": name}
    if org_id is not None:
        payload["org_id"] = org_id
    r = client.post("/v1/pilot/signup", json=payload)
    assert r.status_code == 201, f"signup failed: {r.status_code} {r.text[:200]}"
    return r.json()


# ---------------------------------------------------------------------------
# TestOrgSignup
# ---------------------------------------------------------------------------

class TestOrgSignup:
    def test_default_org_user_id_format(self, client: TestClient) -> None:
        """Default org signup produces opc_NNN_xxxxxx format (backward-compat)."""
        body = _signup(client, "+84909000001")
        assert body["user_id"].startswith("opc_001_")
        # No org slug in user_id for default org
        parts = body["user_id"].split("_")
        assert len(parts) == 3, f"Expected 3 segments, got: {body['user_id']!r}"

    def test_custom_org_user_id_format(self, client: TestClient) -> None:
        """Custom org signup produces opc_<orgslug>_NNN_xxxxxx format."""
        body = _signup(client, "+84909000002", name="Acme User", org_id="acme")
        assert body["user_id"].startswith("opc_acme_001_")
        parts = body["user_id"].split("_")
        assert len(parts) == 4, f"Expected 4 segments, got: {body['user_id']!r}"
        assert parts[1] == "acme"

    @pytest.mark.parametrize("bad_org", [
        "UPPERCASE",          # uppercase not allowed
        "has space",          # space not allowed
        "has!special",        # special char
        "a" * 33,             # too long (>32 chars total)
        "-leading-dash",      # must start with alnum
    ])
    def test_invalid_org_id_rejected(self, client: TestClient, bad_org: str) -> None:
        payload = {**TEMPLATE, "zalo": "+84909000003", "org_id": bad_org}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 422, f"Expected 422 for org_id={bad_org!r}, got {resp.status_code}"

    def test_same_zalo_in_two_orgs_creates_two_pilots(self, client: TestClient) -> None:
        """Same Zalo in different orgs → different user_ids (isolation contract)."""
        body_a = _signup(client, "+84909111111", name="User Org A", org_id="orga")
        body_b = _signup(client, "+84909111111", name="User Org B", org_id="orgb")
        assert body_a["user_id"] != body_b["user_id"]
        assert body_a["is_new"] is True
        assert body_b["is_new"] is True

    def test_same_zalo_same_org_is_idempotent(self, client: TestClient) -> None:
        """Same Zalo in same org → idempotent, returns existing record."""
        body1 = _signup(client, "+84909222222", org_id="myorg")
        # Re-submit same Zalo + same org
        resp = client.post("/v1/pilot/signup", json={
            **TEMPLATE, "zalo": "+84909222222", "name": "Same User", "org_id": "myorg",
        })
        assert resp.status_code == 201
        body2 = resp.json()
        assert body2["is_new"] is False
        assert body2["user_id"] == body1["user_id"]

    def test_valid_org_id_formats_accepted(self, client: TestClient) -> None:
        """Single char, alphanumeric with dashes, 32 chars total — all valid."""
        valid_orgs = ["a", "org1", "my-org", "a" * 32]
        for i, org in enumerate(valid_orgs):
            payload = {**TEMPLATE, "zalo": f"+8490900{i:04d}", "org_id": org}
            resp = client.post("/v1/pilot/signup", json=payload)
            assert resp.status_code == 201, f"Expected 201 for org_id={org!r}: {resp.text[:200]}"


# ---------------------------------------------------------------------------
# TestOrgCap
# ---------------------------------------------------------------------------

class TestOrgCap:
    def test_two_orgs_can_each_fill_to_cap(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """50 to org_a + 50 to org_b both succeed (cap is per-org, not global)."""
        monkeypatch.setattr(vpr, "MAX_PILOTS", 3)  # small cap for speed
        for i in range(3):
            _signup(client, f"+8490910{i:04d}", name=f"A{i}", org_id="orga")
            _signup(client, f"+8490920{i:04d}", name=f"B{i}", org_id="orgb")
        # Both orgs at cap — verify counts
        stats_a = client.get("/v1/pilot/stats?org_id=orga").json()
        stats_b = client.get("/v1/pilot/stats?org_id=orgb").json()
        assert stats_a["total_pilots"] == 3
        assert stats_b["total_pilots"] == 3

    def test_overflow_in_one_org_rejected(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """51st signup to org_a → 409 after cap=3 reached."""
        monkeypatch.setattr(vpr, "MAX_PILOTS", 3)
        for i in range(3):
            _signup(client, f"+8490930{i:04d}", name=f"U{i}", org_id="orga")
        overflow = {**TEMPLATE, "zalo": "+84909999991", "name": "Over", "org_id": "orga"}
        resp = client.post("/v1/pilot/signup", json=overflow)
        assert resp.status_code == 409
        assert "waitlist" in resp.json()["detail"]

    def test_full_org_a_does_not_block_org_b(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Org A at cap → org B signups still succeed."""
        monkeypatch.setattr(vpr, "MAX_PILOTS", 2)
        for i in range(2):
            _signup(client, f"+8490940{i:04d}", name=f"A{i}", org_id="orga")
        # org_a at cap
        overflow_a = {**TEMPLATE, "zalo": "+84909999992", "name": "Over", "org_id": "orga"}
        assert client.post("/v1/pilot/signup", json=overflow_a).status_code == 409
        # org_b still accepts
        body = _signup(client, "+84909888801", name="B1", org_id="orgb")
        assert body["is_new"] is True


# ---------------------------------------------------------------------------
# TestOrgStats
# ---------------------------------------------------------------------------

class TestOrgStats:
    def test_stats_scoped_to_org(self, client: TestClient) -> None:
        """Stats for org_a only shows org_a counts."""
        _signup(client, "+84909100001", name="A1", org_id="orga")
        _signup(client, "+84909100002", name="A2", org_id="orga")
        _signup(client, "+84909100003", name="B1", org_id="orgb")

        stats_a = client.get("/v1/pilot/stats?org_id=orga").json()
        assert stats_a["total_pilots"] == 2

        stats_b = client.get("/v1/pilot/stats?org_id=orgb").json()
        assert stats_b["total_pilots"] == 1

    def test_stats_default_without_param(self, client: TestClient) -> None:
        """Query without ?org_id returns default-namespace counts."""
        # Signup in default org (no org_id field → treated as default)
        payload = {**TEMPLATE, "zalo": "+84909200001", "name": "Def1"}
        r = client.post("/v1/pilot/signup", json=payload)
        assert r.status_code == 201

        stats = client.get("/v1/pilot/stats").json()
        assert stats["total_pilots"] == 1

    def test_legacy_records_without_org_id_counted_as_default(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Records in pilots.jsonl with NO org_id field → treated as 'default'."""
        import json
        # Inject a legacy record (no org_id field)
        legacy = {
            "user_id": "opc_001_legacy",
            "name": "Legacy User",
            "zalo": "+84909300001",
            "business_type": "shop_online",
            "city": "HN",
            "industry": None,
            "source": "direct",
            "onboarded_at": "2026-01-01T00:00:00+00:00",
            "pilot_end_at": "2026-03-01T00:00:00+00:00",
            "status": "active",
            # NO org_id field — legacy record
        }
        (tmp_path / "pilots.jsonl").write_text(json.dumps(legacy) + "\n", encoding="utf-8")

        stats = client.get("/v1/pilot/stats?org_id=default").json()
        assert stats["total_pilots"] == 1

        # Must NOT appear under a different org
        stats_other = client.get("/v1/pilot/stats?org_id=other").json()
        assert stats_other["total_pilots"] == 0

    def test_stats_capacity_remaining_is_per_org(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """capacity_remaining reflects per-org count, not global total."""
        monkeypatch.setattr(vpr, "MAX_PILOTS", 10)
        _signup(client, "+84909400001", org_id="orga")
        _signup(client, "+84909400002", org_id="orga")
        _signup(client, "+84909400003", org_id="orgb")

        stats_a = client.get("/v1/pilot/stats?org_id=orga").json()
        assert stats_a["capacity_remaining"] == 8  # 10 - 2

        stats_b = client.get("/v1/pilot/stats?org_id=orgb").json()
        assert stats_b["capacity_remaining"] == 9  # 10 - 1


# ---------------------------------------------------------------------------
# TestOrgRecent
# ---------------------------------------------------------------------------

class TestOrgRecent:
    def test_recent_filtered_per_org(self, client: TestClient) -> None:
        """recent?org_id=orga returns only orga signups."""
        _signup(client, "+84909500001", name="A1", org_id="orga")
        _signup(client, "+84909500002", name="A2", org_id="orga")
        _signup(client, "+84909500003", name="B1", org_id="orgb")

        r = client.get("/v1/pilot/recent?org_id=orga")
        assert r.status_code == 200
        signups = r.json()["signups"]
        assert len(signups) == 2

    def test_no_cross_org_leakage(self, client: TestClient) -> None:
        """org_a signups must not appear in org_b query response."""
        _signup(client, "+84909600001", name="A1", org_id="orga")
        _signup(client, "+84909600002", name="A2", org_id="orga")

        r = client.get("/v1/pilot/recent?org_id=orgb")
        assert r.status_code == 200
        assert r.json()["signups"] == []

    def test_recent_default_org_without_param(self, client: TestClient) -> None:
        """recent without ?org_id returns default org signups."""
        payload = {**TEMPLATE, "zalo": "+84909700001", "name": "Def1"}
        client.post("/v1/pilot/signup", json=payload)

        r = client.get("/v1/pilot/recent")
        assert r.status_code == 200
        signups = r.json()["signups"]
        assert len(signups) == 1

    def test_recent_legacy_records_in_default(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        """Legacy records (no org_id) appear in default org recent query."""
        import json
        legacy = {
            "user_id": "opc_001_legacy",
            "name": "Legacy",
            "zalo": "+84909800001",
            "business_type": "freelancer",
            "city": "HCM",
            "industry": None,
            "source": "direct",
            "onboarded_at": "2026-01-01T00:00:00+00:00",
            "pilot_end_at": "2026-03-01T00:00:00+00:00",
            "status": "active",
        }
        (tmp_path / "pilots.jsonl").write_text(json.dumps(legacy) + "\n", encoding="utf-8")

        r = client.get("/v1/pilot/recent?org_id=default")
        assert r.status_code == 200
        signups = r.json()["signups"]
        assert len(signups) == 1
        assert signups[0]["business_type"] == "freelancer"


# ---------------------------------------------------------------------------
# TestOrgHealth
# ---------------------------------------------------------------------------

class TestOrgHealth:
    def test_health_returns_per_org_breakdown(self, client: TestClient) -> None:
        """Health endpoint includes per_org dict with pilot counts."""
        _signup(client, "+84909010001", org_id="orga")
        _signup(client, "+84909010002", org_id="orga")
        _signup(client, "+84909010003", org_id="orgb")

        r = client.get("/v1/pilot/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert "per_org" in body
        assert body["per_org"]["orga"] == 2
        assert body["per_org"]["orgb"] == 1

    def test_health_empty_orgs_not_in_breakdown(self, client: TestClient) -> None:
        """Empty state: per_org is empty dict (no orgs with 0 pilots listed)."""
        r = client.get("/v1/pilot/health")
        body = r.json()
        assert body["per_org"] == {}

    def test_health_default_org_in_breakdown(self, client: TestClient) -> None:
        """Default org signups appear under 'default' key in per_org."""
        payload = {**TEMPLATE, "zalo": "+84909020001", "name": "DefUser"}
        client.post("/v1/pilot/signup", json=payload)

        r = client.get("/v1/pilot/health")
        body = r.json()
        assert "default" in body["per_org"]
        assert body["per_org"]["default"] == 1
