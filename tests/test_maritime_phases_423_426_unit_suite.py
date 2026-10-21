"""Zero-mock unit test suite for Maritime Automation Phases 423-426.

Tests:
- Phase 423: Exhaust Gas Economizer Soot Water Washing & Delta-P (MEPC.340(77), IACS M53)
- Phase 424: Marine Thermal Oil Heating System & N2 Blanketing (DIN 4754, ISO 5149)
- Phase 425: Machinery Bilge Water Vacuum Evaporator & Distillation (MARPOL Annex I)
- Phase 426: Crankcase Explosion Relief Valve & Oil Mist Detector (IACS UR M9/M10)
- Master Facade & Typer CLI Commands.

Strictly < 180 LOC, zero mocks, zero fake data.
"""

from typer.testing import CliRunner

from src.core.maritime.phase_423_economizer_soot_wash import (
    EconomizerSootWashEngine,
    EconomizerSootWashTelemetry,
)
from src.core.maritime.phase_424_thermal_oil_system import (
    ThermalOilSystemEngine,
    ThermalOilTelemetry,
)
from src.core.maritime.phase_425_bilge_water_evaporator import (
    BilgeEvaporatorEngine,
    BilgeEvaporatorTelemetry,
)
from src.core.maritime.phase_426_crankcase_relief_omd import (
    CrankcaseOmdEngine,
    CrankcaseOmdTelemetry,
)
from src.core.maritime_economizer_thermal_bilge_crankcase_engine import (
    MaritimeEconomizerThermalBilgeCrankcaseEngine,
    MaritimePhases423to426Telemetry,
)
from src.cli.commands.maritime_economizer_thermal_bilge_crankcase_command import (
    sootwash_app,
    thermaloil_app,
    bilgeevap_app,
    crankcasesafety_app,
)

runner = CliRunner()


def test_phase_423_economizer_soot_wash_normal_and_trip():
    engine = EconomizerSootWashEngine()
    # Nominal condition
    t_nom = EconomizerSootWashTelemetry(gas_inlet_temp_c=310.0, gas_diff_pressure_kpa=1.1)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NOMINAL"
    assert res_nom.soot_fire_emergency_trip is False
    assert res_nom.fouling_severity_pct == 0.0

    # Emergency soot fire (> 450°C)
    t_fire = EconomizerSootWashTelemetry(gas_inlet_temp_c=465.0)
    res_fire = engine.evaluate(t_fire)
    assert res_fire.soot_fire_emergency_trip is True
    assert res_fire.status == "EMERGENCY_TRIP"
    assert "EMERGENCY SOOT FIRE" in str(res_fire.warnings)

    # Wash active without damper 100% open
    t_wash = EconomizerSootWashTelemetry(wash_active=True, bypass_damper_open_pct=50.0)
    res_wash = engine.evaluate(t_wash)
    assert res_wash.wash_permit_granted is False
    assert res_wash.compliance_flags["damper_interlock"] is False


def test_phase_424_thermal_oil_system_nominal_and_trips():
    engine = ThermalOilSystemEngine()
    # Nominal condition
    t_nom = ThermalOilTelemetry(bulk_temp_c=260.0, film_temp_c=295.0, heater_diff_pressure_bar=1.8)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NOMINAL"
    assert res_nom.burner_interlock_clear is True
    assert res_nom.emergency_burner_trip is False

    # Film temperature overheat (> 340°C)
    t_overheat = ThermalOilTelemetry(film_temp_c=348.0)
    res_overheat = engine.evaluate(t_overheat)
    assert res_overheat.film_overheat_detected is True
    assert res_overheat.emergency_burner_trip is True
    assert res_overheat.status == "EMERGENCY_TRIP"

    # Flow starvation (DP < 1.5 bar)
    t_starv = ThermalOilTelemetry(heater_diff_pressure_bar=1.1)
    res_starv = engine.evaluate(t_starv)
    assert res_starv.flow_starvation_trip is True
    assert res_starv.emergency_burner_trip is True


