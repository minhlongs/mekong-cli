"""
Unit & Integration Test Suite for Phases 271-274 Maritime Compliance & Operations Suite.
Covers:
- Phase 271: Maritime Collision Investigation, Marine Accident Formal Inquiry & Casualty Board (Circular 34/2015, VMC 2015)
- Phase 272: Electronic Certificate of Origin (e-C/O) & Preferential Rules of Origin (ROO) (Decree 31/2018, EVFTA/CPTPP)
- Phase 273: Seaport Tugboat Towage Tariffs & Assisted Berthing Service Charges (Circular 39/2023 Section III)
- Phase 274: SOLAS Verified Gross Mass (VGM) Container Weighing & Tolerance Verification (SOLAS Reg. VI/2, MSC.1/Circ.1475)
"""

import ast
import json
import pytest
from typer.testing import CliRunner

from src.core.maritime_casualty_co_tug_vgm_engine import (
    MarineCasualtyInquiryEngine,
    MarineCasualtyData,
    CasualtyType,
    CasualtySeverity,
    ElectronicCOEngine,
    ProductOriginInput,
    TradeAgreement,
    OriginCriterion,
    SeaportTugTariffEngine,
    TugboatJobData,
    TugVoyageType,
    TugMaritimeZone,
    SolasVgmEngine,
    ContainerVgmInput,
    VgmStatus,
)
from src.cli.app_setup import build_app
import scripts.mcp_server as mcp_server


# ============================================================================
# 1. Zero External Dependencies Verification (AST Analysis)
# ============================================================================

