"""Zero-mock Comprehensive Test Suite for Maritime Phases 335-338.

Covers:
- Phase 335: VTS & TSS Traffic Separation Navigation (COLREGs Rule 10, CPA/TCPA)
- Phase 336: Project Cargo & Heavy Lift OOG CSS Lashing Safety (IMO CSS Code Annex 13)
- Phase 337: Green Port Electric Tug & Cold Ironing Energy (IEC/IEEE 80005)
- Phase 338: BIMCO Charterparty Performance & Maritime Arbitration (LMAA/VMAC)
- Central Facade, Typer CLI commands, 8 Vietnamese aliases, and FastMCP endpoints.
"""

import json
import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime_vts_css_tug_charter_engine import (
    CharterpartyArbitrationEngine,
    CharterpartyDisputeInput,
    ElectricTugColdIroningEngine,
    ElectricTugColdIroningInput,
    LashingDevice,
    ProjectCargoCssLashingEngine,
    ProjectCargoLashingInput,
    VtsNavigationInput,
    VtsTssNavigationEngine,
)

runner = CliRunner()
app = build_app()


# ==============================================================================
# Phase 335: VTS & TSS Navigation Management Unit Tests
# ==============================================================================


def test_vts_tss_compliant_lane_navigation():
    """Vessel following lane correctly within corridor limits."""
    inp = VtsNavigationInput(
        vessel_mmsi="574000111",
        vessel_name="MV MEKONG EXPRESS",
        lat=10.20,
        lon=107.02,
        course_deg=135.0,
        speed_knots=11.5,
        tss_lane_name="Vung Tau TSS Inbound",
        tss_lane_heading_deg=135.0,
        tss_lane_width_nm=1.5,
        cross_track_error_nm=0.2,
    )
    res = VtsTssNavigationEngine.evaluate(inp)
    assert res.colregs_rule10_compliant is True
    assert res.is_wrong_way is False
    assert res.is_outside_corridor is False
    assert res.vts_service_level == "INS"
    assert res.heading_deviation_deg == 0.0


def test_vts_tss_wrong_way_severe_violation():
    """Vessel navigating against the TSS flow (> 90 deg deviation) triggers NAS."""
    inp = VtsNavigationInput(
        vessel_mmsi="574000222",
        vessel_name="MV ROGUE TRADER",
        lat=10.22,
        lon=107.03,
        course_deg=315.0,  # Opposite heading (180 deg)
        speed_knots=12.0,
        tss_lane_name="Vung Tau TSS Inbound",
        tss_lane_heading_deg=135.0,
    )
    res = VtsTssNavigationEngine.evaluate(inp)
    assert res.colregs_rule10_compliant is False
    assert res.is_wrong_way is True
    assert res.vts_service_level == "NAS"
    assert any("COLREGs Rule 10 violation" in adv for adv in res.advisories)


def test_vts_tss_outside_corridor():
    """Cross track error exceeding lane half width triggers warning & TOS."""
    inp = VtsNavigationInput(
        vessel_mmsi="574000333",
        vessel_name="MV DRIFTING STAR",
        lat=10.25,
        lon=107.10,
        course_deg=140.0,
        speed_knots=10.0,
        tss_lane_name="Vung Tau TSS Inbound",
        tss_lane_heading_deg=135.0,
        tss_lane_width_nm=1.0,
        cross_track_error_nm=0.8,  # > 0.5 NM
    )
    res = VtsTssNavigationEngine.evaluate(inp)
    assert res.colregs_rule10_compliant is False
    assert res.is_outside_corridor is True
    assert res.vts_service_level == "TOS"


def test_vts_cpa_tcpa_collision_risk_alert():
    """Detects dangerous encounter when CPA < 1.0 NM and TCPA <= 15 min."""
    # Target approaching on collision course
    inp = VtsNavigationInput(
        vessel_mmsi="574000111",
        vessel_name="MV MEKONG 1",
        lat=10.00,
        lon=107.00,
        course_deg=0.0,
        speed_knots=12.0,
        tss_lane_name="Vung Tau Outer",
        tss_lane_heading_deg=0.0,
        target_mmsi="574999999",
        target_lat=10.05,  # 3 NM north
        target_lon=107.00,
        target_course_deg=180.0,  # Head-on
        target_speed_knots=12.0,
    )
    res = VtsTssNavigationEngine.evaluate(inp)
    assert res.cpa_nm is not None
    assert res.cpa_nm < 1.0
    assert res.tcpa_minutes is not None
    assert res.tcpa_minutes <= 15.0
    assert res.collision_risk is True
    assert res.vts_service_level == "NAS"


# ==============================================================================
# Phase 336: Project Cargo & Heavy Lift CSS Lashing Unit Tests
# ==============================================================================


