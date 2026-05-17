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
