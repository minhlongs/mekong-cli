"""Unit tests for Maritime Phase 389 & Phase 390.

Testing Controllable Pitch Propeller (CPP) Hydraulics & Cryogenic Tank Leak Sniffing.
Strictly zero mock dependencies, exact physical calculations.
"""

from src.core.maritime.phase_389_cpp_pitch_hydraulic_load import (
    CppPitchControlEngine,
    CppPitchControlInput,
)
from src.core.maritime.phase_390_cryogenic_tank_leak_insulation import (
    CryogenicTankLeakEngine,
    CryogenicTankLeakInput,
)


def test_cpp_normal_operation():
    engine = CppPitchControlEngine()
    inp = CppPitchControlInput(
        commanded_pitch_deg=22.0,
        actual_pitch_deg=21.9,
        pitch_travel_time_s=16.0,
        hydraulic_pressure_bar=58.0,
        seal_header_pressure_bar=2.3,
        sea_water_draft_pressure_bar=1.5,
        main_engine_load_pct=85.0,
        exhaust_gas_temp_c=420.0,
    )
    res = engine.evaluate(inp)
    assert res.hydraulic_status == "NORMAL"
    assert res.pitch_response_compliant is True
    assert res.seal_barrier_intact is True
    assert res.seal_pressure_margin_bar == 0.8
    assert res.engine_overload_protection is False
    assert res.recommended_pitch_deg == 22.0
    assert len(res.warnings) == 0


def test_cpp_engine_overload_auto_derating():
    engine = CppPitchControlEngine()
    # Engine load 108% MCR -> pitch should automatically reduce
    inp = CppPitchControlInput(
        commanded_pitch_deg=24.0,
        main_engine_load_pct=108.0,
        exhaust_gas_temp_c=490.0,
    )
    res = engine.evaluate(inp)
    assert res.engine_overload_protection is True
    assert res.recommended_pitch_deg < 24.0
    # Overload delta = 8%, reduction = 4.0 deg -> 20.0 deg
    assert res.recommended_pitch_deg == 20.0
    assert any("ENGINE OVERLOAD PROTECTION ACTIVE" in w for w in res.warnings)


def test_cpp_low_pressure_and_seal_compromised():
    engine = CppPitchControlEngine()
    # Hydraulic pressure < 35 bar, seal margin < 0.30 bar
    inp = CppPitchControlInput(
        hydraulic_pressure_bar=30.0,
        seal_header_pressure_bar=1.7,
        sea_water_draft_pressure_bar=1.6,
        pitch_travel_time_s=28.0,
    )
    res = engine.evaluate(inp)
    assert res.hydraulic_status == "LOW_PRESSURE"
    assert res.pitch_response_compliant is False
    assert res.seal_barrier_intact is False
    assert res.seal_pressure_margin_bar == 0.1
    assert any("CPP HYDRAULIC PRESSURE LOW" in w for w in res.warnings)
    assert any("CPP TRAVEL SLUGGISH" in w for w in res.warnings)
    assert any("STERN TUBE SEAL BARRIER COMPROMISED" in w for w in res.warnings)


def test_cryo_tank_safe_nominal_inerting():
    engine = CryogenicTankLeakEngine()
    inp = CryogenicTankLeakInput(
        methane_concentration_vol_pct=0.04,
        dew_point_c=-48.0,
        oxygen_concentration_pct=0.4,
        insulation_diff_pressure_kpa=0.7,
        inner_hull_steel_temp_c=14.0,
    )
    res = engine.evaluate(inp)
    assert res.barrier_integrity == "INTACT"
    assert res.atmosphere_inert_compliant is True
    assert res.pressure_relief_required is False
    assert res.hull_cold_spot_detected is False
    assert res.cargo_tank_safety_status == "SAFE"
    assert res.vent_mast_exhaust_active is False
    assert len(res.warnings) == 0


def test_cryo_tank_critical_barrier_breach_and_cold_spot():
    engine = CryogenicTankLeakEngine()
    # CH4 >= 1.5% vol and inner hull temp < 0.0 C
    inp = CryogenicTankLeakInput(
        methane_concentration_vol_pct=2.1,
        dew_point_c=-35.0,
        oxygen_concentration_pct=1.4,
        insulation_diff_pressure_kpa=3.2,
        inner_hull_steel_temp_c=-4.5,
    )
    res = engine.evaluate(inp)
    assert res.barrier_integrity == "PRIMARY_BARRIER_BREACH"
    assert res.atmosphere_inert_compliant is False
    assert res.pressure_relief_required is True
    assert res.hull_cold_spot_detected is True
    assert res.cargo_tank_safety_status == "CRITICAL_EMERGENCY"
    assert res.vent_mast_exhaust_active is True
    assert any("PRIMARY BARRIER BREACH" in w for w in res.warnings)
    assert any("CRITICAL COLD SPOT DETECTED" in w for w in res.warnings)
    assert any("INSULATION OVERPRESSURE" in w for w in res.warnings)