def test_css_lashing_compliant_heavy_cargo():
    """Heavy lift 120t cargo with sufficient lashings passes SF >= 1.25."""
    lashings = [
        LashingDevice(
            device_id=f"LASH-{i}",
            msl_kn=120.0,
            vertical_angle_deg=30.0,
            horizontal_angle_deg=15.0,
        )
        for i in range(8)
    ]
    inp = ProjectCargoLashingInput(
        cargo_id="CRG-TRANSFORMER-100",
        description="Substation Transformer",
        mass_metric_ton=120.0,
        cog_height_m=2.0,
        cargo_width_m=3.5,
        accel_transverse_ay=4.5,
        accel_vertical_az=1.5,
        dunnage_friction_mu=0.3,
        lashings=lashings,
    )
    res = ProjectCargoCssLashingEngine.evaluate(inp)
    assert res.is_overall_compliant is True
    assert res.is_sliding_safe is True
    assert res.is_tipping_safe is True
    assert res.sliding_safety_factor >= 1.25
    assert res.tipping_safety_factor >= 1.25


def test_css_lashing_insufficient_sliding_safety():
    """Inadequate number of lashings fails sliding SF threshold."""
    # Only 2 weak lashings
    lashings = [
        LashingDevice(device_id="LASH-01", msl_kn=40.0, vertical_angle_deg=45.0, horizontal_angle_deg=30.0),
        LashingDevice(device_id="LASH-02", msl_kn=40.0, vertical_angle_deg=45.0, horizontal_angle_deg=30.0),
    ]
    inp = ProjectCargoLashingInput(
        cargo_id="CRG-TURBINE-01",
        description="Gas Turbine Rotor",
        mass_metric_ton=90.0,
        cog_height_m=2.5,
        cargo_width_m=2.5,
        accel_transverse_ay=6.0,  # High roll accel
        accel_vertical_az=2.5,
        dunnage_friction_mu=0.1,  # Steel on steel without rubber/wood
        lashings=lashings,
    )
    res = ProjectCargoCssLashingEngine.evaluate(inp)
    assert res.is_sliding_safe is False
    assert res.is_overall_compliant is False
    assert res.sliding_safety_factor < 1.25
    assert any("UNSAFE SLIDING" in adv for adv in res.advisories)


# ==============================================================================
# Phase 337: Green Port Electric Tug & Cold Ironing Unit Tests
# ==============================================================================


def test_electric_tug_optimal_energy_and_cold_ironing():
    """Efficient bollard pull metric and normal cold ironing."""
    inp = ElectricTugColdIroningInput(
        tug_name="GREEN TUG VUNG TAU 01",
        battery_capacity_kwh=3000.0,
        current_soc_pct=65.0,
        bollard_pull_ahead_tons=75.0,
        towage_duration_hours=2.5,
        towage_energy_consumed_kwh=20.0,  # 20 / (75*2.5 = 187.5) = 0.107 kWh/(t*h)
        shore_grid_max_kw=1500.0,
        vessel_berth_load_kw=800.0,
        shore_charging_power_kw=400.0,
    )
    res = ElectricTugColdIroningEngine.evaluate(inp)
    assert res.is_bollard_pull_efficient is True
    assert res.bollard_pull_metric_kwh_per_ton_h <= 0.15
    assert res.is_emergency_soc_compliant is True
    assert res.peak_shaving_active is False
    assert res.co2_abated_metric_ton > 0.0
    assert res.nox_abated_kg > 0.0


def test_electric_tug_low_soc_and_peak_shaving():
    """Low battery SoC warning and shore substation peak shaving engagement."""
    inp = ElectricTugColdIroningInput(
        tug_name="GREEN TUG SAIGON 02",
        battery_capacity_kwh=2000.0,
        current_soc_pct=15.0,  # Below 20%
        bollard_pull_ahead_tons=60.0,
        towage_duration_hours=2.0,
        towage_energy_consumed_kwh=30.0,
        shore_grid_max_kw=1000.0,
        vessel_berth_load_kw=700.0,
        shore_charging_power_kw=500.0,  # Total 1200 > 1000 kW
    )
    res = ElectricTugColdIroningEngine.evaluate(inp)
    assert res.is_emergency_soc_compliant is False
    assert res.peak_shaving_active is True
    assert res.shore_total_demand_kw == 1000.0
    assert any("Battery SoC 15.0% below emergency reserve" in adv for adv in res.advisories)
    assert any("PEAK SHAVING ENGAGED" in adv for adv in res.advisories)


# ==============================================================================
# Phase 338: BIMCO Charterparty Arbitration Unit Tests
# ==============================================================================


