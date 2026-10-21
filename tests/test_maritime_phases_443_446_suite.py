"""Unit Tests for Maritime Automation Phases 443-446:
- Phase 443: Cargo Deepwell Pump Hydraulic & Stripping Interlock
- Phase 444: Nitrogen PSA Membrane Purity & Low-Pressure Buffer
- Phase 445: Cargo Hold H2S Gas Detection & Extraction Fan Safety
- Phase 446: Double-Bottom Fuel Tank Radar Overfill Protection
- Master Facade Validation

Strictly zero mocks, < 150 LOC.
"""

from src.core.maritime.phase_443_cargo_deepwell_hydraulic_stripping import (
    DeepwellPumpEngine,
    DeepwellPumpTelemetry,
)
from src.core.maritime.phase_444_nitrogen_psa_membrane_purity import (
    NitrogenPsaEngine,
    NitrogenPsaTelemetry,
)
from src.core.maritime.phase_445_cargo_hold_h2s_extraction_fan import (
    ToxicGasExtractionEngine,
    ToxicGasExtractionTelemetry,
)
from src.core.maritime.phase_446_double_bottom_radar_overfill import (
    TankOverfillEngine,
    TankOverfillTelemetry,
)
from src.core.maritime_cargo_n2_h2s_overfill_engine import (
    MaritimeCargoSafetyFacade,
)


def test_phase_443_cargo_deepwell_pump():
    engine = DeepwellPumpEngine()
    normal_telem = DeepwellPumpTelemetry(
        hydraulic_header_pressure_bar=235.0,
        hydraulic_return_pressure_bar=18.0,
        cofferdam_purge_leakage_l_min=0.08,
        cargo_leakage_detected=False,
        hydraulic_oil_ingress=False,
        stripping_suction_pressure_bar=0.35,
        cargo_temp_celsius=25.0,
    )
    res_normal = engine.evaluate(normal_telem)
    assert res_normal.is_safe is True
    assert res_normal.recommended_flow_throttle_pct == 0.0

    trip_telem = DeepwellPumpTelemetry(
        hydraulic_header_pressure_bar=145.0,  # Below 160 trip
        hydraulic_return_pressure_bar=38.0,   # Above 35 trip
        cofferdam_purge_leakage_l_min=0.85,   # Above 0.50 trip
        cargo_leakage_detected=True,
        hydraulic_oil_ingress=True,
        stripping_suction_pressure_bar=0.05,  # Cavitation
        cargo_temp_celsius=30.0,
    )
    res_trip = engine.evaluate(trip_telem)
    assert res_trip.is_safe is False
    assert res_trip.header_pressure_trip is True
    assert res_trip.return_overpressure_trip is True
    assert res_trip.cofferdam_seal_leakage_trip is True
    assert res_trip.recommended_flow_throttle_pct == 100.0


def test_phase_444_nitrogen_psa_membrane():
    engine = NitrogenPsaEngine()
    safe_telem = NitrogenPsaTelemetry(
        oxygen_content_pct=2.1,
        feed_air_pressure_bar=8.5,
        feed_air_temp_celsius=42.0,
        feed_air_dew_point_celsius=-48.0,
        buffer_tank_pressure_bar=7.8,
    )
    res_safe = engine.evaluate(safe_telem)
    assert res_safe.is_safe is True
    assert res_safe.dump_valve_open is False

    degraded_telem = NitrogenPsaTelemetry(
        oxygen_content_pct=6.5,  # >5.0% O2 -> Dump
        feed_air_pressure_bar=6.0,
        feed_air_temp_celsius=58.0,
        feed_air_dew_point_celsius=-20.0,
        buffer_tank_pressure_bar=3.5,  # <4.5 bar -> Collapse
    )
    res_deg = engine.evaluate(degraded_telem)
    assert res_deg.is_safe is False
    assert res_deg.dump_valve_open is True
    assert res_deg.buffer_pressure_low_trip is True


def test_phase_445_cargo_hold_h2s_and_extraction():
    engine = ToxicGasExtractionEngine()
    normal_telem = ToxicGasExtractionTelemetry(
        h2s_concentration_ppm=1.2,
        lel_combustible_pct=3.0,
        fan_dp_pascals=380.0,
        exhaust_temp_celsius=32.0,
        extraction_fan_running=True,
    )
    res_norm = engine.evaluate(normal_telem)
    assert res_norm.is_safe is True
    assert res_norm.emergency_booster_fan_required is False

    toxic_telem = ToxicGasExtractionTelemetry(
        h2s_concentration_ppm=16.0,  # > 10 ppm -> Evac
        lel_combustible_pct=25.0,   # > 20% -> Trip
        fan_dp_pascals=120.0,       # < 250 Pa -> Fan failure
        exhaust_temp_celsius=72.0,
        extraction_fan_running=True,
    )
    res_toxic = engine.evaluate(toxic_telem)
    assert res_toxic.is_safe is False
    assert res_toxic.h2s_evacuation_trip is True
    assert res_toxic.lel_combustible_trip is True
    assert res_toxic.ventilation_failure is True
    assert res_toxic.emergency_booster_fan_required is True


def test_phase_446_double_bottom_radar_overfill():
    engine = TankOverfillEngine()
    safe_bunker = TankOverfillTelemetry(
        radar_sounding_pct=75.0,
        independent_high_high_sensor=False,
        bunker_flow_rate_m3_h=200.0,
        manifold_valve_closed=False,
        vent_trunk_pressure_mbar=6.0,
    )
    res_safe = engine.evaluate(safe_bunker, tank_total_capacity_m3=500.0)
    assert res_safe.is_safe is True
    assert res_safe.manifold_shutdown_tripped is False
    assert res_safe.time_to_overflow_seconds > 60.0

    critical_bunker = TankOverfillTelemetry(
        radar_sounding_pct=98.5,
        independent_high_high_sensor=True,
        bunker_flow_rate_m3_h=250.0,
        manifold_valve_closed=False,
        vent_trunk_pressure_mbar=32.0,
    )
    res_crit = engine.evaluate(critical_bunker, tank_total_capacity_m3=500.0)
    assert res_crit.is_safe is False
    assert res_crit.high_high_trip_98 is True
    assert res_crit.manifold_shutdown_tripped is True
    assert res_crit.vent_overpressure_risk is True


def test_master_facade_evaluation():
    facade = MaritimeCargoSafetyFacade()
    dw = DeepwellPumpTelemetry(230.0, 18.0, 0.05, False, False, 0.30, 20.0)
    psa = NitrogenPsaTelemetry(2.0, 8.0, 40.0, -45.0, 7.5)
    gas = ToxicGasExtractionTelemetry(0.5, 1.0, 400.0, 28.0, True)
    of = TankOverfillTelemetry(80.0, False, 100.0, False, 5.0)

    res = facade.evaluate_all(dw, psa, gas, of)
    assert res.overall_safe is True
    assert len(res.aggregated_critical_alarms) == 0
