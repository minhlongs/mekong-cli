"""
Tests cho src/api/vn_pilot_routes.py — signup + poll response endpoints.

Isolates ~/.mekong/ to tmp_path qua MEKONG_PILOT_DIR env + monkeypatching the
module-level CONFIG_DIR (FastAPI route handlers capture the var at call time).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import vn_pilot_routes as vpr


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """FastAPI app + TestClient with isolated CONFIG_DIR."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


VALID_SIGNUP = {
    "name": "Nguyễn Văn A",
    "zalo": "+84909123456",
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "thời trang",
    "source": "fb",
}


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/v1/pilot/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok", "service": "vn-pilot"}


class TestSignup:
    def test_happy_path_creates_pilot(self, client: TestClient, tmp_path: Path) -> None:
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_new"] is True
        assert body["user_id"].startswith("opc_001_")
        assert body["credits"] == 50
        # Persisted to disk
        assert (tmp_path / "pilots.jsonl").exists()
        assert (tmp_path / "pilot_credits.json").exists()
        balances = json.loads((tmp_path / "pilot_credits.json").read_text())
        assert balances[body["user_id"]] == 50

    def test_idempotent_same_zalo_returns_existing(self, client: TestClient) -> None:
        first = client.post("/v1/pilot/signup", json=VALID_SIGNUP).json()
        second = client.post("/v1/pilot/signup", json=VALID_SIGNUP).json()
        assert first["user_id"] == second["user_id"]
        assert second["is_new"] is False
        # Credits NOT re-granted
        assert second["credits"] == 50

    def test_sequential_user_ids(self, client: TestClient) -> None:
        for i in range(3):
            payload = {**VALID_SIGNUP, "zalo": f"+8490912345{i}", "name": f"User {i}"}
            r = client.post("/v1/pilot/signup", json=payload).json()
            assert r["user_id"].startswith(f"opc_{i+1:03d}_")

    def test_cap_at_10_pilots(self, client: TestClient) -> None:
        for i in range(10):
            payload = {**VALID_SIGNUP, "zalo": f"+849091234{i:02d}", "name": f"U{i}"}
            assert client.post("/v1/pilot/signup", json=payload).status_code == 201
        overflow = {**VALID_SIGNUP, "zalo": "+84909999999", "name": "Overflow"}
        resp = client.post("/v1/pilot/signup", json=overflow)
        assert resp.status_code == 409
        assert "10 user" in resp.json()["detail"]
        assert "waitlist" in resp.json()["detail"]

    @pytest.mark.parametrize("zalo", ["invalid", "+1234", "abc", "84909123456", "0aaaaa"])
    def test_invalid_zalo_rejected(self, client: TestClient, zalo: str) -> None:
        payload = {**VALID_SIGNUP, "zalo": zalo}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 422

    @pytest.mark.parametrize("valid_zalo", ["+84909123456", "0909123456", "+84 909 123 456", "+849091234567"])
    def test_valid_zalo_formats_accepted(self, client: TestClient, valid_zalo: str) -> None:
        payload = {**VALID_SIGNUP, "zalo": valid_zalo, "name": f"U {valid_zalo}"}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 201, f"failed for {valid_zalo}: {resp.json()}"

    def test_invalid_business_type_rejected(self, client: TestClient) -> None:
        payload = {**VALID_SIGNUP, "business_type": "spaceship_pilot"}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 422

    def test_short_name_rejected(self, client: TestClient) -> None:
        payload = {**VALID_SIGNUP, "name": "A"}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 422

    def test_missing_required_field(self, client: TestClient) -> None:
        payload = {k: v for k, v in VALID_SIGNUP.items() if k != "name"}
        resp = client.post("/v1/pilot/signup", json=payload)
        assert resp.status_code == 422


