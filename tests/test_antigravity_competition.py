"""
Test Suite for Vietnamese Competition, Antitrust & Economic Concentration Suite (Phase 94).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- CompetitionEngine domain logic (Luật Cạnh tranh 2018, Nghị định 35/2020/NĐ-CP).
- CLI commands with Rich tables and headless --json mode.
- Dual MCP server handlers (FastMCP and fallback JSON-RPC 2.0).
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.competition_engine import CompetitionEngine


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestCompetitionBoundary:
    """Verifies that competition_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "competition_engine.py")
        with open(engine_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=engine_path)

        forbidden_prefixes = ("requests", "httpx", "aiohttp", "boto3", "openai", "anthropic", "google")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(forbidden_prefixes), f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(forbidden_prefixes), f"Forbidden from-import: {node.module}"


class TestCompetitionEngine:
    """Tests core domain and regulatory business logic of CompetitionEngine."""

    def test_audit_economic_concentration_below_threshold(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_economic_concentration(
            merger_name="Sáp nhập Doanh nghiệp Nhỏ",
            acquiring_entity="Công ty A",
            target_entity="Công ty B",
            total_assets_vnd=2_000_000_000_000.0,      # < 3,000 tỷ
            total_revenue_vnd=2_500_000_000_000.0,     # < 3,000 tỷ
            transaction_value_vnd=600_000_000_000.0,   # < 1,000 tỷ
            combined_market_share_pct=15.0,            # < 20.0%
        )
        assert res["requires_notification"] is False
        assert res["verdict"] == "CLEARED_WITHOUT_NOTIFICATION"
        assert len(res["notification_triggers"]) == 0

    def test_audit_economic_concentration_notification_required(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_economic_concentration(
            merger_name="Sáp nhập Chuỗi Bán lẻ",
            acquiring_entity="Tập đoàn Bán lẻ A",
            target_entity="Chuỗi B",
            total_assets_vnd=3_500_000_000_000.0,     # >= 3,000 tỷ
            total_revenue_vnd=4_200_000_000_000.0,    # >= 3,000 tỷ
            transaction_value_vnd=1_200_000_000_000.0,# >= 1,000 tỷ
            combined_market_share_pct=26.5,           # >= 20.0%
            pre_hhi=1200.0,
            post_hhi=1500.0,
        )
        assert res["requires_notification"] is True
        assert res["verdict"] == "NOTIFICATION_REQUIRED_PRELIMINARY"
        assert len(res["notification_triggers"]) == 4

    def test_audit_economic_concentration_high_hhi_official_review(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_economic_concentration(
            merger_name="Sáp nhập Thép Tập trung cao",
            acquiring_entity="Thép A",
            target_entity="Thép B",
            total_assets_vnd=5_000_000_000_000.0,
            total_revenue_vnd=6_000_000_000_000.0,
            transaction_value_vnd=2_000_000_000_000.0,
            combined_market_share_pct=38.0,
            pre_hhi=1650.0,
            post_hhi=1950.0,  # post_hhi > 1800 and delta > 200
        )
        assert res["requires_notification"] is True
        assert res["verdict"] == "SUBJECT_TO_OFFICIAL_REVIEW"
        assert res["delta_hhi"] == 300.0

    def test_audit_economic_concentration_prohibited_over_50_pct(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_economic_concentration(
            merger_name="Độc quyền Độc tôn",
            acquiring_entity="Tập đoàn X",
            target_entity="Tập đoàn Y",
            total_assets_vnd=10_000_000_000_000.0,
            total_revenue_vnd=12_000_000_000_000.0,
            transaction_value_vnd=4_000_000_000_000.0,
            combined_market_share_pct=58.0,  # >= 50%
        )
        assert res["verdict"] == "PROHIBITED_SIGNIFICANT_RESTRAINT"

    def test_audit_economic_concentration_credit_institution(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        # For credit institutions, threshold is 12,000B assets and 10,000B revenue
        res = engine.audit_economic_concentration(
            merger_name="Hợp nhất Ngân hàng Nhỏ",
            acquiring_entity="Ngân hàng A",
            target_entity="Ngân hàng B",
            total_assets_vnd=10_000_000_000_000.0,    # < 12,000 tỷ
            total_revenue_vnd=8_000_000_000_000.0,    # < 10,000 tỷ
            transaction_value_vnd=800_000_000_000.0,  # < 1,000 tỷ
            combined_market_share_pct=14.0,           # < 20%
            is_credit_institution=True,
        )
        assert res["requires_notification"] is False
        assert res["verdict"] == "CLEARED_WITHOUT_NOTIFICATION"

    def test_assess_market_dominance_single_over_30(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.assess_market_dominance(
            enterprise_name="Nền tảng Công nghệ Mekong",
            market_share_pct=35.0,  # >= 30%
        )
        assert res["is_dominant"] is True
        assert "SINGLE_DOMINANCE" in res["dominance_basis"]
        assert res["risk_level"] == "HIGH"
        assert len(res["compliance_guidelines"]) >= 4

    def test_assess_market_dominance_cr2_collective(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.assess_market_dominance(
            enterprise_name="Doanh nghiệp A",
            market_share_pct=26.0,
            cr_group_shares=[26.0, 25.0, 15.0],  # 26 + 25 = 51% >= 50%
        )
        assert res["is_dominant"] is True
        assert "COLLECTIVE_DOMINANCE_CR2" in res["dominance_basis"]

    def test_assess_market_dominance_cr3_collective(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.assess_market_dominance(
            enterprise_name="Doanh nghiệp B",
            market_share_pct=24.0,
            cr_group_shares=[24.0, 22.0, 20.0, 10.0],  # 24 + 22 + 20 = 66% >= 65%
        )
        assert res["is_dominant"] is True
        assert "COLLECTIVE_DOMINANCE_CR3" in res["dominance_basis"]

    def test_assess_market_dominance_cr4_collective(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.assess_market_dominance(
            enterprise_name="Doanh nghiệp C",
            market_share_pct=20.0,
            cr_group_shares=[20.0, 20.0, 20.0, 16.0],  # 76% >= 75%
        )
        assert res["is_dominant"] is True
        assert "COLLECTIVE_DOMINANCE_CR4" in res["dominance_basis"]

    def test_assess_market_dominance_non_dominant(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.assess_market_dominance(
            enterprise_name="SME Khởi nghiệp",
            market_share_pct=5.0,
            cr_group_shares=[5.0, 4.0, 3.0, 2.0],
        )
        assert res["is_dominant"] is False
        assert res["risk_level"] == "LOW"

    def test_audit_anti_competitive_agreement_horizontal_cartel(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_anti_competitive_agreement(
            agreement_title="Thỏa thuận Giá Sàn Xi măng",
            parties_count=4,
            agreement_type="PRICE_FIXING",
            is_horizontal=True,
            annual_revenue_vnd=200_000_000_000.0,
        )
        assert res["is_prohibited"] is True
        assert "STRICTLY_PROHIBITED_HORIZONTAL_CARTEL" in res["violation_nature"]
        assert res["max_fine_rate_pct"] == 5.0
        assert res["potential_fine_vnd"] == 10_000_000_000.0

    def test_audit_anti_competitive_agreement_bid_rigging(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_anti_competitive_agreement(
            agreement_title="Thông thầu Gói xây lắp",
            parties_count=3,
            agreement_type="BID_RIGGING",
            annual_revenue_vnd=50_000_000_000.0,
        )
        assert res["is_prohibited"] is True
        assert "CRIMINAL_BID_RIGGING_COLLUSION" in res["violation_nature"]
        assert res["max_fine_rate_pct"] == 10.0

    def test_audit_anti_competitive_agreement_legal_vertical(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.audit_anti_competitive_agreement(
            agreement_title="Hợp đồng Phân phối Đại lý Độc quyền Địa phương",
            parties_count=2,
            agreement_type="DISTRIBUTION",
            is_horizontal=False,
        )
        assert res["is_prohibited"] is False
        assert "COMPLIANT" in res["violation_nature"]

    def test_apply_leniency_program_first_applicant(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res = engine.apply_leniency_program(
            enterprise_name="Công ty Tự Thú A",
            violation_id="AGR-PRICE-01",
            submission_order=1,
            self_confessed=True,
            submitted_evidence=True,
        )
        assert res["is_eligible"] is True
        assert res["fine_exemption_pct"] == 100.0
        assert "Miễn 100%" in res["status"]

    def test_apply_leniency_program_second_and_third(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res2 = engine.apply_leniency_program(
            enterprise_name="Công ty Hợp tác B",
            violation_id="AGR-PRICE-01",
            submission_order=2,
        )
        assert res2["fine_exemption_pct"] == 60.0

        res3 = engine.apply_leniency_program(
            enterprise_name="Công ty Hợp tác C",
            violation_id="AGR-PRICE-01",
            submission_order=3,
        )
        assert res3["fine_exemption_pct"] == 40.0

    def test_apply_leniency_program_fourth_rejected(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        res4 = engine.apply_leniency_program(
            enterprise_name="Công ty Đến Muộn D",
            violation_id="AGR-PRICE-01",
            submission_order=4,
        )
        assert res4["fine_exemption_pct"] == 0.0
        assert "QUOTA_EXCEEDED" in res4["status"]

    def test_list_records_and_status(self, temp_db):
        engine = CompetitionEngine(db_path=temp_db)
        engine.audit_economic_concentration("Deal 1", "A", "B", 4e12, 4e12, 1.5e12, 25.0)
        engine.assess_market_dominance("Company D", 35.0)
        engine.audit_anti_competitive_agreement("Cartel C", 3, "PRICE_FIXING", True)
        engine.apply_leniency_program("Company L", "AGR-1", 1)

        all_records = engine.list_records(category="all")
        assert len(all_records) == 4

        conc_records = engine.list_records(category="concentrations")
        assert len(conc_records) == 1

        dom_records = engine.list_records(category="dominance")
        assert len(dom_records) == 1

        agr_records = engine.list_records(category="agreements")
        assert len(agr_records) == 1

        len_records = engine.list_records(category="leniency")
        assert len(len_records) == 1

        status = engine.get_status()
        assert status["total_concentrations_audited"] == 1
        assert status["notifications_required_count"] == 1
        assert status["total_dominance_assessments"] == 1
        assert status["dominant_positions_confirmed"] == 1
        assert status["total_agreements_audited"] == 1
        assert status["prohibited_cartels_detected"] == 1
        assert status["leniency_applications_processed"] == 1


class TestCompetitionCLI:
    """Verifies competition Typer CLI commands in normal and JSON mode."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = build_app()
        self.runner = CliRunner()

    def test_cli_main_and_status(self):
        res = self.runner.invoke(self.app, ["competition", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert "regulatory_framework" in data
        assert "supervisory_authority" in data

    def test_cli_merger_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "competition",
                "merger",
                "Thương vụ M&A Thử nghiệm",
                "--buyer",
                "Tập đoàn A",
                "--target",
                "Công ty B",
                "--assets",
                "3500000000000",
                "--revenue",
                "4000000000000",
                "--value",
                "1200000000000",
                "--share",
                "25.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["merger_name"] == "Thương vụ M&A Thử nghiệm"
        assert data["requires_notification"] is True

    def test_cli_dominance_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "competition",
                "dominance",
                "Tập đoàn Độc quyền",
                "--share",
                "38.0",
                "--cr-shares",
                "38.0,20.0,15.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_dominant"] is True
        assert data["risk_level"] == "HIGH"

    def test_cli_agreement_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "competition",
                "agreement",
                "Thỏa thuận Cartel Giá",
                "--parties",
                "3",
                "--type",
                "PRICE_FIXING",
                "--horizontal",
                "--revenue",
                "100000000000",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_prohibited"] is True

    def test_cli_leniency_cmd(self):
        res = self.runner.invoke(
            self.app,
            [
                "competition",
                "leniency",
                "Công ty Hối lỗi",
                "--violation",
                "AGR-001",
                "--order",
                "1",
                "--confess",
                "--evidence",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["fine_exemption_pct"] == 100.0

    def test_cli_list_cmd(self):
        res = self.runner.invoke(self.app, ["competition", "list", "all", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestCompetitionMCP:
    """Verifies dual MCP servers handle competition tools properly."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-competition-core")

        # 1. Merger
        res_mrg = json.loads(
            server._handle_competition_merger(
                merger_name="Deal Core",
                total_assets_vnd=3.5e12,
                total_revenue_vnd=4e12,
                transaction_value_vnd=1.2e12,
                combined_market_share_pct=25.0,
            )
        )
        assert res_mrg["requires_notification"] is True

        # 2. Dominance
        res_dom = json.loads(server._handle_competition_dominance(enterprise_name="Company Core", market_share_pct=35.0))
        assert res_dom["is_dominant"] is True

        # 3. Agreement
        res_agr = json.loads(
            server._handle_competition_agreement(
                agreement_title="Cartel Core",
                parties_count=3,
                agreement_type="PRICE_FIXING",
                is_horizontal=True,
            )
        )
        assert res_agr["is_prohibited"] is True

        # 4. Leniency
        res_len = json.loads(
            server._handle_competition_leniency(enterprise_name="Company Leniency Core", submission_order=1)
        )
        assert res_len["fine_exemption_pct"] == 100.0

        # 5. List
        res_lst = json.loads(server._handle_competition_list(category="all", limit=10))
        assert isinstance(res_lst, list)

        # 6. Status
        res_stat = json.loads(server._handle_competition_status())
        assert res_stat["status"] == "operational"

    def test_scripts_mcp_server_handlers(self):
        import scripts.mcp_server as s_mcp

        # 1. Merger
        res_mrg = json.loads(
            s_mcp.handle_competition_merger({
                "merger_name": "Deal Scripts",
                "total_assets_vnd": 3.5e12,
                "total_revenue_vnd": 4e12,
                "transaction_value_vnd": 1.2e12,
                "combined_market_share_pct": 25.0,
            })
        )
        assert res_mrg["requires_notification"] is True

        # 2. Dominance
        res_dom = json.loads(
            s_mcp.handle_competition_dominance({"enterprise_name": "Company Scripts", "market_share_pct": 35.0})
        )
        assert res_dom["is_dominant"] is True

        # 3. Agreement
        res_agr = json.loads(
            s_mcp.handle_competition_agreement({
                "agreement_title": "Cartel Scripts",
                "parties_count": 3,
                "agreement_type": "PRICE_FIXING",
                "is_horizontal": True,
            })
        )
        assert res_agr["is_prohibited"] is True

        # 4. Leniency
        res_len = json.loads(
            s_mcp.handle_competition_leniency({"enterprise_name": "Company Leniency Scripts", "submission_order": 1})
        )
        assert res_len["fine_exemption_pct"] == 100.0

        # 5. List
        res_lst = json.loads(s_mcp.handle_competition_list({"category": "all", "limit": 10}))
        assert isinstance(res_lst, list)

        # 6. Status
        res_stat = json.loads(s_mcp.handle_competition_status({}))
        assert res_stat["status"] == "operational"
