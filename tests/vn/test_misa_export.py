"""
Tests for MISA AMIS CSV export — Phase 7 P03.

Covers the exporter service (in-process) + the HTTP route (TestClient).
DRAFT account codes documented in source comments; env override behavior
tested explicitly so founder can swap codes after accountant review
without touching code.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import vn_pilot_routes as vpr
from src.services.misa_exporter import (
    MISA_HEADERS,
    UTF8_BOM,
    build_misa_rows,
    to_csv_bytes,
    write_csv,
)


VALID_SIGNUP = {
    "name": "Nguyễn Văn A",
    "zalo": "+84909123456",
    "business_type": "shop_online",
    "city": "HCM",
    "industry": "thời trang",
    "source": "fb",
}


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """TestClient with isolated CONFIG_DIR + admin token set."""
    monkeypatch.setattr(vpr, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MEKONG_ADMIN_TOKEN", "test_admin_xyz")
    app = FastAPI()
    app.include_router(vpr.router)
    return TestClient(app)


def _seed_conversion(
    user_id: str,
    tier: str,
    amount: int,
    started_at: str,
) -> dict:
    """Build a conversion dict (caller appends to conversions.jsonl)."""
    return {
        "user_id": user_id,
        "tier": tier,
        "monthly_vnd": amount,
        "started_at": started_at,
        "recorded_at": f"{started_at}T00:00:00+00:00",
    }


def _write_conversions(tmp_path: Path, conversions: list[dict]) -> None:
    """Persist conversions to tmp_path/conversions.jsonl."""
    p = tmp_path / "conversions.jsonl"
    p.write_text("\n".join(json.dumps(c) for c in conversions) + "\n", encoding="utf-8")


# ---------- Exporter service tests (no HTTP) ----------

class TestMISAExporter:

    def test_header_row_exact(self) -> None:
        """8 columns in exact order."""
        buf = io.StringIO()
        write_csv([], buf)
        # BOM + header row + trailing newline
        content = buf.getvalue()
        assert content.startswith(UTF8_BOM)
        lines = content.strip().splitlines()
        assert lines[0].lstrip(UTF8_BOM) == ",".join(MISA_HEADERS)
        assert MISA_HEADERS == [
            "voucher_date", "voucher_no", "debit_account",
            "credit_account", "amount_vnd", "description",
            "partner_id", "tax_code",
        ]

    def test_empty_range_returns_header_only(self) -> None:
        rows = build_misa_rows([], "2026-05", "2026-05")
        assert rows == []
        buf = io.StringIO()
        write_csv(rows, buf)
        content = buf.getvalue()
        lines = content.strip().splitlines()
        assert len(lines) == 1  # header only

    def test_voucher_numbering_monotonic_per_month(self) -> None:
        """3 conversions in same month → PIL-202605-001/002/003."""
        conversions = [
            _seed_conversion("opc_001_a", "starter", 199_000, "2026-05-01"),
            _seed_conversion("opc_002_b", "starter", 199_000, "2026-05-15"),
            _seed_conversion("opc_003_c", "growth", 299_000, "2026-05-20"),
        ]
        rows = build_misa_rows(conversions, "2026-05", "2026-05")
        assert [r.voucher_no for r in rows] == [
            "PIL-202605-001", "PIL-202605-002", "PIL-202605-003",
        ]

    def test_voucher_numbering_restarts_per_month(self) -> None:
        """Cross-month range → counter restarts at 001 each month."""
        conversions = [
            _seed_conversion("opc_001_a", "starter", 199_000, "2026-04-15"),
            _seed_conversion("opc_002_b", "starter", 199_000, "2026-05-01"),
            _seed_conversion("opc_003_c", "starter", 199_000, "2026-05-02"),
            _seed_conversion("opc_004_d", "starter", 199_000, "2026-06-10"),
        ]
        rows = build_misa_rows(conversions, "2026-04", "2026-06")
        nos = [r.voucher_no for r in rows]
        assert "PIL-202604-001" in nos
        assert "PIL-202605-001" in nos
        assert "PIL-202605-002" in nos
        assert "PIL-202606-001" in nos

    def test_date_filter_inclusive(self) -> None:
        """Range edges (first + last day of months) must be included."""
        conversions = [
            _seed_conversion("opc_a", "starter", 199_000, "2026-04-30"),  # excluded
            _seed_conversion("opc_b", "starter", 199_000, "2026-05-01"),  # included
            _seed_conversion("opc_c", "starter", 199_000, "2026-05-31"),  # included
            _seed_conversion("opc_d", "starter", 199_000, "2026-06-01"),  # excluded
        ]
        rows = build_misa_rows(conversions, "2026-05", "2026-05")
        assert len(rows) == 2
        assert {r.partner_id for r in rows} == {"opc_b", "opc_c"}

    def test_utf8_bom_present(self) -> None:
        """First 3 bytes of encoded CSV must be EF BB BF (UTF-8 BOM)."""
        csv_bytes = to_csv_bytes([])
        assert csv_bytes[:3] == b"\xef\xbb\xbf"

    def test_vietnamese_accent_roundtrip(self) -> None:
        """Names with accents must serialize + parse back identically."""
        conversions = [_seed_conversion(
            "opc_001_test", "starter_vnd", 199_000, "2026-05-15",
        )]
        # Description contains tier — substitute Vietnamese ourselves
        rows = build_misa_rows(conversions, "2026-05", "2026-05")
        rows[0].description = "Phí pilot tháng 5 — Nguyễn Văn Ánh"
        csv_bytes = to_csv_bytes(rows)
        # Decode + parse via csv reader, verify text preserved
        text = csv_bytes.decode("utf-8-sig")  # strips BOM
        reader = csv.DictReader(io.StringIO(text))
        parsed = list(reader)
        assert len(parsed) == 1
        assert "Nguyễn Văn Ánh" in parsed[0]["description"]
        assert "tháng" in parsed[0]["description"]

    def test_default_codes_drafted(self) -> None:
        """DRAFT codes 131/511/33311 ship as defaults (accountant review pending)."""
        rows = build_misa_rows(
            [_seed_conversion("opc_a", "starter", 199_000, "2026-05-15")],
            "2026-05", "2026-05",
        )
        assert rows[0].debit_account == "131"
        assert rows[0].credit_account == "511"

    def test_env_override_swaps_codes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Founder can swap codes via env without code change."""
        monkeypatch.setenv("MEKONG_MISA_DEBIT_ACCOUNT", "1311")
        monkeypatch.setenv("MEKONG_MISA_CREDIT_ACCOUNT", "5113")
        rows = build_misa_rows(
            [_seed_conversion("opc_a", "starter", 199_000, "2026-05-15")],
            "2026-05", "2026-05",
        )
        assert rows[0].debit_account == "1311"
        assert rows[0].credit_account == "5113"

    def test_invalid_range_raises(self) -> None:
        """to_ym before from_ym is a logic error → ValueError."""
        with pytest.raises(ValueError, match="Range invalid"):
            build_misa_rows([], "2026-06", "2026-05")

    def test_bad_ym_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Expected YYYY-MM"):
            build_misa_rows([], "2026-5", "2026-05")  # missing leading zero


