"""
Production capacity test — exercise the real MAX_PILOTS value end-to-end.

Phase 7 stage 1 cap = 50 (founder override). This test ensures the cap
mechanism scales correctly at production size, not just the parametric
unit test in test_vn_pilot_routes.py::test_cap_uses_max_pilots_constant.

Loops 50 signups + 1 overflow attempt. Runtime <300ms.
"""
from __future__ import annotations

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


VALID_TEMPLATE = {
    "name": "Capacity Test User",
    "zalo": "+84909000000",  # overridden per-iteration
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "test",
    "source": "smoke_test",
}


class TestProductionCapacity:
    """End-to-end test that the production cap (MAX_PILOTS=50) holds.

    Distinct from the unit test which uses monkeypatched cap=3 for speed —
    that validates the conditional logic. This one validates the actual
    integer constant the gateway runs with.
    """

    def test_full_capacity_then_overflow(self, client: TestClient) -> None:
        """Loop MAX_PILOTS signups, all 201. Then #MAX+1 → 409.

        Uses unique Zalo per iteration to avoid the idempotency short-circuit
        (same Zalo → returns existing record without consuming a slot).
        """
        cap = vpr.MAX_PILOTS
        assert cap >= 50, (
            f"Phase 7 expects MAX_PILOTS >= 50, got {cap}. "
            "If this fires the founder override may have been reverted."
        )

        # Fill to cap. Use a Zalo format that scales: +849090NNNNN
        for i in range(cap):
            payload = {
                **VALID_TEMPLATE,
                "zalo": f"+8490900{i:05d}",
                "name": f"PilotUser{i:03d}",
            }
            r = client.post("/v1/pilot/signup", json=payload)
            assert r.status_code == 201, (
                f"Signup {i+1}/{cap} failed: {r.status_code} {r.text[:200]}"
            )
            assert r.json()["is_new"] is True

        # Stats reflect full capacity
        stats = client.get("/v1/pilot/stats").json()
        assert stats["total_pilots"] == cap
        assert stats["capacity_remaining"] == 0

        # Overflow attempt — must reject with 409 and Vietnamese-language hint
        overflow = {**VALID_TEMPLATE, "zalo": "+84909999999", "name": "Overflow"}
        resp = client.post("/v1/pilot/signup", json=overflow)
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert f"{cap} user" in detail, f"Detail should mention cap={cap}: {detail!r}"
        assert "waitlist" in detail

    def test_capacity_remaining_decrements(self, client: TestClient) -> None:
        """capacity_remaining must drop by exactly 1 per new signup."""
        cap = vpr.MAX_PILOTS
        for i in range(5):
            client.post("/v1/pilot/signup", json={
                **VALID_TEMPLATE,
                "zalo": f"+8490900{i:05d}",
                "name": f"U{i}",
            })
        stats = client.get("/v1/pilot/stats").json()
        assert stats["capacity_remaining"] == cap - 5

    def test_idempotent_resubmit_does_not_consume_slot(
        self, client: TestClient
    ) -> None:
        """Same Zalo posted twice → 2nd call returns is_new=False, slot count unchanged."""
        payload = {**VALID_TEMPLATE, "zalo": "+84909000001", "name": "Stable"}
        r1 = client.post("/v1/pilot/signup", json=payload)
        r2 = client.post("/v1/pilot/signup", json=payload)
        assert r1.json()["is_new"] is True
        assert r2.json()["is_new"] is False
        assert client.get("/v1/pilot/stats").json()["total_pilots"] == 1
