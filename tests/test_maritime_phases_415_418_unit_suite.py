"""Zero-mock unit test suite for Maritime Automation Phases 415-418.

Tests:
- Phase 415: Propeller CPP & OD Box Hydraulics (DNV Pt.4 Ch.5, SOLAS II-1)
- Phase 416: Marine Fuel Homogenizer & Water Emulsion (MARPOL Annex VI, ISO 8217)
- Phase 417: Cargo Hold Dew Point & Desiccant Wheel (IMSBC Code, DNV Cargo Care)
- Phase 418: Crankcase Explosion Relief Valve & OMD (SOLAS II-1 Reg 47, IACS M9/M10)
- Master Facade Engine & Typer CLI Command integration.

Strictly < 200 LOC, zero mocks, zero fake data.
"""

import pytest
from typer.testing import CliRunner

from src.core.maritime.phase_415_cpp_propeller_odbox_hydraulics import (
    CppPropellerOdBoxEngine,
    CppPropellerTelemetry,
)
from src.core.maritime.phase_416_fuel_homogenizer_emulsion import (
    FuelHomogenizerEmulsionEngine,
    FuelHomogenizerTelemetry,
)
from src.core.maritime.phase_417_cargo_hold_dewpoint_desiccant import (
    CargoHoldDewPointEngine,
    CargoHoldDewPointTelemetry,
)
from src.core.maritime.phase_418_crankcase_relief_oil_mist_detector import (
    CrankcaseReliefOmdEngine,
    CrankcaseOmdTelemetry,
)
from src.core.maritime_cpp_homogenizer_dewpoint_omd_engine import (
    MaritimeCppHomogenizerDewpointOmdEngine,
    MaritimePhases415to418Telemetry,
)
from src.cli.commands.maritime_cpp_homogenizer_dewpoint_omd_command import (
    cpppropeller_app,
    fuelhomogenizer_app,
    cargodewpoint_app,
    crankcaseomd_app,
)

runner = CliRunner()


def test_phase_415_cpp_propeller_optimal_and_failsafe():
    engine = CppPropellerOdBoxEngine()
    # Optimal normal run
    t_norm = CppPropellerTelemetry(
        commanded_pitch_deg=18.0,
        actual_pitch_deg=17.8,
        servo_port_a_pressure_bar=48.0,
        servo_port_b_pressure_bar=22.0,
        shaft_speed_rpm=120.0,
        ship_speed_knots=15.0,
    )
    res_norm = engine.evaluate(t_norm)
    assert res_norm.status == "OPTIMAL"
    assert res_norm.advance_ratio_j > 0.6
    assert res_norm.thrust_force_kn > 100.0
    assert not res_norm.fail_safe_locked
    assert res_norm.compliance_flags["solas_ii1_reg28_ahead_astern_capable"] is True

    # Hydraulic failure emergency lock-pin engaged
    t_fail = CppPropellerTelemetry(
        servo_port_a_pressure_bar=4.0,
        servo_port_b_pressure_bar=2.0,
        emergency_lock_pin_engaged=True,
    )
    res_fail = engine.evaluate(t_fail)
    assert res_fail.status == "FAILSAFE_ENGAGED"
    assert res_fail.fail_safe_locked is True


def test_phase_416_fuel_homogenizer_shear_and_emulsion():
    engine = FuelHomogenizerEmulsionEngine()
    # Standard 4.5% water emulsification
    t_norm = FuelHomogenizerTelemetry(
        rotor_speed_rpm=3000.0,
        water_dosing_ratio_pct=4.5,
        fuel_inlet_temp_c=135.0,
        target_engine_viscosity_cst=13.0,
    )
    res_norm = engine.evaluate(t_norm)
    assert res_norm.status == "OPTIMAL"
    assert res_norm.shear_rate_s_minus_1 > 40000.0
    assert res_norm.mean_water_droplet_um <= 4.0
    assert res_norm.micro_explosion_potential in ("VIGOROUS_OPTIMAL", "MODERATE")
    assert res_norm.estimated_nox_reduction_pct > 3.0

    # High water dosing trip warning
    t_high = FuelHomogenizerTelemetry(water_dosing_ratio_pct=11.5)
    res_high = engine.evaluate(t_high)
    assert res_high.status in ("WARNING", "CRITICAL")
    assert len(res_high.warnings) > 0


