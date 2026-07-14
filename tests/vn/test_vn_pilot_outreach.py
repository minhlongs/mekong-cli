"""Tests for src/api/vn_pilot_outreach.py — outreach log + history endpoints."""
from __future__ import annotations

import json
from pathlib import Path

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


@pytest.fixture
def pilot_id(client: TestClient, tmp_path: Path) -> str:
    resp = client.post(
        "/v1/pilot/signup",
        json={
            "name": "Outreach Test",
            "zalo": "+84909000909",
            "business_type": "shop_online",
            "city": "HCM",
        },
    )
    assert resp.status_code == 201
    return resp.json()["user_id"]


class TestOutreachLog:
    def test_happy_path_returns_201(self, client: TestClient, pilot_id: str) -> None:
        resp = client.post(
            "/v1/pilot/outreach/log",
            json={"user_id": pilot_id, "channel": "zalo", "day_offset": 7, "outcome": "sent"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == pilot_id
        assert body["channel"] == "zalo"
        assert body["day_offset"] == 7
        assert body["outcome"] == "sent"
        assert "ts" in body

    def test_defaults_channel_and_outcome(self, client: TestClient, pilot_id: str) -> None:
        resp = client.post("/v1/pilot/outreach/log", json={"user_id": pilot_id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["channel"] == "zalo"
        assert body["outcome"] == "sent"

    def test_all_channels_accepted(self, client: TestClient, pilot_id: str) -> None:
        for ch in ("zalo", "phone", "email", "other"):
            resp = client.post(
                "/v1/pilot/outreach/log",
                json={"user_id": pilot_id, "channel": ch, "day_offset": 3},
            )
            assert resp.status_code == 200

    def test_404_for_unknown_user(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/pilot/outreach/log",
            json={"user_id": "opc_ZZZ_nonexistent", "channel": "zalo", "day_offset": 3},
        )
        assert resp.status_code == 404

    def test_400_bad_user_id_prefix(self, client: TestClient) -> None:
        resp = client.post(
            "/v1/pilot/outreach/log",
            json={"user_id": "bad-id", "channel": "zalo", "day_offset": 3},
        )
        assert resp.status_code == 400


class TestOutreachHistory:
    def test_empty_history_when_no_contacts(self, client: TestClient, pilot_id: str) -> None:
        resp = client.get(f"/v1/pilot/outreach/{pilot_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == pilot_id
        assert body["total_contacts"] == 0
        assert body["history"] == []

    def test_multiple_contacts_sorted_latest_first(
        self, client: TestClient, pilot_id: str
    ) -> None:
        import time
        for outcome in ("sent", "no_reply", "interested"):
            client.post(
                "/v1/pilot/outreach/log",
                json={"user_id": pilot_id, "channel": "zalo", "day_offset": 3, "outcome": outcome},
            )
            time.sleep(0.01)  # ensure distinct timestamps
        resp = client.get(f"/v1/pilot/outreach/{pilot_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_contacts"] == 3
        assert body["history"][0]["outcome"] == "interested"  # latest first

    def test_404_for_unknown_user(self, client: TestClient) -> None:
        resp = client.get(f"/v1/pilot/outreach/opc_ZZZ_nonexistent")
        assert resp.status_code == 404  # user not in pilots.jsonl

    def test_400_bad_prefix(self, client: TestClient) -> None:
        resp = client.get("/v1/pilot/outreach/bad-id")
        assert resp.status_code == 400