def test_phase_425_bilge_water_evaporator_distillation():
    engine = BilgeEvaporatorEngine()
    # Nominal distillation (<= 5.0 ppm)
    t_nom = BilgeEvaporatorTelemetry(chamber_pressure_bar=0.22, distillate_oil_ppm=1.2)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NOMINAL_DISTILLING"
    assert res_nom.overboard_discharge_permitted is True
    assert res_nom.distillation_efficiency_pct >= 90.0

    # Foam carryover (> 150 mm)
    t_foam = BilgeEvaporatorTelemetry(foam_level_mm=175.0)
    res_foam = engine.evaluate(t_foam)
    assert res_foam.defoamer_dosing_active is True
    assert "Foam surge" in str(res_foam.warnings)

    # Distillate oil off-spec (> 5.0 ppm)
    t_off = BilgeEvaporatorTelemetry(distillate_oil_ppm=6.5)
    res_off = engine.evaluate(t_off)
    assert res_off.overboard_discharge_permitted is False
    assert res_off.recirculation_valve_active is True


def test_phase_426_crankcase_relief_omd_protection():
    engine = CrankcaseOmdEngine()
    # Nominal condition (< 1.0 mg/L)
    t_nom = CrankcaseOmdTelemetry(mist_concentration_mg_l=0.25)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NOMINAL_CLEAR"
    assert res_nom.emergency_slowdown_trip is False

    # Emergency mist trip (>= 2.0 mg/L)
    t_trip = CrankcaseOmdTelemetry(mist_concentration_mg_l=2.4)
    res_trip = engine.evaluate(t_trip)
    assert res_trip.emergency_slowdown_trip is True
    assert res_trip.status == "EMERGENCY_STOP_SLOWDOWN"
    assert "CRITICAL OIL MIST EXPLOSION HAZARD" in str(res_trip.warnings)

    # Door opening lockout (< 20 min)
    t_door = CrankcaseOmdTelemetry(crankcase_door_open_requested=True, minutes_since_engine_stop=12.0)
    res_door = engine.evaluate(t_door)
    assert res_door.door_opening_lockout_active is True
    assert res_door.compliance_flags["SOLAS_II_1_Reg_31"] is False


def test_maritime_phases_423_426_master_facade():
    facade = MaritimeEconomizerThermalBilgeCrankcaseEngine()
    t_all = MaritimePhases423to426Telemetry()
    res = facade.evaluate_all(t_all)
    assert res.overall_status == "ALL_SYSTEMS_NOMINAL"
    assert res.system_wide_trip_active is False

    # Trip scenario
    t_emergency = MaritimePhases423to426Telemetry(
        sootwash=EconomizerSootWashTelemetry(gas_inlet_temp_c=460.0)
    )
    res_emergency = facade.evaluate_all(t_emergency)
    assert res_emergency.system_wide_trip_active is True
    assert res_emergency.overall_status == "EMERGENCY_ACTIVE"


def test_maritime_phases_423_426_cli_commands():
    res_sw = runner.invoke(sootwash_app, ["--diff-p", "1.1"])
    assert res_sw.exit_code == 0
    assert "NOMINAL" in res_sw.stdout

    res_to = runner.invoke(thermaloil_app, ["--bulk-c", "260.0"])
    assert res_to.exit_code == 0
    assert "NOMINAL" in res_to.stdout

    res_be = runner.invoke(bilgeevap_app, ["--oil-ppm", "1.2"])
    assert res_be.exit_code == 0
    assert "NOMINAL_DISTILLING" in res_be.stdout

    res_cc = runner.invoke(crankcasesafety_app, ["--mist-mg-l", "0.25"])
    assert res_cc.exit_code == 0
    assert "NOMINAL_CLEAR" in res_cc.stdout
