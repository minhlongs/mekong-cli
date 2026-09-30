"""
Test suite for Vietnamese Commercial Arbitration, Out-of-Court Dispute Resolution & New York Convention Suite (Phase 107).
Covers:
- ArbitrationEngine (pure standard-library engine, SQLite WAL persistence).
- Statutory compliance: Law on Commercial Arbitration 2010 (Law 54/2010/QH12), Resolution 01/2014/NQ-HĐTP,
  Civil Procedure Code 2015 (Part Seven, Arts 423-451), New York Convention 1958, VIAC Rules of Arbitration.
- CLI surface (mekong arbitration clause/claim/award/foreign/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.arbitration_engine import ArbitrationEngine
from src.cli.commands.arbitration_command import arbitration_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_arbitration.db")
        yield db_path


class TestArbitrationEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "arbitration_agreements" in tables
        assert "arbitration_claims" in tables
        assert "arbitral_awards" in tables
        assert "foreign_award_enforcements" in tables

    def test_clause_drafting_valid(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.draft_arbitration_clause(
            contract_title="Hợp đồng EPC Nhà máy Điện mặt trời",
            institution="VIAC",
            seat="Hà Nội",
            governing_law="VIETNAMESE_LAW",
            language="VIETNAMESE",
            num_arbitrators=3,
        )
        assert res["clause_id"].startswith("ARB-CLS-")
        assert res["is_valid"] is True
        assert res["valid_clause"] is True
        assert res["institution"] == "VIAC"
        assert res["num_arbitrators"] == 3
        assert len(res["violations"]) == 0
        assert "Vietnam International Arbitration Centre" in res["model_clause"]

    def test_clause_even_arbitrators_flawed(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.draft_arbitration_clause(
            contract_title="Hợp đồng Mua bán Quốc tế",
            institution="SIAC",
            seat="Singapore",
            governing_law="ENGLISH_LAW",
            language="ENGLISH",
            num_arbitrators=2,  # Even number violates Law 54/2010 Art 39
        )
        assert res["is_valid"] is False
        assert any("trọng tài viên phải là số lẻ" in flaw.lower() for flaw in res["violations"])

    def test_clause_unsupported_institution(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.draft_arbitration_clause(
            contract_title="Hợp đồng Thầu Phụ",
            institution="UNKNOWN_CHAMBER",
            num_arbitrators=1,
        )
        assert res["is_valid"] is False
        assert any("Tổ chức trọng tài phải thuộc danh mục hợp lệ" in flaw for flaw in res["violations"])

    def test_viac_fee_calculation_brackets(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        # <= 500M VND
        fee_small_3 = engine.calculate_viac_fee(300_000_000, 3)
        assert fee_small_3 == 30_000_000.0
        fee_small_1 = engine.calculate_viac_fee(300_000_000, 1)
        assert fee_small_1 == 30_000_000.0 * 0.7  # 30% discount for sole arbitrator

        # 500M - 2B VND (e.g. 800M: 30M + 0.04 * 300M = 30M + 12M = 42M)
        fee_tier2 = engine.calculate_viac_fee(800_000_000, 3)
        assert fee_tier2 == 42_000_000.0

        # 2B - 10B VND (e.g. 3B: 90M + 0.025 * 1B = 90M + 25M = 115M)
        fee_tier3 = engine.calculate_viac_fee(3_000_000_000, 3)
        assert fee_tier3 == 115_000_000.0

        # > 50B VND (e.g. 60B: 890M + 0.008 * 10B = 890M + 80M = 970M)
        fee_tier6 = engine.calculate_viac_fee(60_000_000_000, 3)
        assert fee_tier6 == 970_000_000.0

    def test_file_arbitration_claim_registered(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        # Create a clause first
        clause = engine.draft_arbitration_clause(contract_title="Hợp đồng Cung cấp Thiết bị")

        res = engine.file_arbitration_claim(
            claimant="Tập đoàn Phát triển Hạ tầng",
            respondent="Công ty Vật liệu Xây dựng Thăng Long",
            dispute_subject="Chậm giao hàng và vi phạm chất lượng thép",
            dispute_amount_vnd=10_000_000_000,
            clause_id=clause["clause_id"],
            tribunal_size=3,
        )
        assert res["claim_id"].startswith("ARB-CLM-")
        assert res["status"] == "CLAIM_REGISTERED"
        assert res["claimant"] == "Tập đoàn Phát triển Hạ tầng"
        assert res["dispute_amount_vnd"] == 10_000_000_000
        assert res["arbitration_fee_vnd"] > 0
        assert res["tribunal_size"] == 3

    def test_render_arbitral_award_final_and_binding(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        claim = engine.file_arbitration_claim(
            claimant="Ngân hàng TMCP Quốc tế",
            respondent="Công ty CP Xuất nhập khẩu Hoàng Hà",
            dispute_subject="Nợ quá hạn tín dụng thương mại",
            dispute_amount_vnd=4_000_000_000,
            tribunal_size=3,
        )

        res = engine.render_arbitral_award(
            claim_id=claim["claim_id"],
            tribunal_president="TS. Trần Hữu Huỳnh",
            claim_granted_pct=80.0,
            award_date="2026-09-30",
        )
        assert res["award_id"].startswith("ARB-AWD-")
        assert res["status"] == "FINAL_AND_BINDING"
        assert res["amount_awarded_vnd"] == 3_200_000_000.0
        assert res["set_aside_risk"] == "LOW"
        assert len(res["compliance_notes"]) > 0

    def test_render_arbitral_award_nonexistent_claim(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.render_arbitral_award(
            claim_id="ARB-CLM-NONEXISTENT",
            tribunal_president="Trọng tài viên",
            claim_granted_pct=100.0,
        )
        assert res["status"] == "SET_ASIDE_RISK_HIGH"
        assert res["set_aside_risk"] == "HIGH"
        assert any("Không tìm thấy hồ sơ khởi kiện" in v for v in res["compliance_notes"])

    def test_enforce_foreign_award_approved(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.enforce_foreign_award(
            foreign_tribunal="SIAC - Singapore International Arbitration Centre",
            origin_country="Singapore",
            award_amount_usd=5_000_000.0,
            new_york_convention_member=True,
            consular_authenticated=True,
            years_since_award=1.5,
        )
        assert res["dossier_id"].startswith("FRG-ENF-")
        assert res["status"] == "ELIGIBLE_FOR_RECOGNITION"
        assert res["statute_of_limitations_valid"] is True
        assert len(res["violations"]) == 0

    def test_enforce_foreign_award_statute_expired(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.enforce_foreign_award(
            foreign_tribunal="ICC International Court of Arbitration",
            origin_country="France",
            award_amount_usd=2_000_000.0,
            new_york_convention_member=True,
            consular_authenticated=True,
            years_since_award=3.5,  # Exceeds 3 years limit under CPC 2015 Art 451
        )
        assert res["status"] == "REJECTED_INADMISSIBLE"
        assert res["statute_of_limitations_valid"] is False
        assert any("03 năm" in g for g in res["violations"])

    def test_enforce_foreign_award_non_convention_rejected(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.enforce_foreign_award(
            foreign_tribunal="Local Court Arbitral Panel",
            origin_country="NonMemberState",
            award_amount_usd=1_000_000.0,
            new_york_convention_member=False,  # Not in 1958 Convention
            consular_authenticated=True,
            years_since_award=1.0,
        )
        assert res["status"] == "REJECTED_INADMISSIBLE"
        assert any("không phải là thành viên Công ước New York 1958" in g for g in res["violations"])

    def test_enforce_foreign_award_unauthenticated_rejected(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        res = engine.enforce_foreign_award(
            foreign_tribunal="HKIAC - Hong Kong International Arbitration Centre",
            origin_country="Hong Kong",
            award_amount_usd=3_000_000.0,
            new_york_convention_member=True,
            consular_authenticated=False,  # Lacks consular authentication
            years_since_award=1.0,
        )
        assert res["status"] == "REJECTED_INADMISSIBLE"
        assert any("hợp pháp hóa lãnh sự" in g for g in res["violations"])

    def test_list_arbitration_records(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        clause = engine.draft_arbitration_clause(contract_title="Hợp đồng Mua bán")
        claim = engine.file_arbitration_claim(
            claimant="Bên A",
            respondent="Bên B",
            dispute_subject="Tranh chấp hợp đồng",
            dispute_amount_vnd=1_000_000_000,
        )
        award = engine.render_arbitral_award(claim_id=claim["claim_id"])
        foreign = engine.enforce_foreign_award(foreign_tribunal="SIAC")

        all_records = engine.list_arbitration_records(category="ALL", limit=50)
        assert "clauses" in all_records
        assert "claims" in all_records
        assert "awards" in all_records
        assert "foreign_awards" in all_records

        assert len(all_records["clauses"]) >= 1
        assert len(all_records["claims"]) >= 1
        assert len(all_records["awards"]) >= 1
        assert len(all_records["foreign_awards"]) >= 1

        clauses_only = engine.list_arbitration_records(category="CLAUSES", limit=10)
        assert "clauses" in clauses_only
        assert "claims" not in clauses_only

    def test_arbitration_telemetry(self, temp_db: str):
        engine = ArbitrationEngine(db_path=temp_db)
        engine.draft_arbitration_clause(contract_title="Hợp đồng Xây lắp")
        claim = engine.file_arbitration_claim(
            claimant="Bên Mua",
            respondent="Bên Bán",
            dispute_subject="Chậm giao thiết bị",
            dispute_amount_vnd=2_000_000_000,
        )
        engine.render_arbitral_award(claim_id=claim["claim_id"])
        engine.enforce_foreign_award(foreign_tribunal="ICC")

        telemetry = engine.get_arbitration_telemetry()
        assert telemetry["total_arbitration_clauses"] >= 1
        assert telemetry["total_arbitration_claims"] >= 1
        assert telemetry["total_awards_rendered"] >= 1
        assert telemetry["total_foreign_dossiers"] >= 1
        assert telemetry["total_dispute_amount_vnd"] >= 2_000_000_000


class TestArbitrationCLI:
    runner = CliRunner()

    def test_cli_clause_json(self):
        result = self.runner.invoke(
            arbitration_app,
            [
                "clause",
                "Hợp đồng Tổng thầu EPC",
                "--inst",
                "VIAC",
                "--arbitrators",
                "3",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_valid"] is True
        assert data["institution"] == "VIAC"

    def test_cli_clause_console(self):
        result = self.runner.invoke(
            arbitration_app,
            [
                "clause",
                "Hợp đồng Phân phối Độc quyền",
                "--inst",
                "SIAC",
            ],
        )
        assert result.exit_code == 0
        assert "ARB-CLS-" in result.output

    def test_cli_claim_json(self):
        result = self.runner.invoke(
            arbitration_app,
            [
                "claim",
                "Công ty Khai thác Khoáng sản",
                "--respondent",
                "Công ty Chế biến Thép",
                "--amount",
                "8000000000",
                "--subject",
                "Tranh chấp giao quặng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "CLAIM_REGISTERED"
        assert data["dispute_amount_vnd"] == 8_000_000_000

    def test_cli_award_json(self):
        # Create claim first
        claim_res = self.runner.invoke(
            arbitration_app,
            [
                "claim",
                "Bên Khởi Kiện A",
                "--respondent",
                "Bên Bị Kiện B",
                "--amount",
                "5000000000",
                "--json",
            ],
        )
        claim_data = json.loads(claim_res.output)
        cid = claim_data["claim_id"]

        result = self.runner.invoke(
            arbitration_app,
            [
                "award",
                cid,
                "--president",
                "GS. TS. Lê Hồng Hạnh",
                "--granted-pct",
                "90",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "FINAL_AND_BINDING"
        assert data["amount_awarded_vnd"] == 4_500_000_000.0

    def test_cli_foreign_json(self):
        result = self.runner.invoke(
            arbitration_app,
            [
                "foreign",
                "SIAC - Singapore",
                "--country",
                "Singapore",
                "--amount-usd",
                "3500000",
                "--years",
                "1.2",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "ELIGIBLE_FOR_RECOGNITION"
        assert data["statute_of_limitations_valid"] is True

    def test_cli_list_json(self):
        result = self.runner.invoke(
            arbitration_app,
            ["list", "--category", "ALL", "--limit", "10", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "clauses" in data
        assert "claims" in data

    def test_cli_status_json(self):
        result = self.runner.invoke(arbitration_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_arbitration_clauses" in data
        assert "total_arbitration_claims" in data


class TestArbitrationMcpParity:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_arbitration_clause,
            handle_arbitration_claim,
            handle_arbitration_award,
            handle_arbitration_foreign,
            handle_arbitration_list,
            handle_arbitration_status,
        )

        res_cl = handle_arbitration_clause({
            "contract_title": "Hợp đồng Vận tải Biển Quốc tế",
            "institution": "VIAC",
            "seat": "TP. Hồ Chí Minh",
            "governing_law": "VIETNAMESE_LAW",
            "language": "VIETNAMESE",
            "num_arbitrators": 3,
        })
        data_cl = json.loads(res_cl)
        assert data_cl["is_valid"] is True

        res_cm = handle_arbitration_claim({
            "claimant": "Tổng Công ty Hàng Hải",
            "respondent": "Công ty Logistics Phương Nam",
            "dispute_subject": "Chậm giải phóng tàu và phát sinh lưu kho",
            "dispute_amount_vnd": 6_000_000_000.0,
            "tribunal_size": 3,
        })
        data_cm = json.loads(res_cm)
        assert data_cm["status"] == "CLAIM_REGISTERED"

        cid = data_cm["claim_id"]
        res_aw = handle_arbitration_award({
            "claim_id": cid,
            "tribunal_president": "TS. Luật sư Trần Du Lịch",
            "claim_granted_pct": 100.0,
        })
        data_aw = json.loads(res_aw)
        assert data_aw["status"] == "FINAL_AND_BINDING"

        res_fn = handle_arbitration_foreign({
            "foreign_tribunal": "ICC Paris",
            "origin_country": "Pháp",
            "award_amount_usd": 1_800_000.0,
            "new_york_convention_member": True,
            "consular_authenticated": True,
            "years_since_award": 1.0,
        })
        data_fn = json.loads(res_fn)
        assert data_fn["status"] == "ELIGIBLE_FOR_RECOGNITION"

        res_ls = handle_arbitration_list({"category": "ALL", "limit": 10})
        data_ls = json.loads(res_ls)
        assert "clauses" in data_ls

        res_st = handle_arbitration_status({})
        data_st = json.loads(res_st)
        assert "total_arbitration_claims" in data_st

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_cl = server._handle_arbitration_clause(
            contract_title="Hợp đồng BOT Xây dựng Trạm Thu phí",
            institution="VIAC",
            seat="Đà Nẵng",
            num_arbitrators=3,
        )
        data_cl = json.loads(res_cl)
        assert data_cl["is_valid"] is True

        res_cm = server._handle_arbitration_claim(
            claimant="Công ty CP BOT Quốc lộ 1",
            respondent="Nhà thầu Thi công Cầu đường",
            dispute_subject="Chậm tiến độ thi công cầu",
            dispute_amount_vnd=12_000_000_000.0,
        )
        data_cm = json.loads(res_cm)
        assert data_cm["status"] == "CLAIM_REGISTERED"

        cid = data_cm["claim_id"]
        res_aw = server._handle_arbitration_award(
            claim_id=cid,
            tribunal_president="GS. TS. Lê Hồng Hạnh",
            claim_granted_pct=75.0,
        )
        data_aw = json.loads(res_aw)
        assert data_aw["status"] == "FINAL_AND_BINDING"

        res_fn = server._handle_arbitration_foreign(
            foreign_tribunal="HKIAC",
            origin_country="Hong Kong",
            award_amount_usd=4_000_000.0,
            new_york_convention_member=True,
            consular_authenticated=True,
            years_since_award=2.0,
        )
        data_fn = json.loads(res_fn)
        assert data_fn["status"] == "ELIGIBLE_FOR_RECOGNITION"

        res_ls = server._handle_arbitration_list(category="ALL", limit=10)
        data_ls = json.loads(res_ls)
        assert "clauses" in data_ls

        res_st = server._handle_arbitration_status()
        data_st = json.loads(res_st)
        assert "total_arbitration_claims" in data_st
