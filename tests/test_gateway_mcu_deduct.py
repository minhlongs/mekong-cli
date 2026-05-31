"""Tests for POST /v1/mcu/deduct gateway endpoint."""

from __future__ import annotations

import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.gateway import app
from src.raas.credits import CreditStore


# Use the session-isolated DB path patched by conftest._isolate_billing_db
def _get_isolated_db_path():
    """Get the temp DB path patched by conftest."""
    import src.raas.credits as credits_mod
    return credits_mod.DB_PATH


def _wipe_tenant(tenant_id: str) -> None:
    """Remove a specific tenant from the isolated DB to ensure clean state."""
    db_path = _get_isolated_db_path()
    try:
        conn = sqlite3.connect(str(db_path), timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("DELETE FROM credit_accounts WHERE tenant_id = ?", (tenant_id,))
        conn.execute("DELETE FROM credit_transactions WHERE tenant_id = ?", (tenant_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass


@pytest.fixture
def credit_store():
    """Provide a fresh CreditStore instance using the session-isolated DB."""
    return CreditStore()


@pytest.fixture(autouse=True)
def _clean_mcu_deduct_tenants():
    """Ensure test tenants start with zero balance before each MCU deduct test."""
    # Wipe all tenant IDs used in this test file
    for tid in ["t1", "new_tenant"]:
        _wipe_tenant(tid)
    yield
    # Cleanup after test too
    for tid in ["t1", "new_tenant"]:
        _wipe_tenant(tid)


client = TestClient(app)  # type: ignore[call-arg]


class TestMCUDeductEndpoint:
    """Test POST /v1/mcu/deduct."""

    def test_deduct_simple_success(self, credit_store):
        credit_store.add_credits("t1", 100, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "simple",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["amount_deducted"] == 1
        assert data["balance_after"] == 99

    def test_deduct_standard_success(self, credit_store):
        credit_store.add_credits("t1", 100, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "standard",
        })
        assert resp.status_code == 200
        assert resp.json()["amount_deducted"] == 3

    def test_deduct_complex_success(self, credit_store):
        credit_store.add_credits("t1", 100, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "complex",
        })
        assert resp.status_code == 200
        assert resp.json()["amount_deducted"] == 5

    def test_deduct_insufficient_balance_402(self, credit_store):
        credit_store.add_credits("t1", 2, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "complex",
        })
        assert resp.status_code == 402
        data = resp.json()
        # Check for structured error response
        assert "INSUFFICIENT_CREDITS" in str(data) or "Insufficient" in str(data)

    def test_deduct_invalid_complexity_400(self, credit_store):
        credit_store.add_credits("t1", 100, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "mega",
        })
        assert resp.status_code == 400
        data = resp.json()
        # Check for structured error response with INVALID_INPUT or Invalid complexity
        assert "INVALID_INPUT" in str(data) or "Invalid complexity" in str(data)

    def test_deduct_with_mission_id(self, credit_store):
        credit_store.add_credits("t1", 50, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "standard",
            "mission_id": "m-456",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_deduct_low_balance_flag(self, credit_store):
        credit_store.add_credits("t1", 12, "test_credit")
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1",
            "complexity": "standard",
        })
        data = resp.json()
        assert data["success"] is True
        assert data["low_balance"] is True  # 12-3=9 < 10

    def test_deduct_missing_tenant_id_422(self):
        resp = client.post("/v1/mcu/deduct", json={
            "complexity": "simple",
        })
        assert resp.status_code == 422

    def test_sequential_deductions(self, credit_store):
        credit_store.add_credits("t1", 20, "test_credit")
        client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1", "complexity": "simple",
        })
        client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1", "complexity": "standard",
        })
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "t1", "complexity": "complex",
        })
        data = resp.json()
        assert data["balance_after"] == 11  # 20-1-3-5

    def test_deduct_zero_balance_tenant(self):
        resp = client.post("/v1/mcu/deduct", json={
            "tenant_id": "new_tenant",
            "complexity": "simple",
        })
        assert resp.status_code == 402
