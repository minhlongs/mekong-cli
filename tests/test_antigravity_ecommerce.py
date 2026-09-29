# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Cross-Border E-Commerce, Platform Tax Invoicing & Marketplace Compliance Engine (Phase 61)."""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.ecommerce_engine import (
    PLATFORM_TYPES,
    FCT_RATES,
    LOW_VALUE_PARCEL_EXEMPTION_VND,
    VND_PER_USD,
    EcommerceEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestEcommerceCoreBoundary:
    """Ensure EcommerceEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/ecommerce_engine.py")
        assert source_path.exists(), "ecommerce_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestEcommerceEngine:
    """Test EcommerceEngine FCT calculations, licensing audits, order settlement, and cross-border parcels."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> EcommerceEngine:
        db_file = tmp_path / "test_ecommerce.db"
        return EcommerceEngine(db_path=db_file)

    def test_constants_and_platform_types(self) -> None:
        assert "SALES_WEBSITE" in PLATFORM_TYPES
        assert "MARKETPLACE" in PLATFORM_TYPES
        assert "SOCIAL_COMMERCE" in PLATFORM_TYPES
        assert PLATFORM_TYPES["SALES_WEBSITE"]["procedure"] == "NOTIFICATION"
        assert PLATFORM_TYPES["MARKETPLACE"]["procedure"] == "REGISTRATION"
        assert PLATFORM_TYPES["MARKETPLACE"]["quarterly_tax_reporting"] is True

        assert "DIGITAL_SERVICES" in FCT_RATES
        assert "ONLINE_ADVERTISING" in FCT_RATES
        assert "CLOUD_SAAS" in FCT_RATES
        assert FCT_RATES["DIGITAL_SERVICES"]["total_fct_pct"] == 10.0
        assert FCT_RATES["CLOUD_SAAS"]["vat_pct"] == 0.0  # Software is VAT exempt
        assert LOW_VALUE_PARCEL_EXEMPTION_VND == 1_000_000.0

    def test_calculate_foreign_contractor_tax_usd(self, engine: EcommerceEngine) -> None:
        # $50,000 USD revenue for online advertising -> 10% FCT (5% VAT + 5% CIT)
        res = engine.calculate_foreign_contractor_tax(
            foreign_supplier_name="Google Asia Pacific Pte Ltd",
            supplier_etax_code="0109887766",
            service_category="ONLINE_ADVERTISING",
            revenue_usd=50000.0,
            quarter="Q1-2026",
        )
        assert res["ok"] is True
        assert res["declaration_id"].startswith("FCT-")
        assert res["foreign_supplier"]["name"] == "Google Asia Pacific Pte Ltd"
        assert res["financials"]["reporting_quarter"] == "Q1-2026"

        declared_vnd = 50000.0 * VND_PER_USD
        assert res["financials"]["declared_revenue_vnd"] == declared_vnd
        assert res["tax_breakdown_vnd"]["vat_rate_pct"] == 5.0
        assert res["tax_breakdown_vnd"]["cit_rate_pct"] == 5.0
        assert res["tax_breakdown_vnd"]["total_fct_liability_vnd"] == round(declared_vnd * 0.10)
        assert res["tax_breakdown_vnd"]["effective_tax_rate_pct"] == 10.0

    def test_calculate_foreign_contractor_tax_cloud_saas(self, engine: EcommerceEngine) -> None:
        # Cloud SaaS software is VAT exempt (0% VAT, 5% CIT)
        res = engine.calculate_foreign_contractor_tax(
            foreign_supplier_name="Amazon Web Services Inc",
            supplier_etax_code="0108889900",
            service_category="CLOUD_SAAS",
            revenue_vnd=1_000_000_000.0,
            quarter="Q2-2026",
        )
        assert res["ok"] is True
        assert res["tax_breakdown_vnd"]["vat_rate_pct"] == 0.0
        assert res["tax_breakdown_vnd"]["cit_rate_pct"] == 5.0
        assert res["tax_breakdown_vnd"]["vat_amount_vnd"] == 0
        assert res["tax_breakdown_vnd"]["cit_amount_vnd"] == 50_000_000.0
        assert res["tax_breakdown_vnd"]["total_fct_liability_vnd"] == 50_000_000.0

    def test_audit_platform_compliance_approved(self, engine: EcommerceEngine) -> None:
        res = engine.audit_platform_compliance(
            platform_name="Shopee Vietnam",
            domain_url="https://shopee.vn",
            platform_type="MARKETPLACE",
            enterprise_tax_id="0106773786",
            has_operating_regulations=True,
            has_dispute_mechanism=True,
            has_seller_kyc=True,
            has_data_retention_3yr=True,
            has_tax_reporting_system=True,
        )
        assert res["ok"] is True
        assert res["registration_id"].startswith("REG-")
        assert res["compliance_evaluation"]["compliance_score"] == 100.0
        assert res["compliance_evaluation"]["compliance_status"] == "COMPLIANT_APPROVED"
        assert len(res["compliance_evaluation"]["identified_gaps"]) == 0

    def test_audit_platform_compliance_gaps(self, engine: EcommerceEngine) -> None:
        res = engine.audit_platform_compliance(
            platform_name="Unregulated Bazaar",
            domain_url="https://bazaar.local",
            platform_type="MARKETPLACE",
            has_operating_regulations=False,
            has_dispute_mechanism=False,
            has_seller_kyc=False,
            has_data_retention_3yr=False,
            has_tax_reporting_system=False,
        )
        assert res["ok"] is True
        assert res["compliance_evaluation"]["compliance_score"] == 0.0
        assert res["compliance_evaluation"]["compliance_status"] == "NON_COMPLIANT_REJECTED"
        assert len(res["compliance_evaluation"]["identified_gaps"]) == 5

    def test_process_marketplace_order_settlement(self, engine: EcommerceEngine) -> None:
        # GMV = 1,000,000 VND, Commission = 6%, Payment fee = 2.5%, Shipping = 30,000
        # Platform fee = 60,000 VND
        # Payment fee = (1,000,000 + 30,000) * 0.025 = 25,750 VND
        # Seller payout = 1,000,000 - 60,000 - 25,750 = 914,250 VND
        res = engine.process_marketplace_order_settlement(
            order_code="240929-SHOPEE-9988",
            platform_id="SHOPEE_VN",
            seller_id="SHOP-888",
            buyer_id="USER-999",
            gmv_gross_vnd=1000000.0,
            platform_commission_pct=6.0,
            payment_fee_pct=2.5,
            shipping_fee_vnd=30000.0,
            vat_rate_pct=10,
        )
        assert res["ok"] is True
        assert res["order_id"].startswith("ORD-")
        assert res["order_code"] == "240929-SHOPEE-9988"
        f = res["financial_settlement_vnd"]
        assert f["gmv_gross_goods_vnd"] == 1000000.0
        assert f["platform_commission_fee_vnd"] == 60000.0
        assert f["payment_gateway_fee_vnd"] == 25750.0
        assert f["seller_net_payout_vnd"] == 914250.0
        assert f["buyer_total_payment_vnd"] == 1030000.0

        inv = res["electronic_invoice"]
        assert inv["invoice_number"].startswith("INV-")
        assert inv["vat_rate_pct"] == 10
        assert inv["total_invoiced_amount_vnd"] == 1000000.0

    def test_evaluate_cross_border_parcel_exempt(self, engine: EcommerceEngine) -> None:
        # 450,000 VND <= 1,000,000 VND -> Exempt
        res = engine.evaluate_cross_border_parcel(
            tracking_no="SPX12345678",
            shipper_country="China",
            consignee_name="Nguyen Van A",
            item_description="Bluetooth Earphones",
            customs_value_vnd=450000.0,
            import_duty_pct=10.0,
        )
        assert res["ok"] is True
        assert res["parcel_id"].startswith("PCL-")
        assert res["valuation_and_taxation"]["is_tax_exempt"] is True
        assert res["valuation_and_taxation"]["total_tax_payable_vnd"] == 0.0
        assert res["valuation_and_taxation"]["clearance_status"] == "TAX_EXEMPT_CLEARED"

    def test_evaluate_cross_border_parcel_taxable(self, engine: EcommerceEngine) -> None:
        # 3,000,000 VND > 1,000,000 VND -> Taxable
        # Duty 10% = 300,000 VND
        # VAT 10% on (3,000,000 + 300,000) = 330,000 VND
        # Total tax = 630,000 VND
        res = engine.evaluate_cross_border_parcel(
            tracking_no="VN987654321HK",
            shipper_country="Hong Kong",
            consignee_name="Tran Thi B",
            item_description="Smart Watch",
            customs_value_vnd=3000000.0,
            import_duty_pct=10.0,
        )
        assert res["ok"] is True
        assert res["valuation_and_taxation"]["is_tax_exempt"] is False
        assert res["valuation_and_taxation"]["import_duty_vnd"] == 300000.0
        assert res["valuation_and_taxation"]["import_vat_vnd"] == 330000.0
        assert res["valuation_and_taxation"]["total_tax_payable_vnd"] == 630000.0
        assert res["valuation_and_taxation"]["clearance_status"] == "TAXABLE_CLEARANCE_REQUIRED"

    def test_list_records_and_record_list(self, engine: EcommerceEngine) -> None:
        engine.calculate_foreign_contractor_tax("Netflix Inc", "0109991122", "STREAMING_MEDIA", 20000.0)
        engine.audit_platform_compliance("Tiki", "https://tiki.vn", "MARKETPLACE")
        engine.process_marketplace_order_settlement("ORD-1", "TIKI", "S1", "B1", 500000.0)
        engine.evaluate_cross_border_parcel("TRK-1", "Japan", "Le C", "Anime figure", 800000.0)

        platforms = engine.list_platform_registrations(limit=10)
        assert len(platforms) >= 1
        assert platforms["ok"] is True
        assert "platforms" in platforms

        fct = engine.list_fct_declarations(limit=10)
        assert len(fct) >= 1
        assert fct["ok"] is True
        assert "declarations" in fct

        orders = engine.list_marketplace_orders(limit=10)
        assert len(orders) >= 1
        assert orders["ok"] is True
        assert "orders" in orders

        parcels = engine.list_cross_border_parcels(limit=10)
        assert len(parcels) >= 1
        assert parcels["ok"] is True
        assert "parcels" in parcels

    def test_get_status_telemetry(self, engine: EcommerceEngine) -> None:
        engine.calculate_foreign_contractor_tax("Meta Ireland", "0109993344", "ONLINE_ADVERTISING", 10000.0)
        engine.audit_platform_compliance("TikTok Shop", "https://tiktok.com", "SOCIAL_COMMERCE")
        engine.process_marketplace_order_settlement("ORD-2", "TIKTOK", "S2", "B2", 200000.0)

        status = engine.get_status()
        assert status["ok"] is True
        assert status["engine"] == "EcommerceEngine"
        assert status["metrics"]["registered_platforms"] >= 1
        assert status["metrics"]["fct_tax_declarations_count"] >= 1
        assert status["metrics"]["total_marketplace_orders_settled"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestEcommerceCli:
    """Test Typer CLI commands for e-commerce."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_fct_console(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "ecom",
                "fct",
                "Google Asia Pacific",
                "0109887766",
                "ONLINE_ADVERTISING",
                "--usd",
                "10000.0",
                "--quarter",
                "Q1-2026",
            ],
        )
        assert result.exit_code == 0
        assert "Google Asia Pacific" in result.output

    def test_cli_fct_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "ecom",
                "fct",
                "Google Asia Pacific",
                "0109887766",
                "ONLINE_ADVERTISING",
                "--usd",
                "10000.0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["foreign_supplier"]["name"] == "Google Asia Pacific"
        assert data["tax_breakdown_vnd"]["effective_tax_rate_pct"] == 10.0

    def test_cli_audit_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "ecom",
                "audit",
                "Lazada Vietnam",
                "https://lazada.vn",
                "--type",
                "MARKETPLACE",
                "--tax-id",
                "0105999888",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["platform_profile"]["platform_name"] == "Lazada Vietnam"
        assert data["compliance_evaluation"]["compliance_score"] == 100.0

    def test_cli_order_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "ecom",
                "order",
                "ORD-240929-100",
                "LAZADA_VN",
                "SELLER-1",
                "BUYER-1",
                "500000",
                "--commission",
                "5.0",
                "--shipping",
                "25000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["order_code"] == "ORD-240929-100"
        assert data["financial_settlement_vnd"]["seller_net_payout_vnd"] > 0

    def test_cli_parcel_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "ecom",
                "parcel",
                "TRK-9999",
                "Korea",
                "Pham Thi D",
                "Cosmetics Lip Gloss",
                "--vnd",
                "400000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["valuation_and_taxation"]["is_tax_exempt"] is True

    def test_cli_list_json(self) -> None:
        res = runner.invoke(self.app, ["ecom", "list", "--type", "platforms", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "platforms" in data

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["ecom", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestEcommerceMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for e-commerce tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_ecom_fct")
        assert hasattr(server, "_handle_ecom_audit")
        assert hasattr(server, "_handle_ecom_order")
        assert hasattr(server, "_handle_ecom_parcel")
        assert hasattr(server, "_handle_ecom_list")
        assert hasattr(server, "_handle_ecom_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_ecom_fct",
            "mekong_ecom_audit",
            "mekong_ecom_order",
            "mekong_ecom_parcel",
            "mekong_ecom_list",
            "mekong_ecom_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        f_handler = CORE_HANDLERS["mekong_ecom_fct"]
        f_raw = f_handler({
            "foreign_supplier_name": "Meta Ireland Ltd",
            "supplier_etax_code": "0109995544",
            "service_category": "DIGITAL_SERVICES",
            "revenue_usd": 20000.0,
        })
        f_res = json.loads(f_raw)
        assert f_res["ok"] is True
        assert f_res["foreign_supplier"]["name"] == "Meta Ireland Ltd"
        assert f_res["tax_breakdown_vnd"]["effective_tax_rate_pct"] == 10.0

        a_handler = CORE_HANDLERS["mekong_ecom_audit"]
        a_raw = a_handler({
            "platform_name": "Sendo JSC",
            "domain_url": "https://sendo.vn",
            "platform_type": "MARKETPLACE",
            "enterprise_tax_id": "0312345678",
            "has_operating_regulations": True,
            "has_dispute_mechanism": True,
            "has_seller_kyc": True,
            "has_data_retention_3yr": True,
            "has_tax_reporting_system": True,
        })
        a_res = json.loads(a_raw)
        assert a_res["ok"] is True
        assert a_res["compliance_evaluation"]["compliance_status"] == "COMPLIANT_APPROVED"

        p_handler = CORE_HANDLERS["mekong_ecom_parcel"]
        p_raw = p_handler({
            "tracking_no": "VN1122334455HK",
            "shipper_country": "China",
            "consignee_name": "Nguyen Van X",
            "item_description": "Mouse Pad",
            "customs_value_vnd": 250000.0,
        })
        p_res = json.loads(p_raw)
        assert p_res["ok"] is True
        assert p_res["valuation_and_taxation"]["is_tax_exempt"] is True
