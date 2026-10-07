# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Mekong E-Commerce Customs, Specialized Inspection,
Hazardous Chemicals & EU CBAM/EUDR Compliance Suite (Phases 175 - 178).

Covers:
1. AST Boundary & Zero-Dependency Purity (Pure Python Stdlib in src/core/ecom_inspect_engine.py)
2. Phase 175: Cross-Border E-Commerce Customs & Platform Withholding Engine
3. Phase 176: Hazardous Chemicals Import NSW & DG Segregation Engine
4. Phase 177: Specialized Food Safety & Quarantine Inspection Engine
5. Phase 178: EU CBAM Embedded Emissions & EUDR Compliance Engine
6. CLI Commands & Dual-Group Wiring (mekong ecom-customs / tmdt & mekong inspect / kiemtra)
7. FastMCP & JSON-RPC Server Tool Handlers (scripts/mcp_server.py)
"""

from __future__ import annotations

import ast
import json
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.ecom_inspect_engine import (
    CrossBorderEcomEngine,
    EcomPlatform,
    EcomOrderItem,
    HazardousChemicalNSWEngine,
    ChemicalItem,
    ChemicalAnnex,
    IMDGSegregationClass,
    SpecializedInspectionEngine,
    FoodSafetyConsignmentRecord,
    FoodInspectionMethod,
    QuarantineType,
    CBAMEUDRComplianceEngine,
    CBAMEmissionsInput,
    CBAMSector,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_ecom_tax_calculation,
    handle_ecom_split_detection,
    handle_chemical_nsw_eval,
    handle_dg_segregation_check,
    handle_food_safety_inspect_tier,
    handle_cbam_liability_calc,
    handle_eudr_compliance_check,
    CORE_HANDLERS,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestEComInspectBoundary:
    """Verify ecom_inspect_engine is 100% Python Standard Library."""

    def test_pure_standard_library_imports(self) -> None:
        file_rel_path = "src/core/ecom_inspect_engine.py"
        source_path = pathlib.Path(file_rel_path)
        assert source_path.exists(), f"{file_rel_path} must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        allowed_stdlib = {
            "__future__",
            "datetime",
            "typing",
            "dataclasses",
            "enum",
            "math",
            "json",
            "hashlib",
            "uuid",
        }

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        disallowed = imported_modules - allowed_stdlib
        assert not disallowed, f"Disallowed external dependencies in {file_rel_path}: {disallowed}"


# ============================================================================
# 2. Phase 175: Cross-Border E-Commerce Customs & Platform Withholding Engine
# ============================================================================


class TestCrossBorderEcomEngine:
    """Tests for Phase 175: CrossBorderEcomEngine."""

    def test_de_minimis_duty_exemption_under_one_million(self) -> None:
        """Parcel <= 1,000,000 VND is exempt from import duty under Decree 134/2016, but VAT is payable (repeal of Decision 78)."""
        item = EcomOrderItem(
            item_id="ITM-01",
            product_name="Phone Case",
            hs_code="3926.90.99",
            unit_price_vnd=800_000.0,
            quantity=1,
            seller_id="SELLER-CN-01",
            platform=EcomPlatform.SHOPEE,
            direct_seller_discount_vnd=50_000.0,
            import_duty_rate=10.0,
            vat_rate=10.0,
        )
        res = CrossBorderEcomEngine.calculate_customs_tax(
            order_id="ORD-VN-001",
            platform=EcomPlatform.SHOPEE,
            buyer_id="BUYER-001",
            items=[item],
            intl_freight_vnd=50_000.0,
        )
        assert res.customs_value_vnd == 800_000.0  # 800k + 50k freight - 50k seller discount
        assert res.is_de_minimis_duty_free is True
        assert res.import_duty_vnd == 0.0
        assert res.vat_vnd == 80_000.0  # 10% of customs value
        assert res.total_tax_liability_vnd == 80_000.0
        assert res.platform_withholding_payable_vnd == 80_000.0

    def test_parcel_over_one_million_liable_for_both_duty_and_vat(self) -> None:
        """Parcel > 1,000,000 VND pays both import duty and VAT."""
        item = EcomOrderItem(
            item_id="ITM-02",
            product_name="Smart Watch",
            hs_code="8517.62.99",
            unit_price_vnd=2_000_000.0,
            quantity=1,
            seller_id="SELLER-CN-02",
            platform=EcomPlatform.LAZADA,
            import_duty_rate=15.0,
            vat_rate=10.0,
        )
        res = CrossBorderEcomEngine.calculate_customs_tax(
            order_id="ORD-VN-002",
            platform=EcomPlatform.LAZADA,
            buyer_id="BUYER-002",
            items=[item],
        )
        assert res.customs_value_vnd == 2_000_000.0
        assert res.is_de_minimis_duty_free is False
        assert res.import_duty_vnd == 300_000.0  # 15% of 2M
        # VAT base = 2,000,000 + 300,000 = 2,300,000 -> 10% = 230,000
        assert res.vat_vnd == 230_000.0
        assert res.total_tax_liability_vnd == 530_000.0
        assert res.platform_withholding_payable_vnd == 530_000.0

    def test_platform_marketing_voucher_not_deductible(self) -> None:
        """Marketing vouchers by marketplace platforms cannot reduce customs dutiable value."""
        item = EcomOrderItem(
            item_id="ITM-03",
            product_name="Bluetooth Earphones",
            hs_code="8518.30.00",
            unit_price_vnd=1_200_000.0,
            quantity=1,
            seller_id="SELLER-CN-03",
            platform=EcomPlatform.TIKTOK_SHOP,
            direct_seller_discount_vnd=100_000.0,
            platform_subsidy_voucher_vnd=200_000.0,  # non-deductible
            import_duty_rate=10.0,
            vat_rate=10.0,
        )
        res = CrossBorderEcomEngine.calculate_customs_tax(
            order_id="ORD-VN-003",
            platform=EcomPlatform.TIKTOK_SHOP,
            buyer_id="BUYER-003",
            items=[item],
        )
        # Customs value = 1,200,000 - 100,000 = 1,100,000
        assert res.customs_value_vnd == 1_100_000.0
        assert res.platform_voucher_disallowed_vnd == 200_000.0
        assert res.is_de_minimis_duty_free is False

    def test_split_consignment_detection_high_risk(self) -> None:
        """Frequent small orders just below 1M VND threshold trigger split fraud flag."""
        orders = [
            {"customs_value_vnd": 950_000.0, "phone": "0901234567", "address": "123 Nguyen Hue, Q1, HCMC"},
            {"customs_value_vnd": 920_000.0, "phone": "0901234567", "address": "123 Nguyen Hue, Q1, HCMC"},
            {"customs_value_vnd": 980_000.0, "phone": "0901234567", "address": "123 Nguyen Hue, Q1, HCMC"},
            {"customs_value_vnd": 890_000.0, "phone": "0901234567", "address": "123 Nguyen Hue, Q1, HCMC"},
        ]
        res = CrossBorderEcomEngine.evaluate_split_consignment_risk(
            buyer_id="BUYER-SUSPECT-01",
            orders=orders,
            window_hours=48.0,
        )
        assert res.is_split_fraud_detected is True
        assert res.order_count == 4
        assert res.total_aggregate_value_vnd == 3_740_000.0
        assert res.risk_score >= 0.70
        assert res.recommended_channel == "RED"
        assert "consolidat" in res.recommended_action.lower() or "split" in res.recommended_action.lower()

    def test_split_consignment_normal_single_order(self) -> None:
        """Single normal order does not trigger split fraud."""
        orders = [{"customs_value_vnd": 450_000.0}]
        res = CrossBorderEcomEngine.evaluate_split_consignment_risk(
            buyer_id="BUYER-LEGIT-01",
            orders=orders,
            window_hours=72.0,
        )
        assert res.is_split_fraud_detected is False
        assert res.order_count == 1
        assert res.risk_score < 0.40
        assert res.recommended_channel == "GREEN"


# ============================================================================
# 3. Phase 176: Hazardous Chemicals Import NSW & DG Segregation Engine
# ============================================================================


class TestHazardousChemicalNSWEngine:
    """Tests for Phase 176: HazardousChemicalNSWEngine."""

    def test_banned_chemical_annex_iii_rejected(self) -> None:
        """Annex III banned chemical is unconditionally prohibited from importation."""
        chem = ChemicalItem(
            cas_number="57-74-9",  # Chlordane
            chemical_name="Chlordane",
            hs_code="2903.82.00",
            quantity_kg=100.0,
            annexes=[ChemicalAnnex.ANNEX_III_BANNED],
        )
        res = HazardousChemicalNSWEngine.evaluate_chemical_compliance(chem)
        assert res.is_banned is True
        assert res.customs_status == "REJECTED_BANNED"

    def test_restricted_chemical_annex_ii_without_license(self) -> None:
        """Annex II restricted chemical without MOIT license is blocked."""
        chem = ChemicalItem(
            cas_number="7664-93-9",  # Sulfuric Acid
            chemical_name="Sulfuric Acid",
            hs_code="2807.00.00",
            quantity_kg=5_000.0,
            annexes=[ChemicalAnnex.ANNEX_II_RESTRICTED, ChemicalAnnex.ANNEX_V_MANDATORY_NSW],
            moit_license_number="",
        )
        res = HazardousChemicalNSWEngine.evaluate_chemical_compliance(chem)
        assert res.requires_moit_license is True
        assert res.moit_license_valid is False
        assert res.customs_status == "BLOCKED_MISSING_LICENSE"

    def test_restricted_chemical_annex_ii_with_valid_license(self) -> None:
        """Annex II with valid MOIT license and NSW declaration receives clearance token."""
        chem = ChemicalItem(
            cas_number="7664-93-9",
            chemical_name="Sulfuric Acid",
            hs_code="2807.00.00",
            quantity_kg=5_000.0,
            annexes=[ChemicalAnnex.ANNEX_II_RESTRICTED, ChemicalAnnex.ANNEX_V_MANDATORY_NSW],
            moit_license_number="MOIT-LIC-2026-999",
            vnsw_declaration_id="VNSW-DEC-8888",
        )
        res = HazardousChemicalNSWEngine.evaluate_chemical_compliance(chem)
        assert res.requires_moit_license is True
        assert res.moit_license_valid is True
        assert res.customs_status == "CLEARED_ELIGIBLE"
        assert res.nsw_token is not None
        assert res.nsw_token.startswith("VNSW-CLR-")

    def test_accident_plan_threshold_over_50_tonnes(self) -> None:
        """Consignment >= 50 tonnes requires major accident prevention plan."""
        chem = ChemicalItem(
            cas_number="108-88-3",  # Toluene
            chemical_name="Toluene",
            hs_code="2902.30.00",
            quantity_kg=60_000.0,
            annexes=[ChemicalAnnex.ANNEX_I_CONDITIONAL, ChemicalAnnex.ANNEX_IV_PLAN, ChemicalAnnex.ANNEX_V_MANDATORY_NSW],
            vnsw_declaration_id="VNSW-DEC-1234",
        )
        res = HazardousChemicalNSWEngine.evaluate_chemical_compliance(chem)
        assert res.requires_accident_plan is True
        assert "PLAN" in res.accident_document_type

    def test_dg_segregation_class_3_flammable_vs_class_5_1_oxidizing(self) -> None:
        """IMDG Code 41-22 Table 7.2.4: Class 3 and Class 5.1 require SEPARATED_FROM (min 6m)."""
        res = HazardousChemicalNSWEngine.check_dg_segregation(
            un_a="UN1203",
            dg_class_a=3.0,
            un_b="UN1479",
            dg_class_b=5.1,
        )
        assert res.segregation_requirement == IMDGSegregationClass.SEPARATED_FROM
        assert res.is_coloading_permitted is True
        assert res.min_distance_meters == 6.0

    def test_dg_segregation_class_1_explosives_vs_class_3(self) -> None:
        """Class 1 and Class 3 require FORBIDDEN co-loading (min 999m marker)."""
        res = HazardousChemicalNSWEngine.check_dg_segregation(
            un_a="UN0027",
            dg_class_a=1.0,
            un_b="UN1203",
            dg_class_b=3.0,
        )
        assert res.segregation_requirement == IMDGSegregationClass.FORBIDDEN
        assert res.is_coloading_permitted is False
        assert res.min_distance_meters == 999.0


# ============================================================================
# 4. Phase 177: Specialized Food Safety & Quarantine Inspection Engine
# ============================================================================


class TestSpecializedInspectionEngine:
    """Tests for Phase 177: SpecializedInspectionEngine."""

    def test_transition_normal_to_reduced_tier(self) -> None:
        """3 consecutive compliant batches + valid HACCP transitions NORMAL -> REDUCED (<= 5%)."""
        rec = FoodSafetyConsignmentRecord(
            consignor_id="EXPORTER-JP-01",
            product_hs="2106.90.99",
            current_method=FoodInspectionMethod.NORMAL,
            consecutive_passes=3,
            has_iso22000_or_haccp=True,
            cert_valid_days=180,
            failed_last_batch=False,
        )
        res = SpecializedInspectionEngine.evaluate_food_inspection_tier(rec)
        assert res.assigned_method == FoodInspectionMethod.REDUCED
        assert res.sample_inspection_rate_pct == 5.0
        assert res.requires_lab_testing is False
        assert "UPGRADE" in res.transition_reason

    def test_failure_downgrades_immediately_to_tightened_tier(self) -> None:
        """Batch failure triggers immediate downgrade to TIGHTENED (100% lab sampling)."""
        rec = FoodSafetyConsignmentRecord(
            consignor_id="EXPORTER-TH-02",
            product_hs="1602.32.10",
            current_method=FoodInspectionMethod.REDUCED,
            consecutive_passes=0,
            has_iso22000_or_haccp=False,
            cert_valid_days=0,
            failed_last_batch=True,
        )
        res = SpecializedInspectionEngine.evaluate_food_inspection_tier(rec)
        assert res.assigned_method == FoodInspectionMethod.TIGHTENED
        assert res.sample_inspection_rate_pct == 100.0
        assert res.requires_lab_testing is True
        assert "ESCALATION" in res.transition_reason

    def test_tightened_recovers_to_normal_after_three_passes(self) -> None:
        """3 consecutive passes under TIGHTENED upgrades back to NORMAL."""
        rec = FoodSafetyConsignmentRecord(
            consignor_id="EXPORTER-TH-02",
            product_hs="1602.32.10",
            current_method=FoodInspectionMethod.TIGHTENED,
            consecutive_passes=3,
            has_iso22000_or_haccp=False,
            cert_valid_days=0,
            failed_last_batch=False,
        )
        res = SpecializedInspectionEngine.evaluate_food_inspection_tier(rec)
        assert res.assigned_method == FoodInspectionMethod.NORMAL
        assert res.sample_inspection_rate_pct == 0.0
        assert res.requires_lab_testing is False
        assert "DE-ESCALATION" in res.transition_reason

    def test_animal_quarantine_validity_within_15_days(self) -> None:
        """Animal quarantine certificate under Circular 25/2016 is valid within 15 days."""
        res = SpecializedInspectionEngine.verify_quarantine_validity(
            certificate_id="QUAR-VET-001",
            quarantine_type=QuarantineType.ANIMAL_LIVE,
            issue_date_str="2026-04-01",
            inspection_date_str="2026-04-10",  # 9 days
        )
        assert res.is_valid is True
        assert res.elapsed_days == 9
        assert res.max_validity_days == 15
        assert res.remaining_days == 6

    def test_animal_quarantine_expired_over_15_days(self) -> None:
        """Animal quarantine certificate beyond 15 days is expired."""
        res = SpecializedInspectionEngine.verify_quarantine_validity(
            certificate_id="QUAR-VET-002",
            quarantine_type=QuarantineType.ANIMAL_LIVE,
            issue_date_str="2026-04-01",
            inspection_date_str="2026-04-20",  # 19 days
        )
        assert res.is_valid is False
        assert res.elapsed_days == 19
        assert res.max_validity_days == 15
        assert "EXPIRED" in res.action


# ============================================================================
# 5. Phase 178: EU CBAM Embedded Emissions & EUDR Compliance Engine
# ============================================================================


class TestCBAMEUDRComplianceEngine:
    """Tests for Phase 178: CBAMEUDRComplianceEngine."""

    def test_cbam_liability_calculation_iron_and_steel(self) -> None:
        """CBAM specific embedded emissions and net liability adjusted for VN carbon price."""
        inp = CBAMEmissionsInput(
            sector=CBAMSector.IRON_AND_STEEL,
            export_volume_tonnes=500.0,
            total_production_volume_tonnes=1000.0,
            direct_emissions_scope1_tco2e=1500.0,
            electricity_consumed_mwh=400.0,
            grid_emission_factor_tco2_mwh=0.722,  # 288.8 tCO2e
            eu_ets_allowance_price_eur=75.0,
            vn_carbon_effective_price_eur=10.0,
        )
        res = CBAMEUDRComplianceEngine.calculate_cbam_liability(inp)
        # Total emissions = 1500 + 288.8 = 1788.8 tCO2e
        # Specific emissions = 1788.8 / 1000 = 1.7888 tCO2e/tonne
        assert pytest.approx(res.specific_embedded_emissions_per_tonne, 0.001) == 1.7888
        # Export embedded emissions = 1.7888 * 500 = 894.4 tCO2e
        assert pytest.approx(res.total_embedded_emissions_tco2e, 0.01) == 894.4
        # Spread = 75 - 10 = 65 EUR
        assert res.net_carbon_price_spread_eur == 65.0
        # Liability = 894.4 * 65 = 58,136 EUR
        assert pytest.approx(res.total_cbam_liability_eur, 1.0) == 58_136.0

    def test_eudr_compliant_closed_polygon_over_4_ha(self) -> None:
        """Plot >= 4 ha requires closed GPS polygon (first == last vertex)."""
        coords = [
            (11.5501, 107.1201),
            (11.5501, 107.1501),
            (11.5801, 107.1501),
            (11.5801, 107.1201),
            (11.5501, 107.1201),  # closed
        ]
        res = CBAMEUDRComplianceEngine.verify_eudr_compliance(
            plot_id="PLOT-RUBBER-01",
            commodity_hs="4001.22.00",  # Natural rubber
            area_hectares=6.5,
            coordinates=coords,
            deforestation_free_post_2020=True,
            legal_land_title_certified=True,
        )
        assert res.is_compliant is True
        assert res.validation_status == "EUDR_COMPLIANT_CLEARED"
        assert len(res.rejection_reasons) == 0
        assert res.deforestation_free_post_2020 is True
        assert res.legal_land_title_certified is True

    def test_eudr_unclosed_polygon_rejected(self) -> None:
        """Plot >= 4 ha with unclosed polygon fails compliance."""
        coords = [
            (11.5501, 107.1201),
            (11.5501, 107.1501),
            (11.5801, 107.1501),
            (11.5801, 107.1201),
        ]  # not closed
        res = CBAMEUDRComplianceEngine.verify_eudr_compliance(
            plot_id="PLOT-COFFEE-02",
            commodity_hs="0901.11.00",
            area_hectares=5.0,
            coordinates=coords,
            deforestation_free_post_2020=True,
            legal_land_title_certified=True,
        )
        assert res.is_compliant is False
        assert res.validation_status == "EUDR_REJECTED_NON_CONFORMING"


# ============================================================================
# 6. CLI Commands & Dual-Group Wiring Tests
# ============================================================================


class TestEComInspectCLI:
    """Verify Typer CLI registration and execution."""

    def test_registered_command_groups_in_app(self) -> None:
        app = build_app()
        group_names = [g.name for g in app.registered_groups]
        assert "ecom-customs" in group_names
        assert "tmdt" in group_names
        assert "inspect" in group_names
        assert "kiemtra" in group_names

    def test_cli_ecom_tax_calculation_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["ecom-customs", "tax", "ORD-CLI-01", "850000", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_de_minimis_duty_free"] is True
        assert data["vat_vnd"] == 85_000.0

    def test_cli_ecom_split_check_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["ecom-customs", "split-check", "BUYER-01", "--values", "950000,920000,980000,910000", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_split_fraud_detected"] is True
        assert data["recommended_channel"] == "RED"

    def test_cli_inspect_chemical_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "chemical", "7664-93-9", "500", "--license", "BCT-1234", "--vnsw", "VNSW-555", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["customs_status"] == "CLEARED_ELIGIBLE"
        assert data["nsw_token"] is not None

    def test_cli_inspect_dg_segregation_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "dg-segregation", "UN1203", "3", "UN1479", "5.1", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_coloading_permitted"] is True
        assert data["min_distance_meters"] == 6.0

    def test_cli_inspect_food_tier_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "food-tier", "JP-FOOD-01", "--current", "NORMAL", "--passes", "3", "--haccp", "--cert-days", "200", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["assigned_method"] == "REDUCED"
        assert data["sample_inspection_rate_pct"] == 5.0

    def test_cli_inspect_quarantine_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "quarantine", "QUAR-VET-01", "ANIMAL_LIVE", "2026-04-01", "2026-04-10", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_valid"] is True

    def test_cli_inspect_cbam_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "cbam", "IRON_AND_STEEL", "100", "100", "180", "50", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_cbam_liability_eur"] > 0

    def test_cli_inspect_eudr_json(self) -> None:
        app = build_app()
        result = runner.invoke(
            app,
            ["inspect", "eudr", "PLOT-01", "4001.22.00", "5.0", "--coords", "11.5,107.1;11.5,107.2;11.6,107.2;11.6,107.1;11.5,107.1", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["is_compliant"] is True

    def test_cli_alias_groups(self) -> None:
        """Verify Vietnamese aliases 'tmdt' and 'kiemtra' function properly."""
        app = build_app()
        res_tmdt = runner.invoke(app, ["tmdt", "--help"])
        assert res_tmdt.exit_code == 0
        assert "tax" in res_tmdt.output

        res_kt = runner.invoke(app, ["kiemtra", "--help"])
        assert res_kt.exit_code == 0
        assert "chemical" in res_kt.output


# ============================================================================
# 7. FastMCP & JSON-RPC Server Tool Handlers Tests
# ============================================================================


class TestEComInspectMCPHandlers:
    """Verify tool handlers registered in scripts/mcp_server.py."""

    def test_mcp_ecom_tax_calculation_handler(self) -> None:
        raw = handle_ecom_tax_calculation({"order_id": "ORD-MCP-01", "item_price_vnd": 900_000.0})
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["is_de_minimis_duty_free"] is True
        assert res["vat_vnd"] == 90_000.0

    def test_mcp_ecom_split_detection_handler(self) -> None:
        raw = handle_ecom_split_detection({
            "buyer_id": "BUYER-MCP-01",
            "order_values_vnd": [960_000.0, 940_000.0, 980_000.0, 910_000.0],
            "recipient_phone": "0901234567",
            "recipient_address": "123 Nguyen Hue",
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["is_split_fraud_detected"] is True

    def test_mcp_chemical_nsw_eval_handler(self) -> None:
        raw = handle_chemical_nsw_eval({
            "cas_number": "7664-93-9",
            "quantity_kg": 500.0,
            "import_license_no": "LIC-999",
            "vnsw_declaration_id": "VNSW-111",
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["customs_status"] == "CLEARED_ELIGIBLE"

    def test_mcp_dg_segregation_check_handler(self) -> None:
        raw = handle_dg_segregation_check({
            "un_a": "UN1203",
            "dg_class_a": 3.0,
            "un_b": "UN1479",
            "dg_class_b": 5.1,
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["is_coloading_permitted"] is True
        assert res["min_distance_meters"] == 6.0

    def test_mcp_food_safety_inspect_tier_handler(self) -> None:
        raw = handle_food_safety_inspect_tier({
            "consignor_id": "FOOD-MCP-01",
            "current_method": "NORMAL",
            "consecutive_passes": 3,
            "has_iso22000_or_haccp": True,
            "cert_valid_days": 100,
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["assigned_method"] == "REDUCED"

    def test_mcp_cbam_liability_calc_handler(self) -> None:
        raw = handle_cbam_liability_calc({
            "sector": "IRON_AND_STEEL",
            "export_volume_tonnes": 100.0,
            "total_production_volume_tonnes": 100.0,
            "direct_emissions_scope1_tco2e": 180.0,
            "electricity_consumed_mwh": 50.0,
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["total_cbam_liability_eur"] > 0

    def test_mcp_eudr_compliance_check_handler(self) -> None:
        raw = handle_eudr_compliance_check({
            "plot_id": "PLOT-MCP-01",
            "commodity_hs": "0901.11.00",
            "area_hectares": 5.0,
            "coordinates": [[11.5, 107.1], [11.5, 107.2], [11.6, 107.2], [11.6, 107.1], [11.5, 107.1]],
            "deforestation_free_post_2020": True,
            "legal_land_title_certified": True,
        })
        res = json.loads(raw)
        assert res["ok"] is True
        assert res["is_compliant"] is True

    def test_mcp_core_handlers_dispatch(self) -> None:
        """Verify all 7 tools are wired in CORE_HANDLERS under both prefixed and short names."""
        tools = [
            "ecom_tax_calculation",
            "ecom_split_detection",
            "chemical_nsw_eval",
            "dg_segregation_check",
            "food_safety_inspect_tier",
            "cbam_liability_calc",
            "eudr_compliance_check",
        ]
        for t in tools:
            assert t in CORE_HANDLERS, f"{t} must be in CORE_HANDLERS"
            assert f"mekong_{t}" in CORE_HANDLERS, f"mekong_{t} must be in CORE_HANDLERS"