class TestPollResponse:
    def _onboard(self, client: TestClient) -> str:
        return client.post("/v1/pilot/signup", json=VALID_SIGNUP).json()["user_id"]

    def test_happy_path(self, client: TestClient, tmp_path: Path) -> None:
        uid = self._onboard(client)
        resp = client.post("/v1/pilot/response", json={
            "user_id": uid, "score": 5, "comment": "Tuyệt vời",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["recorded"] is True
        assert body["low_nps_alert"] is False
        # Persisted
        line = (tmp_path / "poll_responses.jsonl").read_text().strip()
        rec = json.loads(line)
        assert rec["user_id"] == uid
        assert rec["score"] == 5
        assert rec["comment"] == "Tuyệt vời"
        assert rec["iso_week"].startswith("2026-W")

    def test_low_score_flags_alert(self, client: TestClient) -> None:
        uid = self._onboard(client)
        resp = client.post("/v1/pilot/response", json={"user_id": uid, "score": 2})
        assert resp.status_code == 201
        assert resp.json()["low_nps_alert"] is True

    def test_score_4_not_flagged(self, client: TestClient) -> None:
        """4 = passive (NPS standard). Boundary: alert chỉ ở 1-3 detractor."""
        uid = self._onboard(client)
        resp = client.post("/v1/pilot/response", json={"user_id": uid, "score": 4})
        assert resp.json()["low_nps_alert"] is False

    @pytest.mark.parametrize("score", [0, 6, -1, 10, 99])
    def test_score_out_of_range_rejected(self, client: TestClient, score: int) -> None:
        uid = self._onboard(client)
        resp = client.post("/v1/pilot/response", json={"user_id": uid, "score": score})
        assert resp.status_code == 422

    def test_unknown_user_rejected(self, client: TestClient) -> None:
        resp = client.post("/v1/pilot/response", json={
            "user_id": "opc_999_deadbe", "score": 3,
        })
        assert resp.status_code == 404
        assert "Unknown" in resp.json()["detail"]

    def test_invalid_user_id_format_rejected(self, client: TestClient) -> None:
        resp = client.post("/v1/pilot/response", json={
            "user_id": "random_user_123", "score": 3,
        })
        assert resp.status_code == 422

    def test_iso_week_override_persisted(self, client: TestClient, tmp_path: Path) -> None:
        uid = self._onboard(client)
        resp = client.post("/v1/pilot/response", json={
            "user_id": uid, "score": 4, "iso_week": "2026-W21",
        })
        assert resp.json()["iso_week"] == "2026-W21"
        rec = json.loads((tmp_path / "poll_responses.jsonl").read_text().strip())
        assert rec["iso_week"] == "2026-W21"


class TestStats:
    def test_empty_state(self, client: TestClient) -> None:
        body = client.get("/v1/pilot/stats").json()
        assert body == {
            "total_pilots": 0,
            "active_pilots": 0,
            "capacity_remaining": 10,
            "by_type": {},
            "by_source": {},
        }

    def test_aggregates_by_type_and_source(self, client: TestClient) -> None:
        for i, (btype, src) in enumerate([
            ("shop_online", "fb"),
            ("shop_online", "fb"),
            ("freelancer", "linkedin"),
            ("cafe_fnb", "zalo_group"),
        ]):
            client.post("/v1/pilot/signup", json={
                **VALID_SIGNUP, "zalo": f"+849091234{i:02d}", "name": f"U{i}",
                "business_type": btype, "source": src,
            })
        stats = client.get("/v1/pilot/stats").json()
        assert stats["total_pilots"] == 4
        assert stats["active_pilots"] == 4
        assert stats["capacity_remaining"] == 6
        assert stats["by_type"] == {"shop_online": 2, "freelancer": 1, "cafe_fnb": 1}
        assert stats["by_source"] == {"fb": 2, "linkedin": 1, "zalo_group": 1}



class TestRecent:
    def test_recent_empty(self, client: TestClient) -> None:
        resp = client.get("/v1/pilot/recent")
        assert resp.status_code == 200
        assert resp.json() == {"signups": [], "nps_responses": []}

    def test_recent_signups_all_returned(self, client: TestClient) -> None:
        for i in range(3):
            client.post("/v1/pilot/signup", json={
                **VALID_SIGNUP, "zalo": f"+849091234{i:02d}", "name": f"User{i}",
                "business_type": "shop_online" if i == 0 else "freelancer",
            })
        body = client.get("/v1/pilot/recent").json()
        # onboarded_at uses seconds resolution → ties expected within fast tests.
        # Assert membership + count, not strict positional order.
        types = [s["business_type"] for s in body["signups"]]
        assert len(types) == 3
        assert types.count("freelancer") == 2
        assert types.count("shop_online") == 1

    def test_recent_excludes_pii(self, client: TestClient) -> None:
        client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        signup_record = client.get("/v1/pilot/recent").json()["signups"][0]
        assert "name" not in signup_record
        assert "zalo" not in signup_record
        assert "industry" not in signup_record
        assert "user_id" not in signup_record
        # Allowed fields only
        assert set(signup_record.keys()) == {"business_type", "city", "source", "onboarded_at"}

    def test_recent_nps_with_comment_truncation(self, client: TestClient) -> None:
        # Onboard then submit poll response with long comment
        signup = client.post("/v1/pilot/signup", json=VALID_SIGNUP).json()
        long_comment = "A" * 200
        post_resp = client.post("/v1/pilot/response", json={
            "user_id": signup["user_id"],
            "score": 5,  # PollResponseRequest score range = 1-5
            "comment": long_comment,
        })
        assert post_resp.status_code == 201, post_resp.text
        body = client.get("/v1/pilot/recent").json()
        assert len(body["nps_responses"]) == 1
        nps = body["nps_responses"][0]
        assert nps["score"] == 5
        assert nps["comment_preview"] == "A" * 80  # truncated to 80
        assert "user_id" not in nps  # PII boundary

    def test_recent_limit_validation(self, client: TestClient) -> None:
        # ge=1 le=100 enforced by FastAPI Query
        assert client.get("/v1/pilot/recent?limit=0").status_code == 422
        assert client.get("/v1/pilot/recent?limit=101").status_code == 422
        assert client.get("/v1/pilot/recent?limit=1").status_code == 200
        assert client.get("/v1/pilot/recent?limit=100").status_code == 200

    def test_recent_respects_limit(self, client: TestClient) -> None:
        for i in range(5):
            client.post("/v1/pilot/signup", json={
                **VALID_SIGNUP, "zalo": f"+849091234{i:02d}", "name": f"U{i}",
            })
        body = client.get("/v1/pilot/recent?limit=2").json()
        assert len(body["signups"]) == 2


class TestConvert:
    @pytest.fixture(autouse=True)
    def _bypass_admin_auth(self, client: TestClient) -> None:
        """Skip token check in conversion-logic tests (see TestConvertAuth for auth)."""
        client.app.dependency_overrides[vpr._require_admin_token] = lambda: None
        yield
        client.app.dependency_overrides.clear()

    def _signup(self, client: TestClient, suffix: int = 0, name: str = "U") -> str:
        body = client.post("/v1/pilot/signup", json={
            **VALID_SIGNUP, "zalo": f"+849091234{suffix:02d}", "name": f"{name}{suffix}",
        }).json()
        return body["user_id"]

    def test_convert_unknown_user(self, client: TestClient) -> None:
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "opc_999_zzzzzz",
            "tier": "starter_vnd",
            "monthly_vnd": 199_000,
        })
        assert resp.status_code == 404

    def test_convert_creates_record(self, client: TestClient) -> None:
        user_id = self._signup(client)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": user_id,
            "tier": "starter_vnd",
            "monthly_vnd": 199_000,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_new"] is True
        assert body["user_id"] == user_id
        assert body["monthly_vnd"] == 199_000
        assert body["tier"] == "starter_vnd"
        assert body["started_at"]  # auto-filled with today

    def test_convert_idempotent(self, client: TestClient) -> None:
        user_id = self._signup(client)
        payload = {
            "user_id": user_id,
            "tier": "growth_vnd",
            "monthly_vnd": 499_000,
            "started_at": "2026-05-17",
        }
        first = client.post("/v1/pilot/convert", json=payload).json()
        second = client.post("/v1/pilot/convert", json=payload).json()
        assert first["is_new"] is True
        assert second["is_new"] is False
        assert first["recorded_at"] == second["recorded_at"]

    def test_convert_invalid_user_id_format(self, client: TestClient) -> None:
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "not_a_pilot_id",
            "tier": "starter_vnd",
            "monthly_vnd": 199_000,
        })
        assert resp.status_code == 422

    def test_convert_rejects_negative_amount(self, client: TestClient) -> None:
        user_id = self._signup(client)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": user_id,
            "tier": "starter_vnd",
            "monthly_vnd": -1,
        })
        assert resp.status_code == 422


