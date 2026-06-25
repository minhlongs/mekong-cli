"""Phase 8 P04 — Audit log persistence tests.

Tests for src/services/audit_logger.py and its integration with
vn_pilot_auth._require_scope / _audit_log.

PII policy: verify no raw token, no 'name', no 'zalo' field in any audit line.
Isolation: all tests redirect audit file to tmp_path via MEKONG_CONFIG_DIR env var.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import time
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.vn_pilot_routes as vpr
import src.services.audit_logger as audit_logger

# ---------- Constants ----------

JWT_SECRET = "test-jwt-secret-32-bytes-padding!!"
LEGACY_TOKEN = "legacy-admin-token-p04-test"

VALID_SIGNUP = {
    "name": "Nguyễn Thị B",
    "zalo": "+84909111222",
    "business_type": "cafe_fnb",
    "city": "HCM",
    "industry": "ăn uống",
    "source": "fb",
}


def _make_jwt(
    scopes: list[str] | None = None,
    allowed_orgs: list[str] | None = None,
    sub: str = "founder@cashclaw.cc",
    exp_offset: int = 3600,
) -> str:
    if scopes is None:
        scopes = ["founder"]
    if allowed_orgs is None:
        allowed_orgs = ["*"]
    now = int(time.time())
    return jwt.encode(
        {"sub": sub, "scopes": scopes, "allowed_orgs": allowed_orgs, "iat": now, "exp": now + exp_offset},
        JWT_SECRET,
        algorithm="HS256",
    )


# ---------- Fixtures ----------


@pytest.fixture(autouse=True)
def redirect_audit_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect audit log to tmp_path via MEKONG_CONFIG_DIR for isolation."""
    monkeypatch.setenv("MEKONG_CONFIG_DIR", str(tmp_path))


@pytest.fixture
def audit_path(tmp_path: Path) -> Path:
    return tmp_path / "admin-audit.jsonl"


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", LEGACY_TOKEN)
    monkeypatch.setenv("MEKONG_JWT_SECRET", JWT_SECRET)
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app, raise_server_exceptions=True)


# ---------- Helper ----------


def _read_audit(tmp_path: Path) -> list[dict]:
    path = tmp_path / "admin-audit.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


# ---------- Test 1: File auto-created on first write ----------


class TestFileAutoCreated:
    def test_file_created_on_first_write(self, tmp_path: Path) -> None:
        """Audit file is created automatically on first call."""
        audit_path = tmp_path / "admin-audit.jsonl"
        assert not audit_path.exists()
        audit_logger.audit_admin_action(
            scope="founder", org="acme", sub="test@example.com", endpoint="/v1/pilot/convert"
        )
        assert audit_path.exists()
        records = _read_audit(tmp_path)
        assert len(records) == 1
        assert records[0]["event"] == "admin_auth"


# ---------- Test 2: Legacy token → audit line with scope=legacy ----------


