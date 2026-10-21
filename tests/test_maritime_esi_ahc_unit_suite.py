"""Zero-mock unit tests for Maritime Phases 369 & 370.

Phase 369: World Ports Environmental Ship Index (ESI) & Green Dues
Phase 370: Mooring Winch Auto-Tension & Active Heave Compensation (AHC)
Strictly kept under 200 lines.
"""


from src.core.maritime_fuel_bess_esi_ahc_engine import (
    EsiShipInput,
    GreenPortTier,
    MooringAutoTensionAhcEngine,
    PortEsiGreenIncentiveEngine,
    WinchActionState,
    WinchSensorInput,
)


def test_port_esi_gold_tier() -> None:
    ship = EsiShipInput(
        vessel_imo="IMO9999999",
        vessel_name="GREEN HORIZON",
        nox_reduction_pct=50.0,
        fuel_sulfur_pct=0.10,
        co2_improvement_pct=20.0,
        has_ops_cold_ironing=True,
    )
    rep = PortEsiGreenIncentiveEngine().evaluate(ship)
    assert rep.esi_total_score >= 50.0
    assert rep.tier == GreenPortTier.GOLD
    assert rep.port_dues_discount_pct == 20.0
    assert any("20% discount" in inc for inc in rep.eligible_incentives)
    assert any("auxiliary engine" in inc for inc in rep.eligible_incentives)


def test_port_esi_silver_and_standard_tiers() -> None:
    # Silver tier without OPS
    ship_silver = EsiShipInput(
        vessel_imo="IMO1111111",
        vessel_name="SILVER WAVE",
        nox_reduction_pct=30.0,
        fuel_sulfur_pct=0.25,
        co2_improvement_pct=10.0,
        has_ops_cold_ironing=False,
    )
    rep_silver = PortEsiGreenIncentiveEngine().evaluate(ship_silver)
    assert 30.0 <= rep_silver.esi_total_score < 50.0
    assert rep_silver.tier == GreenPortTier.SILVER
    assert rep_silver.port_dues_discount_pct == 10.0

    # Standard tier (high sulfur, no NOx/CO2 improvements)
    ship_standard = EsiShipInput(
        vessel_imo="IMO0000000",
        vessel_name="OLD CARRIER",
        nox_reduction_pct=0.0,
        fuel_sulfur_pct=0.50,
        co2_improvement_pct=0.0,
        has_ops_cold_ironing=False,
    )
    rep_std = PortEsiGreenIncentiveEngine().evaluate(ship_standard)
    assert rep_std.esi_total_score == 0.0
    assert rep_std.tier == GreenPortTier.STANDARD
    assert rep_std.port_dues_discount_pct == 0.0


def test_mooring_autotension_hold() -> None:
    sensor = WinchSensorInput(
        winch_id="WINCH-01",
        measured_tension_kn=200.0,
        mbl_kn=1000.0,
        target_tension_pct_mbl=20.0,  # target = 200 kN
        ship_heave_amplitude_m=0.5,
        wave_period_s=6.0,
        load_displacement_rms_m=0.03,
    )
    rep = MooringAutoTensionAhcEngine().evaluate(sensor)
    assert rep.action_state == WinchActionState.HOLD
    assert rep.is_ahc_active is True
    assert rep.ahc_efficiency_pct > 85.0
    assert rep.target_tension_kn == 200.0
    assert rep.render_threshold_kn == 250.0
    assert rep.heave_threshold_kn == 150.0


def test_mooring_autotension_render_and_heave() -> None:
    # High tension -> RENDER_OUT
    sensor_high = WinchSensorInput(
        winch_id="WINCH-RENDER",
        measured_tension_kn=260.0,  # > 250 kN
        mbl_kn=1000.0,
        target_tension_pct_mbl=20.0,
        ship_heave_amplitude_m=0.2,
        wave_period_s=5.0,
    )
    rep_high = MooringAutoTensionAhcEngine().evaluate(sensor_high)
    assert rep_high.action_state == WinchActionState.RENDER_OUT
    assert any("Auto-rendering line" in w for w in rep_high.warnings)

    # Low tension -> HEAVE_IN
    sensor_low = WinchSensorInput(
        winch_id="WINCH-HEAVE",
        measured_tension_kn=140.0,  # < 150 kN
        mbl_kn=1000.0,
        target_tension_pct_mbl=20.0,
        ship_heave_amplitude_m=0.2,
        wave_period_s=5.0,
    )
    rep_low = MooringAutoTensionAhcEngine().evaluate(sensor_low)
    assert rep_low.action_state == WinchActionState.HEAVE_IN
    assert any("Auto-heaving line" in w for w in rep_low.warnings)


def test_mooring_overload_alarm() -> None:
    sensor_overload = WinchSensorInput(
        winch_id="WINCH-ALARM",
        measured_tension_kn=550.0,  # 55% MBL >= 50% MBL
        mbl_kn=1000.0,
        target_tension_pct_mbl=20.0,
    )
    rep_overload = MooringAutoTensionAhcEngine().evaluate(sensor_overload)
    assert rep_overload.action_state == WinchActionState.OVERLOAD_ALARM
    assert any("exceeds MEG4 limit" in w for w in rep_overload.warnings)
