# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Comprehensive Tests for Vietnam Seaport Terminal Operations, Port Tariffs,
DEM/DET Maritime Lien, SOLAS VGM, Trade Finance L/C (UCP 600 / ISBP 745),
Pharma Cold Chain GDP MKT & ISO 14083 Freight Carbon Accounting Suite (Phases 179 - 182).

Covers:
1. AST Boundary & Zero-Dependency Purity (Pure Python Stdlib in src/core/port_supply_chain_engine.py)
2. Phase 179: Seaport Terminal Ops (TT 39/2023), Sliding Scale DEM/DET & Maritime Lien (Art 168 BLLHH), SOLAS VGM
3. Phase 180: Trade Finance Documentary L/C (UCP 600 / ISBP 745) & Usance Discounting
4. Phase 181: Pharma Cold Chain GDP, Arrhenius Mean Kinetic Temperature (MKT) & Excursion Quarantine
5. Phase 182: Multimodal Freight Carbon Accounting (ISO 14083:2023 / GLEC v3.0) & Modal Shift Decarbonization
6. CLI Commands & Dual-Group Wiring (mekong port / cangbien & mekong tradefinance / scf)
7. FastMCP & JSON-RPC Tool Handlers in scripts/mcp_server.py
"""

from __future__ import annotations

import ast
import json
import math
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.port_supply_chain_engine import (
    SeaportTerminalOpsEngine,
    PortArea,
    ContainerType,
    CargoStatus,
    DEMDETStage,
    PortHandlingTariffResult,
    DEMDETCalculationResult,
    SOLASVGMResult,
    TradeFinanceLCEngine,
    LCExaminationResult,
    LCDiscountProceedsResult,
    ColdChainPharmaGDPEngine,
    PharmaStorageClass,
    QualityDisposition,
    TemperatureExcursionEvent,
    MKTCalculationResult,
    ColdChainIntegrityAssessment,
    FreightCarbonAccountingEngine,
    FreightTransportMode,
    MultimodalRouteCarbonResult,
    ModalShiftOptimizationResult,
)
from src.cli.app_setup import build_app
from scripts.mcp_server import (
    handle_port_tariff_calc,
    handle_dem_det_calc,
    handle_solas_vgm_verify,
    handle_lc_ucp600_examine,
    handle_lc_usance_discount,
    handle_pharma_mkt_eval,
    handle_pharma_coldchain_assess,
    handle_freight_carbon_calc,
    handle_modal_shift_eval,
    CORE_HANDLERS,
)

runner = CliRunner()


# ============================================================================
# 1. AST Boundary & Zero-Dependency Purity Tests
# ============================================================================


class TestPortSupplyChainBoundary:
    """Verify port_supply_chain_engine is 100% Python Standard Library."""

    def test_pure_standard_library_imports(self) -> None:
        file_rel_path = "src/core/port_supply_chain_engine.py"
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
        }

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        prohibited = imported_modules - allowed_stdlib
        assert not prohibited, f"Prohibited non-stdlib imports found: {prohibited}"


# ============================================================================
# 2. Phase 179: Seaport Terminal Ops, DEM/DET & SOLAS VGM Tests
# ============================================================================


class TestSeaportTerminalOpsEngine:
    """Verify TT 39/2023 tariffs, DEM/DET sliding scales, and SOLAS VGM rules."""

    def test_port_tariff_dry_20ft_area_iii_laden(self) -> None:
        res = SeaportTerminalOpsEngine.calculate_port_tariff(
            port_area=PortArea.AREA_III_SOUTH,
            container_type=ContainerType.DRY_20FT,
            cargo_status=CargoStatus.LADEN,
            reefer_plug_hours=0.0,
            is_imo_dangerous=False,
            is_oog=False,
        )
        assert isinstance(res, PortHandlingTariffResult)
        assert res.base_thc_vnd == 1_320_000.0
        assert res.reefer_power_vnd == 0.0
        assert res.surcharge_vnd == 0.0
        assert res.total_port_charge_vnd == 1_320_000.0
        assert "Circular 39/2023/TT-BGTVT" in res.legal_basis

    def test_port_tariff_reefer_40ft_surcharges(self) -> None:
        # Area I North Reefer 40ft: Base 2,750,000 VND
        # Reefer 24h plug-in @ 85,000 VND/h = 2,040,000 VND
        # IMO dangerous +50% = 1,375,000 VND
        # Total: 2,750,000 + 2,040,000 + 1,375,000 = 6,165,000 VND
        res = SeaportTerminalOpsEngine.calculate_port_tariff(
            port_area=PortArea.AREA_I_NORTH,
            container_type=ContainerType.REEFER_40FT,
            cargo_status=CargoStatus.LADEN,
            reefer_plug_hours=24.0,
            is_imo_dangerous=True,
            is_oog=False,
        )
        assert res.base_thc_vnd == 2_750_000.0
        assert res.reefer_power_vnd == 2_040_000.0
        assert res.surcharge_vnd == 1_375_000.0
        assert res.total_port_charge_vnd == 6_165_000.0

    def test_dem_det_free_period(self) -> None:
        res = SeaportTerminalOpsEngine.calculate_dem_det(
            container_id="C20_FREE",
            container_type=ContainerType.DRY_20FT,
            days_incurred=4,
            free_days_allowed=5,
        )
        assert isinstance(res, DEMDETCalculationResult)
        assert res.overdue_days == 0
        assert res.stage == DEMDETStage.WITHIN_FREE_TIME
        assert res.total_penalty_usd == 0.0
        assert not res.carrier_lien_warning

    def test_dem_det_tiered_escalation(self) -> None:
        # 40ft: t1=60, t2=100, t3=160. 18 days incurred with 5 free days -> 13 overdue days.
        # Tier 1 (days 1-5 = 5 days): 5 * 60 = 300
        # Tier 2 (days 6-10 = 5 days): 5 * 100 = 500
        # Tier 3 (days 11-13 = 3 days): 3 * 160 = 480
        # Total = 300 + 500 + 480 = $1,280
        res = SeaportTerminalOpsEngine.calculate_dem_det(
            container_id="C40_TIERED",
            container_type=ContainerType.DRY_40FT,
            days_incurred=18,
            free_days_allowed=5,
            cargo_cif_value_usd=10000.0,
        )
        assert res.overdue_days == 13
        assert res.stage == DEMDETStage.TIER_3_CRITICAL
        assert res.total_penalty_usd == 1280.0
        assert math.isclose(res.total_penalty_vnd, 1280.0 * 25450.0)

    def test_dem_det_carrier_lien_triggered(self) -> None:
        # Overdue days > 25 triggers Art 168 Maritime Lien warning
        res = SeaportTerminalOpsEngine.calculate_dem_det(
            container_id="C40_LIEN",
            container_type=ContainerType.DRY_40FT,
            days_incurred=32,
            free_days_allowed=5,  # 27 overdue days
            cargo_cif_value_usd=50000.0,
        )
        assert res.carrier_lien_warning is True
        assert "exceeds 25 days" in res.lien_rationale

    def test_solas_vgm_compliant(self) -> None:
        # 20,000 kg declared, 20,200 kg scale. Variance = 200 kg (1.0%).
        # Max allowable = min(20000 * 0.05, 500) = 500 kg. 200 <= 500 -> Compliant
        res = SeaportTerminalOpsEngine.verify_solas_vgm(
            container_id="MSKU1029384",
            declared_vgm_kg=20000.0,
            verified_scale_kg=20200.0,
        )
        assert isinstance(res, SOLASVGMResult)
        assert res.is_compliant is True
        assert res.variance_kg == 200.0
        assert res.gate_in_status == "ACCEPTED_FOR_LOADING"
        assert res.penalty_estimate_vnd == 0.0

    def test_solas_vgm_rejected_no_load(self) -> None:
        # 20,000 kg declared, 20,800 kg scale. Variance = 800 kg > 500 kg -> Non-compliant
        res = SeaportTerminalOpsEngine.verify_solas_vgm(
            container_id="MSKU9999999",
            declared_vgm_kg=20000.0,
            verified_scale_kg=20800.0,
        )
        assert res.is_compliant is False
        assert res.variance_kg == 800.0
        assert res.gate_in_status == "GATE_IN_BLOCKED_OVERWEIGHT"
        assert res.penalty_estimate_vnd > 0.0
        assert "exceeds allowable tolerance" in res.rejection_reason


# ============================================================================
# 3. Phase 180: Trade Finance, UCP 600 & Usance Discounting Tests
# ============================================================================


class TestTradeFinanceLCEngine:
    """Verify UCP 600 examination rules, discrepancy detector, and usance math."""

    def test_lc_examination_clean_presentation(self) -> None:
        res = TradeFinanceLCEngine.examine_presentation(
            lc_reference="LC-2026-VCB-001",
            presentation_date_iso="2026-10-05",
            latest_shipment_date_iso="2026-10-01",
            expiry_date_iso="2026-10-25",
            bl_onboard_date_iso="2026-09-28",
            invoice_amount_usd=100000.0,
            lc_credit_amount_usd=100000.0,
            is_goods_description_exact_match=True,
            presentation_period_days=21,
        )
        assert isinstance(res, LCExaminationResult)
        assert res.is_clean is True
        assert len(res.discrepancies) == 0
        assert res.discrepancy_fee_usd == 0.0
        assert res.action_required == "PROCEED_WITH_HONOR"

    def test_lc_examination_multiple_discrepancies(self) -> None:
        # Late shipment (onboard Oct 10 > latest Oct 5)
        # Stale B/L (presentation Oct 20 > Oct 10 + 7 days period = Oct 17)
        # Invoice mismatch
        # Overdrawn (125,000 > 100,000 + 5% tol = 105,000)
        res = TradeFinanceLCEngine.examine_presentation(
            lc_reference="LC-2026-BIDV-999",
            presentation_date_iso="2026-10-20",
            latest_shipment_date_iso="2026-10-05",
            expiry_date_iso="2026-10-25",
            bl_onboard_date_iso="2026-10-10",
            invoice_amount_usd=125000.0,
            lc_credit_amount_usd=100000.0,
            is_goods_description_exact_match=False,
            presentation_period_days=7,
            credit_tolerance_pct=5.0,
        )
        assert res.is_clean is False
        assert len(res.discrepancies) == 4
        titles = [d.discrepancy_title for d in res.discrepancies]
        assert "Late Shipment" in titles
        assert "Stale Bill of Lading" in titles
        assert "Invoice Goods Description Mismatch" in titles
        assert "Credit Amount Overdrawn" in titles
        assert res.discrepancy_fee_usd == 85.0

    def test_usance_discount_calculation(self) -> None:
        # Draft: $200,000, 90 days tenor, SOFR 5.25% + spread 1.75% = 7.0% per annum
        # Discount charge = 200,000 * 0.07 * (90 / 360) = 200,000 * 0.07 * 0.25 = $3,500
        # Discrepancy fee = $85
        # Net proceeds = 200,000 - 3,500 - 85 = $196,415
        res = TradeFinanceLCEngine.calculate_usance_discount(
            lc_reference="LC-DISC-01",
            draft_amount_usd=200000.0,
            tenor_days=90,
            benchmark_rate_pct=5.25,
            spread_margin_pct=1.75,
            discrepancy_fee_usd=85.0,
            fx_rate_usd_vnd=25450.0,
        )
        assert isinstance(res, LCDiscountProceedsResult)
        assert res.all_in_discount_rate_pct == 7.0
        assert math.isclose(res.discount_charge_usd, 3500.0)
        assert math.isclose(res.net_proceeds_usd, 196415.0)
        assert math.isclose(res.net_proceeds_vnd, 196415.0 * 25450.0)


# ============================================================================
# 4. Phase 181: Pharma Cold Chain GDP, Arrhenius MKT & Excursions Tests
# ============================================================================


class TestColdChainPharmaGDPEngine:
    """Verify Arrhenius MKT calculation, temperature profiles, and excursion handling."""

    def test_mkt_arrhenius_steady_temperature(self) -> None:
        # 10 readings of constant 5.0 °C
        readings = [5.0] * 10
        res = ColdChainPharmaGDPEngine.calculate_mkt(
            batch_id="VAC-COVID-01",
            temperatures_celsius=readings,
            storage_class=PharmaStorageClass.COLD_CHAIN,
        )
        assert isinstance(res, MKTCalculationResult)
        assert math.isclose(res.mkt_celsius, 5.0, rel_tol=1e-3)
        assert res.is_mkt_within_spec is True
        assert res.disposition == QualityDisposition.RELEASE

    def test_mkt_arrhenius_temperature_excursion_non_compliant(self) -> None:
        # Cold chain requires 2.0 to 8.0 °C. Readings spike to 18-20 °C.
        readings = [4.0, 5.0, 15.0, 18.0, 20.0, 16.0]
        res = ColdChainPharmaGDPEngine.calculate_mkt(
            batch_id="INSULIN-99",
            temperatures_celsius=readings,
            storage_class=PharmaStorageClass.COLD_CHAIN,
        )
        assert res.mkt_celsius > 8.0
        assert res.is_mkt_within_spec is False
        assert res.disposition == QualityDisposition.QUALITY_INVESTIGATION_REQUIRED

    def test_coldchain_excursions_freeze_critical_quarantine(self) -> None:
        # Freezing event (0.0 or below) in Cold Chain (+2 to +8) causes mandatory quarantine
        events = [
            TemperatureExcursionEvent(
                start_time_iso="2026-10-06T08:00:00Z",
                duration_hours=2.0,
                peak_temp_c=-1.5,
                delta_over_limit_c=3.5,
            )
        ]
        res = ColdChainPharmaGDPEngine.assess_cold_chain_excursions(
            shipment_id="BIO-SHP-001",
            storage_class=PharmaStorageClass.COLD_CHAIN,
            total_transit_hours=36.0,
            excursion_events=events,
        )
        assert isinstance(res, ColdChainIntegrityAssessment)
        assert res.freeze_violation is True
        assert res.disposition == QualityDisposition.MANDATORY_QUARANTINE_HOLD
        assert "CRITICAL FREEZE BREACH" in res.quarantine_hold_rationale

    def test_coldchain_excursions_minor_investigation(self) -> None:
        # Minor excursion: 8.5 °C (0.5 °C above 8.0) for 1 hour
        events = [
            TemperatureExcursionEvent(
                start_time_iso="2026-10-06T10:00:00Z",
                duration_hours=1.0,
                peak_temp_c=8.5,
                delta_over_limit_c=0.5,
            )
        ]
        res = ColdChainPharmaGDPEngine.assess_cold_chain_excursions(
            shipment_id="BIO-SHP-002",
            storage_class=PharmaStorageClass.COLD_CHAIN,
            total_transit_hours=48.0,
            excursion_events=events,
        )
        assert res.disposition == QualityDisposition.QUALITY_INVESTIGATION_REQUIRED
        assert "MINOR EXCURSION DETECTED" in res.quarantine_hold_rationale


# ============================================================================
# 5. Phase 182: Multimodal Freight Carbon & Modal Shift Tests
# ============================================================================


class TestFreightCarbonAccountingEngine:
    """Verify ISO 14083 carbon accounting and Scope 3 modal shift evaluation."""

    def test_multimodal_emissions_calculation(self) -> None:
        # 50 tonnes cargo:
        # Leg 1: Road trucking Euro 4, 30 km -> factor 82.0 g/tkm -> 50 * 30 * 82 = 123,000 g = 123 kg
        # Leg 2: Feeder ship, 200 km -> factor 28.0 g/tkm -> 50 * 200 * 28 = 280,000 g = 280 kg
        # Total emissions = 123 + 280 = 403 kg CO2e = 0.403 tonnes
        legs = [
            ("Port Drayage", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, 30.0),
            ("Domestic Feeder", FreightTransportMode.FEEDER_VESSEL, 200.0),
        ]
        res = FreightCarbonAccountingEngine.calculate_multimodal_emissions(
            route_id="RT-SGN-HPH",
            cargo_weight_tonnes=50.0,
            legs_data=legs,
            carbon_price_per_tonne_vnd=125000.0,
        )
        assert isinstance(res, MultimodalRouteCarbonResult)
        assert res.total_cargo_weight_tonnes == 50.0
        assert res.total_distance_km == 230.0
        assert math.isclose(res.total_emissions_kg_co2e, 403.0, abs_tol=1e-2)
        assert math.isclose(res.total_emissions_t_co2e, 0.403, abs_tol=1e-4)
        assert res.offset_cost_vnd == 0.403 * 125000.0

    def test_modal_shift_evaluation(self) -> None:
        # 100 tonnes cargo, 52 trips/year:
        # Road baseline: 100 km @ 82.0 g/tkm = 8,200 kg = 8.2 tonnes/trip -> 426.4 t/yr
        # Intermodal: 15 km Road (15 * 100 * 82 / 1000 = 123 kg) + 85 km Barge (85 * 100 * 24 / 1000 = 204 kg) = 327 kg = 0.327 t
        # Savings = 8.2 - 0.327 = 7.873 tonnes/trip
        intermodal_legs = [
            ("Drayage truck", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, 15.0),
            ("Inland barge", FreightTransportMode.INLAND_WATERWAY_BARGE, 85.0),
        ]
        res = FreightCarbonAccountingEngine.evaluate_modal_shift(
            origin="Bình Dương ICD",
            destination="Cái Mép Seaport",
            cargo_weight_tonnes=100.0,
            road_distance_km=100.0,
            intermodal_legs=intermodal_legs,
            annual_trips=52,
            carbon_price_vnd=125000.0,
        )
        assert isinstance(res, ModalShiftOptimizationResult)
        assert res.emissions_saved_t_co2e > 0
        assert res.reduction_percentage > 50.0  # Big decarbonization gain (~60.1%)
        assert res.annual_cost_savings_offset_vnd > 0


# ============================================================================
# 6. Typer CLI Commands & Dual-Group Wiring Tests
# ============================================================================


class TestPortSupplyChainCLICommands:
    """Verify CLI commands on both groups: mekong port/cangbien and mekong tradefinance/scf."""

    @pytest.fixture(scope="class")
    def app(self):
        return build_app()

    def test_cli_port_tariff_json(self, app) -> None:
        result = runner.invoke(
            app,
            ["port", "tariff", "--area", "AREA_III_SOUTH", "--container", "DRY_40FT", "--json"],
        )
        assert result.exit_code == 0
        # Check against the actual engine output format
        data = json.loads(result.output)
        assert data["container_type"] == "DRY_40FT"
        assert data["base_thc_vnd"] > 0

    def test_cli_cangbien_alias_tariff(self, app) -> None:
        result = runner.invoke(app, ["cangbien", "tariff", "--area", "AREA_I_NORTH"])
        assert result.exit_code == 0
        assert "BIỂU PHÍ" in result.output

    def test_cli_port_dem_det(self, app) -> None:
        result = runner.invoke(
            app,
            ["port", "dem-det", "--id", "TCLU999", "--days", "12", "--free-days", "5"],
        )
        assert result.exit_code == 0
        assert "QUẢN TRỊ DEM/DET" in result.output

    def test_cli_port_vgm_compliant(self, app) -> None:
        result = runner.invoke(
            app,
            ["port", "vgm", "--id", "MSKU001", "--declared", "24000", "--measured", "24200"],
        )
        assert result.exit_code == 0
        assert "HỢP LỆ" in result.output

    def test_cli_tradefinance_lc_exam(self, app) -> None:
        result = runner.invoke(
            app,
            ["tradefinance", "lc-exam", "--ref", "LC-TEST-01", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["lc_reference"] == "LC-TEST-01"
        assert "is_clean" in data

    def test_cli_scf_alias_discount(self, app) -> None:
        result = runner.invoke(
            app,
            ["scf", "lc-discount", "--ref", "LC-TEST-02", "--draft", "100000", "--tenor", "90"],
        )
        assert result.exit_code == 0
        assert "CHIẾT KHẤU" in result.output

    def test_cli_tradefinance_mkt(self, app) -> None:
        result = runner.invoke(
            app,
            ["tradefinance", "mkt", "--batch", "BATCH-X", "--temps", "4.0,4.5,5.0,5.5,6.0"],
        )
        assert result.exit_code == 0
        assert "Nhiệt độ Động học" in result.output

    def test_cli_tradefinance_carbon(self, app) -> None:
        result = runner.invoke(
            app,
            ["tradefinance", "carbon", "--route", "RT-TEST", "--weight", "25", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_cargo_weight_tonnes"] == 25.0
        assert "total_emissions_kg_co2e" in data


# ============================================================================
# 7. FastMCP & JSON-RPC Tool Handlers Tests
# ============================================================================


class TestPortSupplyChainMCPHandlers:
    """Verify FastMCP handlers and dispatch table integration in scripts/mcp_server.py."""

    def test_mcp_port_tariff_calc(self) -> None:
        # Note: server handler returns JSON string formatted in the handler
        raw = handle_port_tariff_calc({"port_area": "AREA_III_SOUTH", "container_type": "DRY_40FT"})
        # Handler often returns the JSON result directly
        data = json.loads(raw)
        assert data["base_thc_vnd"] > 0

    def test_mcp_dem_det_calc(self) -> None:
        raw = handle_dem_det_calc({"container_id": "TEST_C", "days_incurred": 14, "free_days_allowed": 5})
        data = json.loads(raw)
        assert data["overdue_days"] == 9
        assert data["total_penalty_usd"] > 0

    def test_mcp_solas_vgm_verify(self) -> None:
        raw = handle_solas_vgm_verify({"container_id": "TEST_VGM", "declared_vgm_kg": 20000, "verified_scale_kg": 20200})
        data = json.loads(raw)
        assert data["is_compliant"] is True

    def test_mcp_lc_ucp600_examine(self) -> None:
        raw = handle_lc_ucp600_examine({"lc_reference": "LC-MCP-01"})
        data = json.loads(raw)
        assert data["lc_reference"] == "LC-MCP-01"

    def test_mcp_lc_usance_discount(self) -> None:
        raw = handle_lc_usance_discount({"lc_reference": "LC-MCP-02", "draft_amount_usd": 150000, "tenor_days": 60})
        data = json.loads(raw)
        assert data["net_proceeds_usd"] > 0

    def test_mcp_pharma_mkt_eval(self) -> None:
        raw = handle_pharma_mkt_eval({"batch_id": "BATCH-MCP", "temperatures_celsius": [3.5, 4.2, 5.1, 4.8]})
        data = json.loads(raw)
        assert data["mkt_celsius"] > 0

    def test_mcp_pharma_coldchain_assess(self) -> None:
        raw = handle_pharma_coldchain_assess({"shipment_id": "SHP-MCP"})
        data = json.loads(raw)
        assert "disposition" in data

    def test_mcp_freight_carbon_calc(self) -> None:
        raw = handle_freight_carbon_calc({
            "route_id": "RT-MCP",
            "cargo_weight_tonnes": 30.0,
            "legs": [{"leg_name": "Test Leg", "mode": "INLAND_WATERWAY_BARGE", "distance_km": 120.0}],
        })
        data = json.loads(raw)
        assert data["total_emissions_kg_co2e"] > 0

    def test_mcp_modal_shift_eval(self) -> None:
        raw = handle_modal_shift_eval({"origin": "Hà Nội", "destination": "Hải Phòng"})
        data = json.loads(raw)
        assert data["reduction_percentage"] > 0

    def test_core_handlers_dispatch_keys(self) -> None:
        expected_keys = [
            "mekong_port_tariff_calc",
            "port_tariff_calc",
            "mekong_dem_det_calc",
            "dem_det_calc",
            "mekong_solas_vgm_verify",
            "solas_vgm_verify",
            "mekong_lc_ucp600_examine",
            "lc_ucp600_examine",
            "mekong_lc_usance_discount",
            "lc_usance_discount",
            "mekong_pharma_mkt_eval",
            "pharma_mkt_eval",
            "mekong_pharma_coldchain_assess",
            "pharma_coldchain_assess",
            "mekong_freight_carbon_calc",
            "freight_carbon_calc",
            "mekong_modal_shift_eval",
            "modal_shift_eval",
        ]
        for key in expected_keys:
            assert key in CORE_HANDLERS, f"Key {key} missing from CORE_HANDLERS"
            assert callable(CORE_HANDLERS[key]), f"Handler for {key} is not callable"