def test_charterparty_time_charter_warranty_claim():
    """Good weather speed underperformance and excess bunker fuel recovery."""
    inp = CharterpartyDisputeInput(
        fixture_id="FIX-MEKONG-TC-01",
        vessel_name="MV MEKONG STAR",
        charter_type="TIME_CHARTER",
        daily_hire_or_demurrage_usd=24000.0,
        bunker_price_usd_per_mt=650.0,
        voyage_distance_nm=3600.0,
        warranted_speed_knots=13.0,
        recorded_speed_knots=11.5,
        warranted_fuel_mt_day=25.0,
        recorded_fuel_mt_day=28.0,
        beaufort_scale=3,
        douglas_sea_state=2,
    )
    res = CharterpartyArbitrationEngine.evaluate(inp)
    assert res.is_good_weather is True
    assert res.weather_excluded is False
    assert res.speed_underperformance_knots == 1.5
    assert res.time_lost_hours > 0.0
    assert res.warranty_claim_usd > 0.0
    assert res.favored_party == "CHARTERER"


def test_charterparty_good_weather_exclusion_bars_claim():
    """Adverse weather (Beaufort > 4 or Sea State > 3) excludes underperformance claim."""
    inp = CharterpartyDisputeInput(
        fixture_id="FIX-MEKONG-TC-02",
        vessel_name="MV MEKONG WAVE",
        charter_type="TIME_CHARTER",
        daily_hire_or_demurrage_usd=20000.0,
        voyage_distance_nm=2400.0,
        warranted_speed_knots=13.0,
        recorded_speed_knots=10.0,
        beaufort_scale=6,  # Heavy weather
        douglas_sea_state=4,
    )
    res = CharterpartyArbitrationEngine.evaluate(inp)
    assert res.is_good_weather is False
    assert res.weather_excluded is True
    assert res.warranty_claim_usd == 0.0
    assert res.favored_party == "NEUTRAL"
    assert any("WEATHER EXCLUSION" in adv for adv in res.advisories)


def test_charterparty_voyage_demurrage_and_despatch():
    """Voyage charter laytime demurrage for delayed discharge and despatch for early finish."""
    # 1. Demurrage scenario
    inp_dem = CharterpartyDisputeInput(
        fixture_id="FIX-MEKONG-VC-01",
        vessel_name="MV BULK PHOENIX",
        charter_type="VOYAGE_CHARTER",
        daily_hire_or_demurrage_usd=15000.0,
        allowed_laytime_hours=72.0,
        actual_laytime_used_hours=96.0,  # 24 hours exceeded (1 day demurrage)
    )
    res_dem = CharterpartyArbitrationEngine.evaluate(inp_dem)
    assert res_dem.demurrage_due_usd == 15000.0
    assert res_dem.despatch_due_usd == 0.0
    assert res_dem.favored_party == "OWNER"

    # 2. Despatch scenario
    inp_des = CharterpartyDisputeInput(
        fixture_id="FIX-MEKONG-VC-02",
        vessel_name="MV FAST DISCHARGE",
        charter_type="VOYAGE_CHARTER",
        daily_hire_or_demurrage_usd=15000.0,
        allowed_laytime_hours=72.0,
        actual_laytime_used_hours=48.0,  # 24 hours saved (0.5 rate = 7500 USD)
    )
    res_des = CharterpartyArbitrationEngine.evaluate(inp_des)
    assert res_des.demurrage_due_usd == 0.0
    assert res_des.despatch_due_usd == 7500.0
    assert res_des.favored_party == "CHARTERER"


def test_charterparty_vmac_jurisdiction_apportionment():
    """Test VMAC jurisdiction award routing for demurrage claim."""
    inp = CharterpartyDisputeInput(
        fixture_id="FIX-VMAC-01",
        vessel_name="MV SAIGON GLORY",
        charter_type="VOYAGE_CHARTER",
        daily_hire_or_demurrage_usd=10000.0,
        allowed_laytime_hours=48.0,
        actual_laytime_used_hours=72.0,
        arbitration_forum="VMAC",
    )
    res = CharterpartyArbitrationEngine.evaluate(inp)
    assert res.arbitration_forum == "VMAC"
    assert res.demurrage_due_usd == 10000.0
    assert res.favored_party == "OWNER"
    assert any("VMAC Rules" in adv for adv in res.advisories)


def test_css_lashing_tipping_moment_failure():
    """High center of gravity causes tipping safety factor violation."""
    lashings = [
        LashingDevice(device_id="LASH-T1", msl_kn=20.0, vertical_angle_deg=10.0, horizontal_angle_deg=10.0),
    ]
    inp = ProjectCargoLashingInput(
        cargo_id="CRG-TOWER-01",
        description="Fractionation Column Section",
        mass_metric_ton=50.0,
        cog_height_m=6.0,  # Very high CoG relative to width
        cargo_width_m=2.0,
        accel_transverse_ay=6.0,
        accel_vertical_az=1.0,
        dunnage_friction_mu=0.3,
        lashings=lashings,
    )
    res = ProjectCargoCssLashingEngine.evaluate(inp)
    assert res.is_tipping_safe is False
    assert res.is_overall_compliant is False
    assert any("UNSAFE TIPPING" in adv for adv in res.advisories)