def test_core_engine_zero_dependencies():
    """Verify core engine imports only Python standard library."""
    engine_path = "src/core/maritime_casualty_co_tug_vgm_engine.py"
    with open(engine_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=engine_path)

    std_lib_modules = {
        "dataclasses", "datetime", "enum", "math", "typing", "json", "sys", "os"
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                assert root_module in std_lib_modules, f"Non-standard import found: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                assert root_module in std_lib_modules, f"Non-standard import-from found: {node.module}"


# ============================================================================
# 2. Phase 271: Maritime Casualty Formal Inquiry Engine Tests
# ============================================================================

def test_casualty_very_serious_total_loss():
    """Test very serious marine casualty (total loss / fatalities / severe pollution)."""
    data = MarineCasualtyData(
        vessel_name="MV PACIFIC STAR",
        imo_number="9123456",
        casualty_type=CasualtyType.COLLISION,
        has_total_loss=True,
        fatalities_count=2,
        severe_injuries_count=5,
        is_severe_pollution=True,
        is_immobilized=True,
        has_major_structural_damage=True,
        hours_since_occurrence=18.0,
    )
    report = MarineCasualtyInquiryEngine.evaluate_casualty(data)
    assert report.severity_level == CasualtySeverity.VERY_SERIOUS_MARINE_CASUALTY
    assert report.is_mandatory_formal_inquiry is True
    assert report.casualty_board_required is True
    assert report.statutory_investigation_max_days == 90
    assert report.emergency_report_deadline_hours == 24.0
    assert report.formal_declaration_deadline_hours == 48.0
    assert report.is_emergency_report_overdue is False
    assert "đặc biệt nghiêm trọng" in report.summary_vi.lower()


def test_casualty_serious_structural_damage():
    """Test serious marine casualty with severe structural damage and immobilization."""
    data = MarineCasualtyData(
        vessel_name="MV MEKONG HOPE",
        imo_number="9345678",
        casualty_type=CasualtyType.GROUNDING,
        has_total_loss=False,
        fatalities_count=0,
        severe_injuries_count=1,
        is_severe_pollution=False,
        is_immobilized=True,
        has_major_structural_damage=True,
        hours_since_occurrence=30.0,
    )
    report = MarineCasualtyInquiryEngine.evaluate_casualty(data)
    assert report.severity_level == CasualtySeverity.SERIOUS_MARINE_CASUALTY
    assert report.is_mandatory_formal_inquiry is True
    assert report.casualty_board_required is True
    assert report.statutory_investigation_max_days == 60
    assert report.is_emergency_report_overdue is True


def test_casualty_standard_collision_and_incident():
    """Test standard marine casualty and minor marine incident."""
    data_mc = MarineCasualtyData(
        vessel_name="MV BLUE WAVE",
        imo_number="9456789",
        casualty_type=CasualtyType.COLLISION,
        hours_since_occurrence=10.0,
    )
    rep_mc = MarineCasualtyInquiryEngine.evaluate_casualty(data_mc)
    assert rep_mc.severity_level == CasualtySeverity.MARINE_CASUALTY
    assert rep_mc.is_mandatory_formal_inquiry is False
    assert rep_mc.casualty_board_required is False
    assert rep_mc.statutory_investigation_max_days == 60

    data_mi = MarineCasualtyData(
        vessel_name="MV AN PHU",
        imo_number="9567890",
        casualty_type=CasualtyType.MACHINERY_BREAKDOWN,
        hours_since_occurrence=5.0,
    )
    rep_mi = MarineCasualtyInquiryEngine.evaluate_casualty(data_mi)
    assert rep_mi.severity_level == CasualtySeverity.MARINE_INCIDENT
    assert rep_mi.statutory_investigation_max_days == 30


# ============================================================================
# 3. Phase 272: Electronic Certificate of Origin (e-C/O) & ROO Engine Tests
# ============================================================================

def test_eco_wholly_obtained():
    """Test wholly obtained (WO) agricultural or mineral maritime exports."""
    inp = ProductOriginInput(
        product_hs_code="0901.11",
        fob_price_usd=2500.0,
        originating_materials_value_usd=2500.0,
        non_originating_materials_value_usd=0.0,
        direct_labor_and_overhead_usd=300.0,
        trade_agreement=TradeAgreement.EVFTA,
        is_wholly_obtained=True,
    )
    res = ElectronicCOEngine.evaluate_origin(inp)
    assert res.is_originating is True
    assert res.qualifying_criterion == OriginCriterion.WHOLLY_OBTAINED
    assert res.preferential_duty_eligible is True
    assert res.de_minimis_tolerance_percent == 0.0
    assert res.is_de_minimis_compliant is True


def test_eco_regional_value_content_evfta():
    """Test EVFTA RVC build-down and build-up calculations."""
    # FOB = 1000, VNM = 400 -> Build-Down = 60%, Required EVFTA = 45% -> Originating
    inp = ProductOriginInput(
        product_hs_code="8471.30",
        fob_price_usd=1000.0,
        originating_materials_value_usd=500.0,
        non_originating_materials_value_usd=400.0,
        direct_labor_and_overhead_usd=100.0,
        trade_agreement=TradeAgreement.EVFTA,
        is_wholly_obtained=False,
    )
    res = ElectronicCOEngine.evaluate_origin(inp)
    assert res.is_originating is True
    assert res.rvc_build_down_percent == pytest.approx(60.0, 0.01)
    assert res.rvc_build_up_percent == pytest.approx(60.0, 0.01)
    assert res.preferential_duty_eligible is True
    assert res.qualifying_criterion == OriginCriterion.REGIONAL_VALUE_CONTENT


def test_eco_non_qualifying_and_zero_fob_error():
    """Test origin rejection when VNM exceeds allowable threshold and invalid FOB validation."""
    inp_reject = ProductOriginInput(
        product_hs_code="8504.40",
        fob_price_usd=1000.0,
        originating_materials_value_usd=200.0,
        non_originating_materials_value_usd=800.0,
        direct_labor_and_overhead_usd=50.0,
        trade_agreement=TradeAgreement.CPTPP,
        is_wholly_obtained=False,
    )
    res_reject = ElectronicCOEngine.evaluate_origin(inp_reject)
    assert res_reject.is_originating is False
    assert res_reject.preferential_duty_eligible is False
    assert res_reject.rvc_build_down_percent == pytest.approx(20.0, 0.01)

    inp_invalid = ProductOriginInput(
        product_hs_code="8504.40",
        fob_price_usd=0.0,
        originating_materials_value_usd=0.0,
        non_originating_materials_value_usd=0.0,
        direct_labor_and_overhead_usd=0.0,
        trade_agreement=TradeAgreement.EVFTA,
    )
    with pytest.raises(ValueError, match="FOB price must be greater than zero"):
        ElectronicCOEngine.evaluate_origin(inp_invalid)


# ============================================================================
# 4. Phase 273: Seaport Tugboat Towage Tariffs Engine Tests
# ============================================================================

def test_tugboat_international_zone_iii_surcharges():
    """Test international voyage tugboat towage tariff with night, hazmat and weather surcharges."""
    job = TugboatJobData(
        voyage_type=TugVoyageType.INTERNATIONAL,
        port_zone=TugMaritimeZone.ZONE_III_SOUTH,
        tugboat_horsepower_hp=4000.0,  # Tier 4000 HP: 560 USD/h
        number_of_tugs=2,
        duration_hours=2.5,
        is_night_operation=True,
        is_hazardous_cargo_tanker=True,
        is_adverse_weather=True,
        is_standby_only=False,
    )
    res = SeaportTugTariffEngine.calculate_towage(job)
    assert res.currency == "USD"
    assert res.base_hourly_rate == 560.0
    # Base: 560 * 2.5 * 2 = 2800 USD
    assert res.base_towage_charge == pytest.approx(2800.0, 0.01)
    # Night: +30% = 840, Hazmat: +30% = 840, Weather: +50% = 1400
    assert res.night_surcharge == pytest.approx(840.0, 0.01)
    assert res.hazmat_surcharge == pytest.approx(840.0, 0.01)
    assert res.adverse_weather_surcharge == pytest.approx(1400.0, 0.01)
    # Total: 2800 + 840 + 840 + 1400 = 5880 USD
    assert res.total_tugboat_charge == pytest.approx(5880.0, 0.01)


def test_tugboat_domestic_zone_ii_standby():
    """Test domestic voyage in Zone II (5% discount) with standby only mode (50% charge)."""
    job = TugboatJobData(
        voyage_type=TugVoyageType.DOMESTIC,
        port_zone=TugMaritimeZone.ZONE_II_CENTRAL,
        tugboat_horsepower_hp=2000.0,  # Base: 5,000,000 * 0.95 = 4,750,000 VND/h
        number_of_tugs=1,
        duration_hours=3.0,
        is_standby_only=True,
    )
    res = SeaportTugTariffEngine.calculate_towage(job)
    assert res.currency == "VND"
    assert res.base_hourly_rate == pytest.approx(4750000.0, 0.01)
    # Raw base = 4,750,000 * 3 = 14,250,000
    # Standby base = 14,250,000 * 0.50 = 7,125,000 VND
    assert res.base_towage_charge == pytest.approx(7125000.0, 0.01)
    assert res.total_tugboat_charge == pytest.approx(7125000.0, 0.01)


# ============================================================================
# 5. Phase 274: SOLAS Verified Gross Mass (VGM) Verification Engine Tests
# ============================================================================

def test_vgm_compliant_method_1():
    """Test compliant container VGM verification within statutory tolerance."""
    container = ContainerVgmInput(
        container_number="MSKU9081234",
        container_size_ft=40,
        tare_weight_kg=3850.0,
        csc_max_gross_weight_kg=32500.0,
        declared_vgm_kg=28000.0,
        weighbridge_measured_gross_kg=28200.0,
    )
    res = SolasVgmEngine.verify_vgm(container)
    assert res.vgm_status == VgmStatus.VERIFIED_AND_ACCEPTED
    assert res.variance_kg == 200.0
    assert res.variance_percentage == pytest.approx((200.0 / 28000.0) * 100.0, 0.01)
    assert res.allowed_tolerance_kg == min(28000.0 * 0.05, 500.0)
    assert res.is_csc_overload is False
    assert res.terminal_weighing_fee_vnd == 350000.0


def test_vgm_missing_and_csc_overload_rejections():
    """Test strict 'No VGM, No Load' rejections on missing declaration and CSC plate overload."""
    # Missing VGM
    cntr_missing = ContainerVgmInput(
        container_number="TGHU1234567",
        container_size_ft=20,
        tare_weight_kg=2200.0,
        csc_max_gross_weight_kg=24000.0,
        declared_vgm_kg=None,
        weighbridge_measured_gross_kg=21000.0,
    )
    res_missing = SolasVgmEngine.verify_vgm(cntr_missing)
    assert res_missing.vgm_status == VgmStatus.REJECTED_MISSING_VGM
    assert res_missing.terminal_weighing_fee_vnd == 250000.0

    # CSC Overload
    cntr_overload = ContainerVgmInput(
        container_number="CMAU9876543",
        container_size_ft=40,
        tare_weight_kg=3850.0,
        csc_max_gross_weight_kg=32500.0,
        declared_vgm_kg=32000.0,
        weighbridge_measured_gross_kg=33100.0,  # Exceeds CSC 32,500 kg
    )
    res_overload = SolasVgmEngine.verify_vgm(cntr_overload)
    assert res_overload.vgm_status == VgmStatus.REJECTED_OVERWEIGHT_CSC_LIMIT
    assert res_overload.is_csc_overload is True

    # Tolerance Exceeded
    cntr_tolerance = ContainerVgmInput(
        container_number="ONEU5544332",
        container_size_ft=40,
        tare_weight_kg=3850.0,
        csc_max_gross_weight_kg=32500.0,
        declared_vgm_kg=25000.0,
        weighbridge_measured_gross_kg=26000.0,  # Variance 1000kg > allowed 500kg
    )
    res_tolerance = SolasVgmEngine.verify_vgm(cntr_tolerance)
    assert res_tolerance.vgm_status == VgmStatus.REJECTED_TOLERANCE_EXCEEDED


# ============================================================================
# 6. Typer CLI Command Integration Tests (Bilingual Aliases)
# ============================================================================

def test_cli_casualty_command_and_alias():
    """Test CLI commands 'casualty inquire' and alias 'tainan inquire'."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["casualty", "inquire", "--vessel", "MV DA NANG", "--imo", "9988776", "--type", "COLLISION"])
    assert result.exit_code == 0
    assert "BÁO CÁO PHÂN LOẠI & ĐIỀU TRA TAI NẠN HÀNG HẢI" in result.output
    assert "MV DA NANG" in result.output

    alias_res = runner.invoke(app, ["tainan", "inquire", "--vessel", "MV DA NANG"])
    assert alias_res.exit_code == 0
    assert "BÁO CÁO PHÂN LOẠI & ĐIỀU TRA TAI NẠN HÀNG HẢI" in alias_res.output


def test_cli_co_command_and_alias():
    """Test CLI commands 'coform evaluate' and alias 'xuatxuhanghoa evaluate'."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["coform", "evaluate", "--hs", "8471.30", "--fta", "EVFTA", "--fob", "1200", "--vom", "700", "--vnm", "500"])
    assert result.exit_code == 0
    assert "THẨM ĐỊNH XUẤT XỨ HÀNG HÓA & CẤP e-C/O" in result.output
    assert "EVFTA" in result.output

    alias_res = runner.invoke(app, ["xuatxuhanghoa", "evaluate"])
    assert alias_res.exit_code == 0
    assert "THẨM ĐỊNH XUẤT XỨ HÀNG HÓA & CẤP e-C/O" in alias_res.output


def test_cli_tug_command_and_alias():
    """Test CLI commands 'tugtariff calculate' and alias 'laidatcang calculate'."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["tugtariff", "calculate", "--voyage", "INTERNATIONAL", "--zone", "ZONE_III_SOUTH", "--hp", "4000", "--hours", "2.0"])
    assert result.exit_code == 0
    assert "TÍNH CƯỚC DỊCH VỤ LAI DẮT CẢNG BIỂN" in result.output
    assert "USD" in result.output

    alias_res = runner.invoke(app, ["laidatcang", "calculate"])
    assert alias_res.exit_code == 0
    assert "TÍNH CƯỚC DỊCH VỤ LAI DẮT CẢNG BIỂN" in alias_res.output


def test_cli_vgm_command_and_alias():
    """Test CLI commands 'solasvgm verify' and alias 'xacnhankhoiluong verify'."""
    runner = CliRunner()
    app = build_app()

    result = runner.invoke(app, ["solasvgm", "verify", "--cntr", "MSKU9081234", "--size", "40", "--declared", "28000", "--measured", "28200"])
    assert result.exit_code == 0
    assert "KIỂM TRA XÁC NHẬN KHỐI LƯỢNG CONTAINER" in result.output
    assert "MSKU9081234" in result.output

    alias_res = runner.invoke(app, ["xacnhankhoiluong", "verify"])
    assert alias_res.exit_code == 0
    assert "KIỂM TRA XÁC NHẬN KHỐI LƯỢNG CONTAINER" in alias_res.output


# ============================================================================
# 7. FastMCP Tool Handler & Specification Tests
# ============================================================================

def test_mcp_marine_casualty_inquiry_evaluate():
    """Test MCP handler handle_marine_casualty_inquiry_evaluate."""
    args = {
        "vessel_name": "MV HAIPHONG EXPRESS",
        "imo_number": "9654321",
        "casualty_type": "FIRE_EXPLOSION",
        "has_total_loss": True,
        "fatalities_count": 1,
        "hours_since_occurrence": 15.0,
    }
    raw = mcp_server.handle_marine_casualty_inquiry_evaluate(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["casualty_report"]["severity_level"] == "VERY_SERIOUS_MARINE_CASUALTY"
    assert res["casualty_report"]["statutory_investigation_max_days"] == 90


def test_mcp_electronic_co_origin_evaluate():
    """Test MCP handler handle_electronic_co_origin_evaluate."""
    args = {
        "product_hs_code": "0901.11",
        "trade_agreement": "EVFTA",
        "fob_price_usd": 2000.0,
        "originating_materials_value_usd": 1500.0,
        "non_originating_materials_value_usd": 500.0,
        "direct_labor_and_overhead_usd": 200.0,
        "is_wholly_obtained": False,
    }
    raw = mcp_server.handle_electronic_co_origin_evaluate(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["origin_determination"]["is_originating"] is True
    assert res["origin_determination"]["preferential_duty_eligible"] is True


def test_mcp_seaport_tugboat_tariff_calculate():
    """Test MCP handler handle_seaport_tugboat_tariff_calculate."""
    args = {
        "voyage_type": "INTERNATIONAL",
        "port_zone": "ZONE_III_SOUTH",
        "tugboat_horsepower_hp": 4000.0,
        "number_of_tugs": 2,
        "duration_hours": 2.0,
        "is_night_operation": True,
    }
    raw = mcp_server.handle_seaport_tugboat_tariff_calculate(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["tugboat_tariff"]["currency"] == "USD"
    assert res["tugboat_tariff"]["night_surcharge"] > 0


def test_mcp_solas_vgm_container_verify():
    """Test MCP handler handle_solas_vgm_container_verify."""
    args = {
        "container_number": "MSKU9081234",
        "container_size_ft": 40,
        "tare_weight_kg": 3850.0,
        "csc_max_gross_weight_kg": 32500.0,
        "declared_vgm_kg": 28000.0,
        "weighbridge_measured_gross_kg": 28200.0,
    }
    raw = mcp_server.handle_solas_vgm_container_verify(args)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["vgm_verification"]["vgm_status"] == "VERIFIED_AND_ACCEPTED"
    assert res["vgm_verification"]["variance_kg"] == 200.0


def test_mcp_server_spec_and_core_handlers_registered():
    """Verify all 4 new tools exist in CORE_TOOLS_SPEC and CORE_HANDLERS."""
    tool_names = {t["name"] for t in mcp_server.CORE_TOOLS_SPEC}
    assert "mekong_marine_casualty_inquiry_evaluate" in tool_names
    assert "mekong_electronic_co_origin_evaluate" in tool_names
    assert "mekong_seaport_tugboat_tariff_calculate" in tool_names
    assert "mekong_solas_vgm_container_verify" in tool_names

    assert "mekong_marine_casualty_inquiry_evaluate" in mcp_server.CORE_HANDLERS
    assert "marine_casualty_inquiry_evaluate" in mcp_server.CORE_HANDLERS
    assert "mekong_electronic_co_origin_evaluate" in mcp_server.CORE_HANDLERS
    assert "electronic_co_origin_evaluate" in mcp_server.CORE_HANDLERS
    assert "mekong_seaport_tugboat_tariff_calculate" in mcp_server.CORE_HANDLERS
    assert "seaport_tugboat_tariff_calculate" in mcp_server.CORE_HANDLERS
    assert "mekong_solas_vgm_container_verify" in mcp_server.CORE_HANDLERS
    assert "solas_vgm_container_verify" in mcp_server.CORE_HANDLERS