class TestRevenue:
    @pytest.fixture(autouse=True)
    def _bypass_admin_auth(self, client: TestClient) -> None:
        client.app.dependency_overrides[vpr._require_admin_token] = lambda: None
        yield
        client.app.dependency_overrides.clear()

    def _signup(self, client: TestClient, suffix: int = 0) -> str:
        body = client.post("/v1/pilot/signup", json={
            **VALID_SIGNUP, "zalo": f"+849091234{suffix:02d}", "name": f"U{suffix}",
        }).json()
        return body["user_id"]

    def test_revenue_empty(self, client: TestClient) -> None:
        body = client.get("/v1/pilot/revenue").json()
        assert body["conversions"] == 0
        assert body["unique_converted_users"] == 0
        assert body["mrr_vnd"] == 0
        assert body["conversion_rate"] == 0.0
        assert body["by_tier"] == {}
        assert body["target_mrr_vnd"] == 1_000_000
        assert body["target_conversions"] == 5

    def test_revenue_aggregates_mrr(self, client: TestClient) -> None:
        # 2 signups, 1 conversion
        user_a = self._signup(client, suffix=0)
        self._signup(client, suffix=1)
        client.post("/v1/pilot/convert", json={
            "user_id": user_a,
            "tier": "starter_vnd",
            "monthly_vnd": 199_000,
            "started_at": "2026-05-17",
        })
        body = client.get("/v1/pilot/revenue").json()
        assert body["conversions"] == 1
        assert body["unique_converted_users"] == 1
        assert body["mrr_vnd"] == 199_000
        assert body["conversion_rate"] == 0.5  # 1 / 2
        assert body["by_tier"] == {"starter_vnd": 1}

    def test_revenue_multiple_tiers(self, client: TestClient) -> None:
        for i in range(3):
            uid = self._signup(client, suffix=i)
            tier = ["starter_vnd", "growth_vnd", "pro_vnd"][i]
            amount = [199_000, 499_000, 999_000][i]
            client.post("/v1/pilot/convert", json={
                "user_id": uid, "tier": tier, "monthly_vnd": amount,
                "started_at": f"2026-05-{17 + i:02d}",
            })
        body = client.get("/v1/pilot/revenue").json()
        assert body["mrr_vnd"] == 199_000 + 499_000 + 999_000
        assert body["unique_converted_users"] == 3
        assert body["by_tier"] == {"starter_vnd": 1, "growth_vnd": 1, "pro_vnd": 1}


