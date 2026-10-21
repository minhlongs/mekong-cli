"""Zero-mock unit tests for Maritime Phases 371 & 372.

Phase 371: Shaft Generator PTO/PTI Hybrid Engine (DNV-RU-SHIP, IEC 60092-501)
Phase 372: Port Berth Allocation & Quay Crane Scheduling BAP/QCSP (UNCTAD, PIANC WG 158)
Strictly kept under 200 lines.
"""

from src.core.maritime_pto_berth_biofoul_waste_engine import (
    BerthAllocationStatus,
    BerthRequest,
    PortBerthCraneBapQcspEngine,
    ShaftGeneratorInput,
    ShaftGeneratorPtoPtiEngine,
    ShaftHybridMode,
)


def test_shaft_pto_normal_power_and_savings() -> None:
    inp = ShaftGeneratorInput(
        vessel_id="IMO9912345",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=85.0,
        main_engine_rated_rpm=100.0,  # 85% speed >= 65% min
        current_me_load_kw=6000.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=1000.0,
        hotel_load_kw=800.0,
        requested_mode=ShaftHybridMode.PTO,
        sfoc_aux_diesel_g_kwh=215.0,
        sfoc_main_engine_g_kwh=165.0,
        fuel_price_usd_tonne=600.0,
    )
    res = ShaftGeneratorPtoPtiEngine().evaluate(inp)
    assert res.is_pto_permitted is True
    assert res.active_mode == ShaftHybridMode.PTO
    assert res.me_speed_ratio_pct == 85.0
    # Expected fuel savings: 1000 * (215 - 165) / 1000 = 50.0 kg/h
    assert res.fuel_savings_kg_per_h == 50.0
    assert res.cost_savings_usd_per_h == 30.0
    assert res.co2_reduction_kg_per_h == round(50.0 * 3.114, 2)
    assert res.me_combined_load_pct_mcr == 70.0  # (6000 + 1000)/10000


def test_shaft_pto_low_speed_inhibit() -> None:
    inp = ShaftGeneratorInput(
        vessel_id="IMO9912345",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=55.0,
        main_engine_rated_rpm=100.0,  # 55% speed < 65% min
        current_me_load_kw=3500.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=1000.0,
        hotel_load_kw=800.0,
        requested_mode=ShaftHybridMode.PTO,
    )
    res = ShaftGeneratorPtoPtiEngine().evaluate(inp)
    assert res.is_pto_permitted is False
    assert res.active_mode == ShaftHybridMode.DISENGAGED
    assert res.fuel_savings_kg_per_h == 0.0
    assert any("PTO inhibited" in w for w in res.warnings)


def test_shaft_pto_torque_overload_warning() -> None:
    inp = ShaftGeneratorInput(
        vessel_id="IMO9912345",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=90.0,
        main_engine_rated_rpm=100.0,
        current_me_load_kw=7500.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=1200.0,  # 7500 + 1200 = 8700 kW -> 87% MCR > 80% limit
        hotel_load_kw=800.0,
        requested_mode=ShaftHybridMode.PTO,
    )
    res = ShaftGeneratorPtoPtiEngine().evaluate(inp)
    assert res.me_combined_load_pct_mcr == 87.0
    assert any("Torque overload risk" in w for w in res.warnings)


def test_shaft_pth_emergency_mode() -> None:
    inp = ShaftGeneratorInput(
        vessel_id="IMO9912345",
        main_engine_mcr_kw=10000.0,
        main_engine_speed_rpm=0.0,
        main_engine_rated_rpm=100.0,
        current_me_load_kw=0.0,
        shaft_gen_capacity_kw=1500.0,
        shaft_power_kw=800.0,
        hotel_load_kw=400.0,
        requested_mode=ShaftHybridMode.PTH,
    )
    res = ShaftGeneratorPtoPtiEngine().evaluate(inp)
    assert res.active_mode == ShaftHybridMode.PTH
    assert any("Take-Me-Home booster mode engaged" in w for w in res.warnings)


def test_berth_allocation_approved() -> None:
    req = BerthRequest(
        vessel_name="Vessel-Alpha",
        loa_m=300.0,
        draft_m=12.0,
        container_moves=1000,
        assigned_berth_length_m=350.0,  # Required: 300 + 30 = 330m <= 350m
        berth_chart_depth_m=13.0,
        tide_height_m=1.5,  # Effective depth: 14.5m; UKC: 2.5m >= 1.5m
        assigned_cranes=3,
        crane_spacing_m=40.0,  # Spacing >= 35.0m
        crane_productivity_moves_per_h=25.0,
    )
    res = PortBerthCraneBapQcspEngine().evaluate(req)
    assert res.status == BerthAllocationStatus.APPROVED
    assert res.required_berth_length_m == 330.0
    assert res.effective_water_depth_m == 14.5
    assert res.actual_ukc_m == 2.5
    # 1000 / (3 * 25) = 13.33 hrs
    assert res.estimated_turnaround_hours == 13.33
    assert len(res.warnings) == 0


def test_berth_insufficient_length() -> None:
    req = BerthRequest(
        vessel_name="Vessel-Beta",
        loa_m=350.0,
        draft_m=12.0,
        container_moves=800,
        assigned_berth_length_m=360.0,  # Required: 380m > 360m
        berth_chart_depth_m=15.0,
        tide_height_m=0.0,
        assigned_cranes=2,
        crane_spacing_m=50.0,
    )
    res = PortBerthCraneBapQcspEngine().evaluate(req)
    assert res.status == BerthAllocationStatus.BERTH_INSUFFICIENT
    assert any("Assigned berth 360.0m < required 380.0m" in w for w in res.warnings)


def test_berth_tidal_gating_deep_draft() -> None:
    req = BerthRequest(
        vessel_name="Vessel-Deep",
        loa_m=366.0,
        draft_m=15.0,  # Deep draft >= 14.0m
        container_moves=1500,
        assigned_berth_length_m=420.0,
        berth_chart_depth_m=14.5,
        tide_height_m=1.0,  # Effective depth 15.5m -> UKC 0.5m < 1.5m
        assigned_cranes=4,
        crane_spacing_m=45.0,
    )
    res = PortBerthCraneBapQcspEngine().evaluate(req)
    assert res.status == BerthAllocationStatus.TIDAL_WAIT
    assert any("Tidal window gating required" in w for w in res.warnings)


def test_berth_crane_spacing_violation() -> None:
    req = BerthRequest(
        vessel_name="Vessel-CraneConflict",
        loa_m=280.0,
        draft_m=11.0,
        container_moves=600,
        assigned_berth_length_m=320.0,
        berth_chart_depth_m=14.0,
        tide_height_m=0.5,
        assigned_cranes=3,
        crane_spacing_m=28.0,  # < 35.0m buffer
    )
    res = PortBerthCraneBapQcspEngine().evaluate(req)
    assert res.status == BerthAllocationStatus.CRANE_INTERFERENCE_VIOLATION
    assert any("Crane boom collision risk" in w for w in res.warnings)