class TestLegacyTokenAudit:
    def test_legacy_auth_writes_scope_legacy(self, client: TestClient, tmp_path: Path) -> None:
        """Legacy MEKONG_ADMIN_TOKEN success writes scope='legacy' audit line."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )

        records = _read_audit(tmp_path)
        assert records, "Expected audit record"
        r = records[-1]
        assert r["scope"] == "legacy"
        assert r["sub"] == "legacy"
        assert r["event"] == "admin_auth"
        assert "endpoint" in r


# ---------- Test 3: JWT founder → audit line with scope=founder, org=acme ----------


class TestJWTFounderAudit:
    def test_jwt_founder_writes_correct_fields(self, client: TestClient, tmp_path: Path) -> None:
        """JWT founder auth writes scope=founder, org, sub, endpoint to audit log."""
        resp = client.post("/v1/pilot/signup", json={**VALID_SIGNUP, "org_id": "acme"})
        uid = resp.json()["user_id"]

        token = _make_jwt(scopes=["founder"], allowed_orgs=["acme"], sub="founder@cashclaw.cc")
        client.post(
            "/v1/pilot/convert?org_id=acme",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )

        records = _read_audit(tmp_path)
        assert records
        r = records[-1]
        assert r["scope"] == "founder"
        assert r["org"] == "acme"
        assert r["sub"] == "founder@cashclaw.cc"
        assert r["endpoint"] == "/v1/pilot/convert"
        assert r["event"] == "admin_auth"
        assert r["timestamp_iso"].endswith("Z")


# ---------- Test 4: JWT readonly → blocked, no audit line ----------


class TestReadonlyBlockedNoAudit:
    def test_readonly_blocked_writes_no_audit(self, client: TestClient, tmp_path: Path) -> None:
        """readonly scope blocked from convert — no audit line written (only successes audited)."""
        token = _make_jwt(scopes=["readonly"])
        client.post(
            "/v1/pilot/convert",
            json={"user_id": "opc_999_zzzzzz", "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )
        records = _read_audit(tmp_path)
        # No audit line since auth failed (scope check rejected before audit call)
        assert len(records) == 0


# ---------- Test 5: File permissions 0600 on creation ----------


class TestFilePermissions:
    def test_audit_file_mode_0600(self, tmp_path: Path) -> None:
        """Audit file is created with mode 0600 (founder-readable only)."""
        audit_logger.audit_admin_action(
            scope="cs", org="default", sub="cs@example.com", endpoint="/v1/pilot/convert"
        )
        audit_path = tmp_path / "admin-audit.jsonl"
        assert audit_path.exists()
        mode = audit_path.stat().st_mode & 0o777
        assert mode == 0o600, f"Expected 0600 got {oct(mode)}"


# ---------- Test 6: read_audit_lines returns correct records ----------


class TestReadAuditLines:
    def test_read_audit_lines_returns_last_n(self, tmp_path: Path) -> None:
        """read_audit_lines(limit) returns at most limit entries in file order."""
        for i in range(15):
            audit_logger.audit_admin_action(
                scope="founder", org=f"org{i}", sub=f"u{i}@x.com", endpoint="/v1/test"
            )
        lines = audit_logger.read_audit_lines(limit=10)
        assert len(lines) == 10
        # Last 10 records — orgs 5-14
        assert lines[0]["org"] == "org5"
        assert lines[-1]["org"] == "org14"

    def test_read_audit_lines_no_file_returns_empty(self, tmp_path: Path) -> None:
        """read_audit_lines returns [] when file does not exist."""
        result = audit_logger.read_audit_lines()
        assert result == []


# ---------- Test 7: Best-effort write on read-only filesystem ----------


class TestBestEffortWrite:
    def test_read_only_dir_does_not_raise(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """audit_admin_action swallows IOError — never raises even on unwritable path."""
        ro_dir = tmp_path / "readonly"
        ro_dir.mkdir()
        ro_dir.chmod(0o555)  # read + execute, no write
        monkeypatch.setenv("MEKONG_CONFIG_DIR", str(ro_dir))

        # Must NOT raise
        try:
            audit_logger.audit_admin_action(
                scope="founder", org="default", sub="founder@x.com", endpoint="/v1/test"
            )
        finally:
            ro_dir.chmod(0o755)  # restore for cleanup


# ---------- Test 8: flock-safe concurrent appends ----------


def _append_worker(config_dir: str, idx: int) -> None:
    """Worker process: write one audit record into the shared file."""
    os.environ["MEKONG_CONFIG_DIR"] = config_dir
    # Re-import in subprocess context
    from src.services.audit_logger import audit_admin_action  # noqa: PLC0415
    audit_admin_action(scope="founder", org="acme", sub=f"w{idx}@x.com", endpoint="/v1/test")


class TestFlockSafeConcurrentAppends:
    def test_concurrent_appends_no_torn_lines(self, tmp_path: Path) -> None:
        """Multiple concurrent processes writing to same audit file produce valid JSONL."""
        n_workers = 10
        with multiprocessing.Pool(n_workers) as pool:
            pool.starmap(_append_worker, [(str(tmp_path), i) for i in range(n_workers)])

        audit_path = tmp_path / "admin-audit.jsonl"
        assert audit_path.exists()
        lines = audit_path.read_text().splitlines()
        assert len(lines) == n_workers, f"Expected {n_workers} lines, got {len(lines)}"
        # Every line must be valid JSON
        subs = set()
        for line in lines:
            rec = json.loads(line)  # raises if torn/invalid
            subs.add(rec["sub"])
        # All 10 unique workers wrote exactly one record each
        assert len(subs) == n_workers


# ---------- Test 9: PII redaction — no raw token / name / zalo in audit ----------


class TestPIIRedaction:
    def test_no_pii_in_audit_lines(self, client: TestClient, tmp_path: Path) -> None:
        """Audit log must never contain raw token, PII name, or zalo phone number."""
        resp = client.post("/v1/pilot/signup", json=VALID_SIGNUP)
        uid = resp.json()["user_id"]

        # Legacy auth (uses LEGACY_TOKEN)
        client.post(
            "/v1/pilot/convert",
            json={"user_id": uid, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {LEGACY_TOKEN}"},
        )

        # JWT auth
        token = _make_jwt(scopes=["founder"], sub="founder@cashclaw.cc")
        resp = client.post("/v1/pilot/signup", json={**VALID_SIGNUP, "zalo": "+84909333444"})
        uid2 = resp.json()["user_id"]
        client.post(
            "/v1/pilot/convert",
            json={"user_id": uid2, "tier": "starter", "monthly_vnd": 199000},
            headers={"Authorization": f"Bearer {token}"},
        )

        audit_text = (tmp_path / "admin-audit.jsonl").read_text()

        # Raw bearer token strings must not appear
        assert LEGACY_TOKEN not in audit_text
        assert JWT_SECRET not in audit_text
        # PII name/phone fields must not appear
        assert VALID_SIGNUP["name"] not in audit_text
        assert "+84909111222" not in audit_text
        assert "+84909333444" not in audit_text
        # No 'name' or 'zalo' field keys
        for line in audit_text.splitlines():
            rec = json.loads(line)
            assert "name" not in rec
            assert "zalo" not in rec

    def test_endpoint_no_query_string_pii(self, tmp_path: Path) -> None:
        """Endpoint logged as path-only (no query string that might contain PII)."""
        audit_logger.audit_admin_action(
            scope="founder", org="default", sub="f@x.com",
            endpoint="/v1/pilot/convert",
        )
        records = _read_audit(tmp_path)
        assert records[0]["endpoint"] == "/v1/pilot/convert"
        # Verify no '?' in endpoint (caller responsibility — tested here as smoke)
        assert "?" not in records[0]["endpoint"]


# ---------- Test 10: Schema completeness ----------


class TestAuditRecordSchema:
    def test_all_required_fields_present(self, tmp_path: Path) -> None:
        """Every audit record contains all 6 required fields."""
        audit_logger.audit_admin_action(
            scope="cs", org="acme", sub="cs@cashclaw.cc", endpoint="/v1/pilot/convert"
        )
        records = _read_audit(tmp_path)
        assert records
        r = records[0]
        required = {"event", "timestamp_iso", "scope", "org", "sub", "endpoint"}
        assert required <= r.keys(), f"Missing fields: {required - r.keys()}"
        assert r["event"] == "admin_auth"
        # timestamp ends with Z (UTC)
        assert r["timestamp_iso"].endswith("Z")
        # Only allowed fields — no extras beyond the 6 (keeps log lean)
        extra = r.keys() - required
        assert not extra, f"Unexpected extra fields: {extra}"