class TestConvertAuth:
    """Auth gate on POST /v1/pilot/convert. Real auth path, no dep-override."""

    ADMIN_TOKEN = "test_admin_token_xyz123"

    def _signup(self, client: TestClient) -> str:
        return client.post("/v1/pilot/signup", json=VALID_SIGNUP).json()["user_id"]

    def test_503_when_env_not_configured(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("MEKONG_ADMIN_TOKEN", raising=False)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "opc_001_aaaaaa", "tier": "starter_vnd", "monthly_vnd": 199_000,
        }, headers={"Authorization": f"Bearer {self.ADMIN_TOKEN}"})
        assert resp.status_code == 503
        assert "MEKONG_ADMIN_TOKEN not set" in resp.json()["detail"]

    def test_401_when_no_authorization_header(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEKONG_ADMIN_TOKEN", self.ADMIN_TOKEN)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "opc_001_aaaaaa", "tier": "starter_vnd", "monthly_vnd": 199_000,
        })
        assert resp.status_code == 401
        assert "Bearer" in resp.json()["detail"]

    def test_401_when_authorization_malformed(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEKONG_ADMIN_TOKEN", self.ADMIN_TOKEN)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "opc_001_aaaaaa", "tier": "starter_vnd", "monthly_vnd": 199_000,
        }, headers={"Authorization": "NotBearer foo"})
        assert resp.status_code == 401

    def test_403_when_token_mismatch(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEKONG_ADMIN_TOKEN", self.ADMIN_TOKEN)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": "opc_001_aaaaaa", "tier": "starter_vnd", "monthly_vnd": 199_000,
        }, headers={"Authorization": "Bearer wrong_token"})
        assert resp.status_code == 403
        assert "Invalid" in resp.json()["detail"]

    def test_201_with_valid_bearer(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MEKONG_ADMIN_TOKEN", self.ADMIN_TOKEN)
        uid = self._signup(client)
        resp = client.post("/v1/pilot/convert", json={
            "user_id": uid, "tier": "starter_vnd", "monthly_vnd": 199_000,
        }, headers={"Authorization": f"Bearer {self.ADMIN_TOKEN}"})
        assert resp.status_code == 201
        assert resp.json()["is_new"] is True

    def test_revenue_endpoint_remains_public(self, client: TestClient) -> None:
        """GET /revenue is dashboard-read aggregate — no auth required."""
        resp = client.get("/v1/pilot/revenue")
        assert resp.status_code == 200