# ==============================================================================
# CLI Commands and Vietnamese Aliases Tests
# ==============================================================================


def test_cli_vts_monitor_and_vietnamese_aliases():
    """CLI execution for vts monitor, luonghanghai, and phanquyvts."""
    for cmd in ["vts", "luonghanghai", "phanquyvts"]:
        result = runner.invoke(
            app,
            [
                cmd, "monitor",
                "--mmsi", "574123456",
                "--name", "MV VIET TRADER",
                "--course", "135.0",
                "--lane-heading", "135.0",
                "--xte", "0.1",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["vessel_mmsi"] == "574123456"
        assert data["colregs_rule10_compliant"] is True


def test_cli_csscargo_and_vietnamese_aliases():
    """CLI execution for csscargo lashing, hangsieutruong, and changketoog."""
    for cmd in ["csscargo", "hangsieutruong", "changketoog"]:
        result = runner.invoke(
            app,
            [
                cmd, "lashing",
                "--cargo-id", "OOG-GENERATOR-01",
                "--mass", "80.0",
                "--ay", "4.0",
                "--az", "1.5",
                "--lash-count", "6",
                "--msl", "120.0",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["cargo_id"] == "OOG-GENERATOR-01"
        assert data["is_overall_compliant"] is True


def test_cli_electug_and_vietnamese_aliases():
    """CLI execution for electug energy, taulaidien, and dienbencang."""
    for cmd in ["electug", "taulaidien", "dienbencang"]:
        result = runner.invoke(
            app,
            [
                cmd, "energy",
                "--name", "E-TUG AN HOA 01",
                "--soc", "55.0",
                "--bp-tons", "80.0",
                "--duration", "2.0",
                "--energy-kwh", "15.0",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["tug_name"] == "E-TUG AN HOA 01"
        assert data["is_emergency_soc_compliant"] is True


def test_cli_charter_and_vietnamese_aliases():
    """CLI execution for charter dispute, thuetautrongtai, and tranhchaphanghai."""
    for cmd in ["charter", "thuetautrongtai", "tranhchaphanghai"]:
        result = runner.invoke(
            app,
            [
                cmd, "dispute",
                "--fixture", "FIX-GRAIN-01",
                "--charter-type", "VOYAGE_CHARTER",
                "--daily-rate", "20000.0",
                "--allowed-laytime", "48.0",
                "--used-laytime", "72.0",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["fixture_id"] == "FIX-GRAIN-01"
        assert data["demurrage_due_usd"] == 20000.0
        assert data["favored_party"] == "OWNER"


# ==============================================================================
# FastMCP Tool Handler Async Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_fastmcp_handlers_phases_335_338():
    """Verify FastMCP tool endpoints execute with pure zero-mock data."""
    from scripts.mcp_server import (
        mekong_charterparty_arbitration_settle,
        mekong_electric_tug_cold_ironing_evaluate,
        mekong_project_cargo_css_lashing_calculate,
        mekong_vts_tss_navigation_evaluate,
    )

    # 1. VTS Navigation FastMCP
    vts_res = await mekong_vts_tss_navigation_evaluate(
        vessel_mmsi="574987654",
        vessel_name="MV FAST MCP",
        course_deg=135.0,
        tss_lane_heading_deg=135.0,
    )
    assert vts_res["vessel_mmsi"] == "574987654"
    assert vts_res["colregs_rule10_compliant"] is True

    # 2. CSS Cargo Lashing FastMCP
    css_res = await mekong_project_cargo_css_lashing_calculate(
        cargo_id="OOG-MCP-TEST",
        mass_metric_ton=60.0,
        lashing_count=6,
        msl_kn_per_lashing=100.0,
    )
    assert css_res["cargo_id"] == "OOG-MCP-TEST"
    assert css_res["is_sliding_safe"] is True

    # 3. Electric Tug FastMCP
    tug_res = await mekong_electric_tug_cold_ironing_evaluate(
        tug_name="E-TUG MCP 01",
        current_soc_pct=50.0,
    )
    assert tug_res["tug_name"] == "E-TUG MCP 01"
    assert tug_res["is_emergency_soc_compliant"] is True

    # 4. Charterparty Arbitration FastMCP
    charter_res = await mekong_charterparty_arbitration_settle(
        fixture_id="FIX-MCP-01",
        charter_type="VOYAGE_CHARTER",
        daily_hire_or_demurrage_usd=12000.0,
        allowed_laytime_hours=48.0,
        actual_laytime_used_hours=72.0,
    )
    assert charter_res["fixture_id"] == "FIX-MCP-01"
    assert charter_res["demurrage_due_usd"] == 12000.0