# ---------- HTTP route tests ----------

class TestMISARoute:
    HEADERS = {"Authorization": "Bearer test_admin_xyz"}

    def test_route_returns_csv_content_type(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        _write_conversions(tmp_path, [
            _seed_conversion("opc_001_a", "starter_vnd", 199_000, "2026-05-15"),
        ])
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-05&to=2026-05",
            headers=self.HEADERS,
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        # Phase 8 P02: org_id included in filename (default when omitted)
        assert "misa-pilots-default-2026-05-2026-05.csv" in resp.headers["content-disposition"]

    def test_route_admin_token_required(self, client: TestClient) -> None:
        """No Authorization header → 401."""
        resp = client.get("/v1/pilot/export/misa?from=2026-05&to=2026-05")
        assert resp.status_code == 401

    def test_route_invalid_month_format_422(self, client: TestClient) -> None:
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-5&to=2026-05",
            headers=self.HEADERS,
        )
        assert resp.status_code == 422

    def test_route_empty_range_returns_header_only(
        self, client: TestClient
    ) -> None:
        """Empty conversion store → header-only CSV (not 404)."""
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-05&to=2026-05",
            headers=self.HEADERS,
        )
        assert resp.status_code == 200
        # BOM + header + trailing newline
        body = resp.content
        assert body.startswith(b"\xef\xbb\xbf")
        text = body.decode("utf-8-sig")
        assert text.strip().splitlines() == [",".join(MISA_HEADERS)]

    def test_route_includes_conversions_in_range(
        self, client: TestClient, tmp_path: Path
    ) -> None:
        _write_conversions(tmp_path, [
            _seed_conversion("opc_001_a", "starter_vnd", 199_000, "2026-04-15"),  # excl
            _seed_conversion("opc_002_b", "starter_vnd", 199_000, "2026-05-10"),
            _seed_conversion("opc_003_c", "growth_vnd", 299_000, "2026-05-20"),
            _seed_conversion("opc_004_d", "starter_vnd", 199_000, "2026-06-05"),  # excl
        ])
        resp = client.get(
            "/v1/pilot/export/misa?from=2026-05&to=2026-05",
            headers=self.HEADERS,
        )
        text = resp.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 2
        partner_ids = {r["partner_id"] for r in rows}
        assert partner_ids == {"opc_002_b", "opc_003_c"}
        # Amounts preserved
        amounts = {int(r["amount_vnd"]) for r in rows}
        assert amounts == {199_000, 299_000}
