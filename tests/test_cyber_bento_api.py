#!/usr/bin/env python3
"""
tests/test_cyber_bento_api.py — Unit and integration tests for Cyber-Bento API Server.
"""

import pytest
from fastapi.testclient import TestClient
from scripts.cyber_bento_api_server import app

client = TestClient(app)

def test_api_status():
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["active_screens"] == 21
    assert data["daemons"]["gateway"] == "ONLINE"
    assert data["daemons"]["c_suite_swarm"] == "ONLINE"

def test_api_screens():
    resp = client.get("/api/v1/screens")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 21
    assert len(data["screens"]) == 21
    # Check c-suite-boardroom is present
    boardroom = next((s for s in data["screens"] if s["href"] == "c-suite-boardroom.html"), None)
    assert boardroom is not None
    assert boardroom["stitch_id"] == "7a7122ec87844012b62aa1f95ebd7916"
    assert boardroom["group"] == "Executive"
    # Check fintech-treasury is present
    treasury = next((s for s in data["screens"] if s["href"] == "fintech-treasury.html"), None)
    assert treasury is not None
    assert treasury["stitch_id"] == "5bbdb79f45fd4d78bfa0eae01a768486"
    assert treasury["group"] == "Fintech"
    # Check zero-to-ipo-launchpad is present
    launchpad = next((s for s in data["screens"] if s["href"] == "zero-to-ipo-launchpad.html"), None)
    assert launchpad is not None
    assert launchpad["stitch_id"] == "e856db6b532e4facbd997edb6bada3c9"
    assert launchpad["group"] == "Executive"

def test_api_vietqr_simulate():
    payload = {"amount": 500000, "bank_code": "MB"}
    resp = client.post("/api/v1/vietqr/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["mcu_credited"] == 500
    assert data["new_balance"] == 9420 + 500
    assert len(data["hmac_sha256"]) == 64
    assert data["status"] == "SETTLED"

def test_api_tt78_verify():
    payload = {
        "invoice_id": "INV-2026-9999",
        "seller_tax_id": "0312345678",
        "amount_vnd": 20000000,
        "vat_rate": 10
    }
    resp = client.post("/api/v1/tt78/verify", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert "TT78" in data["compliance_standard"]
    assert len(data["canonical_sha256"]) == 64

def test_api_c_suite_quorum():
    resp = client.get("/api/v1/c-suite/quorum")
    assert resp.status_code == 200
    data = resp.json()
    assert data["quorum_aligned"] is True
    assert data["consensus_score"] == "5/5"
    assert len(data["agents"]) == 5
    roles = [a["role"] for a in data["agents"]]
    assert "CEO Solo" in roles
    assert "Sun Tzu" in roles

def test_api_merkle_audit():
    records = ["event_1", "event_2", "event_3", "event_4"]
    resp = client.post("/api/v1/audit/merkle", json={"records": records})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["merkle_root"]) == 64
    assert data["leaf_count"] == 4
    assert len(data["leaves"]) == 4