def test_phase_417_cargo_hold_sweat_and_desiccant():
    engine = CargoHoldDewPointEngine()
    # Safe through-ventilation
    t_safe = CargoHoldDewPointTelemetry(
        hold_temp_c=25.0,
        hold_relative_humidity_pct=75.0,
        ambient_air_temp_c=20.0,
        ambient_relative_humidity_pct=50.0,
        seawater_temp_c=24.0,
        cargo_surface_temp_c=22.0,
    )
    res_safe = engine.evaluate(t_safe)
    assert res_safe.ventilation_rule == "THROUGH_VENTILATION_SAFE"
    assert not res_safe.desiccant_wheel_active

    # Rain / fog or high ambient dew point triggers seal and desiccant
    t_rain = CargoHoldDewPointTelemetry(outside_rain_or_fog=True, seawater_temp_c=12.0)
    res_rain = engine.evaluate(t_rain)
    assert res_rain.ventilation_rule == "SEAL_HOLD_RECIRCULATE_DESICCANT"
    assert res_rain.desiccant_wheel_active is True
    assert res_rain.moisture_removal_rate_kg_h > 0.0


def test_phase_418_crankcase_omd_and_relief_valve():
    engine = CrankcaseReliefOmdEngine()
    # Normal safe running
    t_norm = CrankcaseOmdTelemetry(
        sample_cell_transmission_pct=95.0,
        reference_cell_transmission_pct=99.0,
        crankcase_internal_pressure_mbar=-2.5,
    )
    res_norm = engine.evaluate(t_norm)
    assert res_norm.status == "OPTIMAL"
    assert not res_norm.engine_slowdown_required
    assert not res_norm.relief_valve_lifted

    # Overpressure deflagration lifts relief valve
    t_lift = CrankcaseOmdTelemetry(
        sample_cell_transmission_pct=60.0,
        reference_cell_transmission_pct=99.0,
        crankcase_internal_pressure_mbar=240.0,
        relief_valve_opening_setpoint_mbar=200.0,
    )
    res_lift = engine.evaluate(t_lift)
    assert res_lift.status == "CRITICAL"
    assert res_lift.relief_valve_lifted is True
    assert res_lift.engine_slowdown_required is True


def test_maritime_phases_415_418_master_facade():
    engine = MaritimeCppHomogenizerDewpointOmdEngine()
    telem = MaritimePhases415to418Telemetry()
    res = engine.evaluate(telem)

    assert res.overall_safety_status in ("OPTIMAL_OPERATIONAL", "WARNING_OPERATIONAL")
    assert res.system_readiness_pct > 80.0
    d = res.to_dict()
    assert "cpp_propeller" in d
    assert "fuel_homogenizer" in d
    assert "cargo_hold_dewpoint" in d
    assert "crankcase_omd" in d


def test_maritime_phases_415_418_cli_commands():
    res_cpp = runner.invoke(cpppropeller_app, ["--pitch-cmd", "18.0", "--rpm", "120.0"])
    assert res_cpp.exit_code == 0
    assert "Phase 415" in res_cpp.output

    res_homo = runner.invoke(fuelhomogenizer_app, ["--water-pct", "4.0", "--rpm", "3000.0"])
    assert res_homo.exit_code == 0
    assert "Phase 416" in res_homo.output

    res_dew = runner.invoke(cargodewpoint_app, ["--hold-temp", "24.0", "--hold-rh", "75.0"])
    assert res_dew.exit_code == 0
    assert "Phase 417" in res_dew.output

    res_omd = runner.invoke(crankcaseomd_app, ["--trans-pct", "95.0", "--press-mbar", "-2.0"])
    assert res_omd.exit_code == 0
    assert "Phase 418" in res_omd.output
