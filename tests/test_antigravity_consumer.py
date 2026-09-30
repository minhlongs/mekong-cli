"""
Test Suite for Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Suite (Phase 99).
Covers:
- Core AST boundary compliance (zero external vendor SDKs / HTTP).
- ConsumerEngine domain logic (Luật Bảo vệ quyền lợi người tiêu dùng 2023, Nghị định 55/2024/NĐ-CP, Quyết định 07/2024/QĐ-TTg).
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
from src.core.consumer_engine import (
    ConsumerEngine,
    SUMMARY_COURT_TRANSACTION_LIMIT_VND,
    REGISTRATION_REQUIRED_INDUSTRIES,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestConsumerBoundary:
    """Verifies that consumer_engine adheres to pure Python standard library constraints."""

    def test_no_forbidden_vendor_sdk_imports(self):
        engine_path = os.path.join(os.getcwd(), "src", "core", "consumer_engine.py")
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


class TestConsumerEngine:
    """Tests core domain and regulatory business logic of ConsumerEngine."""

    def test_audit_digital_platform_compliant(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.audit_digital_platform_compliance(
            platform_name="Sàn Thương Mại Điện Tử MekongMall",
            platform_type="E_COMMERCE_MARKETPLACE",
            has_transparent_algorithm_option=True,
            has_dark_patterns=False,
            dispute_mechanism_active=True,
            return_policy_days=15,
            seller_verification_rate_pct=100.0,
        )

        assert res["is_compliant"] is True
        assert len(res["violations"]) == 0
        assert "COMPLIANT" in res["compliance_rating"]
        assert res["audit_id"].startswith("PLT-AUD-")

    def test_audit_digital_platform_violations(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.audit_digital_platform_compliance(
            platform_name="App Bán Hàng Trôi Nổi X",
            platform_type="CROSS_BORDER_APP",
            has_transparent_algorithm_option=False,
            has_dark_patterns=True,
            dispute_mechanism_active=False,
            return_policy_days=3,  # < 7 days
            seller_verification_rate_pct=65.0,  # < 100%
        )

        assert res["is_compliant"] is False
        assert len(res["violations"]) == 5
        assert any("quảng cáo hướng đối tượng" in v for v in res["violations"])
        assert any("Dark Patterns" in v for v in res["violations"])
        assert any("03 ngày làm việc" in v for v in res["violations"])
        assert any("tối thiểu 07 ngày" in v for v in res["violations"])
        assert any("xác minh danh tính" in v for v in res["violations"])
        assert "CRITICAL_NON_COMPLIANT" in res["compliance_rating"]

    def test_audit_standard_contract_terms_valid(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.audit_standard_contract_terms(
            contract_title="Hợp đồng dịch vụ viễn thông di động mẫu",
            industry_type="TELECOM",
            excludes_seller_liability=False,
            restricts_consumer_dispute_rights=False,
            allows_unilateral_price_change=False,
            registered_with_ncc=True,
        )

        assert res["is_valid"] is True
        assert len(res["void_clauses"]) == 0
        assert len(res["recommendations"]) >= 1

    def test_audit_standard_contract_terms_void_clauses(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.audit_standard_contract_terms(
            contract_title="Điều khoản mua sắm căn hộ chung cư lấn lướt",
            industry_type="REAL_ESTATE_APARTMENT",
            excludes_seller_liability=True,
            restricts_consumer_dispute_rights=True,
            allows_unilateral_price_change=True,
            registered_with_ncc=False,
        )

        assert res["is_valid"] is False
        assert len(res["void_clauses"]) == 4
        assert any("Ủy ban Cạnh tranh Quốc gia" in v for v in res["void_clauses"])
        assert any("Loại trừ hoặc hạn chế trách nhiệm" in v for v in res["void_clauses"])
        assert any("Hạn chế quyền khiếu nại" in v for v in res["void_clauses"])
        assert any("đơn phương thay đổi giá cả" in v for v in res["void_clauses"])

    def test_manage_defective_product_recall_success(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.manage_defective_product_recall(
            product_name="Nồi chiên không dầu model AF-2026",
            defect_type="GROUP_A_LIFE_THREATENING",
            batch_serial="BAT-2026-X1",
            units_distributed=5000,
            units_recalled=4900,
            public_announcement_made_24h=True,
            reported_to_ministry=True,
        )

        assert res["completion_rate_pct"] == 98.0
        assert res["public_announcement_made_24h"] is True
        assert "SUCCESSFUL_RECALL_PROGRESS" in res["recall_status"]
        assert res["recall_id"].startswith("RCL-PRD-")

    def test_manage_defective_product_recall_critical_violation(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.manage_defective_product_recall(
            product_name="Xe điện lỗi hệ thống phanh ABS",
            defect_type="GROUP_A_LIFE_THREATENING",
            batch_serial="EV-BRAKE-009",
            units_distributed=1000,
            units_recalled=200,
            public_announcement_made_24h=False,
            reported_to_ministry=False,
        )

        assert res["completion_rate_pct"] == 20.0
        assert "CRITICAL_NON_COMPLIANT_RECALL" in res["recall_status"]
        assert any("không công bố công khai trong 24 giờ" in m for m in res["remedial_measures"])
        assert any("Bộ Công Thương" in m for m in res["remedial_measures"])

    def test_assess_consumer_dispute_summary_court_eligible(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.assess_consumer_dispute(
            complainant_name="Trần Thị Mai",
            merchant_name="Công ty Bán lẻ Điện máy Online",
            transaction_value_vnd=35_000_000.0,
            dispute_method="SUMMARY_COURT_PROCEEDING",
            has_evidence_invoice=True,
            seller_refused_compromise=True,
        )

        assert res["eligible_for_summary_court"] is True
        assert res["court_fee_exempt"] is True
        assert any("THỦ TỤC RÚT GỌN TẠI TÒA ÁN" in step for step in res["recommended_next_steps"])
        assert any("MIỄN NỘP TIỀN TẠM ỨNG ÁN PHÍ" in step for step in res["recommended_next_steps"])

    def test_assess_consumer_dispute_ineligible_summary_court(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        res = engine.assess_consumer_dispute(
            complainant_name="Lê Văn Hùng",
            merchant_name="Đại lý Ô tô Siêu Sang",
            transaction_value_vnd=850_000_000.0,  # > 100M VND
            dispute_method="COURT_PROCEEDING",
            has_evidence_invoice=False,
            seller_refused_compromise=True,
        )

        assert res["eligible_for_summary_court"] is False
        assert any("bổ sung chứng từ, hóa đơn" in step for step in res["recommended_next_steps"])
        assert any("100 triệu VND" in step for step in res["recommended_next_steps"])

    def test_list_records_and_status(self, temp_db):
        engine = ConsumerEngine(db_path=temp_db)
        engine.audit_digital_platform_compliance(platform_name="Platform A")
        engine.audit_standard_contract_terms(contract_title="Contract B")
        engine.manage_defective_product_recall(product_name="Product C")
        engine.assess_consumer_dispute(complainant_name="User D", merchant_name="Store E")

        all_records = engine.list_records(category="all")
        assert len(all_records) == 4

        platforms = engine.list_records(category="platforms")
        assert len(platforms) == 1
        assert platforms[0]["platform_name"] == "Platform A"

        status = engine.get_status()
        assert status["status"] == "operational"
        assert status["total_platforms_audited"] == 1
        assert status["total_standard_contracts_reviewed"] == 1
        assert status["active_product_recalls"] == 1
        assert status["consumer_dispute_cases_total"] == 1


class TestConsumerCLI:
    """Tests Typer CLI commands for Consumer Rights Protection Suite."""

    def setup_method(self):
        self.runner = CliRunner()
        self.app = build_app()

    def test_cli_consumer_status_json(self):
        res = self.runner.invoke(self.app, ["consumer", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "operational"
        assert "regulatory_framework" in data
        assert "competent_authority" in data

    def test_cli_consumer_platform_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "consumer",
                "platform",
                "Tiki Marketplace",
                "--type",
                "E_COMMERCE_MARKETPLACE",
                "--algo",
                "--dispute",
                "--return-days",
                "30",
                "--verify-rate",
                "100.0",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["platform_name"] == "Tiki Marketplace"
        assert data["is_compliant"] is True

    def test_cli_consumer_contract_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "consumer",
                "contract",
                "Hợp đồng cung cấp nước sạch sinh hoạt",
                "--industry",
                "CLEAN_WATER",
                "--ncc",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["contract_title"] == "Hợp đồng cung cấp nước sạch sinh hoạt"
        assert data["is_valid"] is True

    def test_cli_consumer_recall_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "consumer",
                "recall",
                "Lò nướng đối lưu model OV-99",
                "--defect-type",
                "GROUP_A_LIFE_THREATENING",
                "--distributed",
                "2000",
                "--recalled",
                "1950",
                "--announce",
                "--report",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["product_name"] == "Lò nướng đối lưu model OV-99"
        assert data["completion_rate_pct"] == 97.5

    def test_cli_consumer_dispute_json(self):
        res = self.runner.invoke(
            self.app,
            [
                "consumer",
                "dispute",
                "Hoàng Thị Bình",
                "--merchant",
                "Điện máy ABC",
                "--value",
                "18000000",
                "--invoice",
                "--refused",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["complainant_name"] == "Hoàng Thị Bình"
        assert data["eligible_for_summary_court"] is True
        assert data["court_fee_exempt"] is True

    def test_cli_consumer_list_json(self):
        res = self.runner.invoke(self.app, ["consumer", "list", "all", "--limit", "10", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert isinstance(data, list)


class TestConsumerMCP:
    """Tests dual FastMCP and pure-Python JSON-RPC handlers for Consumer Suite."""

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-consumer-core")

        # Platform audit
        p_res = json.loads(
            server._handle_consumer_platform(
                platform_name="MCP Digital Platform",
                return_policy_days=14,
                seller_verification_rate_pct=100.0,
            )
        )
        assert p_res["is_compliant"] is True

        # Contract terms
        c_res = json.loads(
            server._handle_consumer_contract(
                contract_title="MCP Telecom Terms",
                industry_type="TELECOM",
                registered_with_ncc=True,
            )
        )
        assert c_res["is_valid"] is True

        # Product recall
        r_res = json.loads(
            server._handle_consumer_recall(
                product_name="MCP Air Fryer",
                defect_type="GROUP_A_LIFE_THREATENING",
                units_distributed=1000,
                units_recalled=950,
            )
        )
        assert r_res["completion_rate_pct"] == 95.0

        # Dispute case
        d_res = json.loads(
            server._handle_consumer_dispute(
                complainant_name="MCP Complainant",
                merchant_name="MCP Seller",
                transaction_value_vnd=12_000_000.0,
            )
        )
        assert d_res["eligible_for_summary_court"] is True

        # List and status
        l_res = json.loads(server._handle_consumer_list(category="all", limit=5))
        assert isinstance(l_res, list)

        s_res = json.loads(server._handle_consumer_status())
        assert s_res["status"] == "operational"

    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_consumer_platform,
            handle_consumer_contract,
            handle_consumer_recall,
            handle_consumer_dispute,
            handle_consumer_list,
            handle_consumer_status,
            CORE_HANDLERS,
        )

        assert "mekong_consumer_platform" in CORE_HANDLERS
        assert "mekong_consumer_contract" in CORE_HANDLERS
        assert "mekong_consumer_recall" in CORE_HANDLERS
        assert "mekong_consumer_dispute" in CORE_HANDLERS
        assert "mekong_consumer_list" in CORE_HANDLERS
        assert "mekong_consumer_status" in CORE_HANDLERS

        p_res = json.loads(handle_consumer_platform({"platform_name": "Pure JSON-RPC App", "return_policy_days": 10}))
        assert p_res["is_compliant"] is True

        c_res = json.loads(handle_consumer_contract({"contract_title": "Pure Contract", "industry_type": "E_COMMERCE"}))
        assert c_res["is_valid"] is True

        r_res = json.loads(handle_consumer_recall({"product_name": "Pure Recall Item", "units_distributed": 100, "units_recalled": 90}))
        assert r_res["completion_rate_pct"] == 90.0

        d_res = json.loads(handle_consumer_dispute({"complainant_name": "Consumer A", "merchant_name": "Seller B", "transaction_value_vnd": 20000000}))
        assert d_res["eligible_for_summary_court"] is True

        l_res = json.loads(handle_consumer_list({"category": "all", "limit": 5}))
        assert isinstance(l_res, list)

        s_res = json.loads(handle_consumer_status({}))
        assert s_res["status"] == "operational"
