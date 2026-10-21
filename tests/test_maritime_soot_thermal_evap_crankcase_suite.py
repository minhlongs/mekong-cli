"""Zero-mock unit test suite for Maritime Automation Phases 423-426 Deep Physics & Kinetics.

Validates:
- Phase 423: Economizer soot fouling, soot fire runaway trip, and NaOH neutralization.
- Phase 424: Thermal oil boundary film temp, turbulent Reynolds number, N2 cushion.
- Phase 425: Antoine equation sub-atmospheric boiling, distillate purity, sludge conc.
- Phase 426: IACS M9 relief valve area, Beer-Lambert oil mist extinction, bearing hotspot.
- Master Facade & CLI commands.
Strictly < 175 LOC, zero mocks, zero fake data.
"""

from typer.testing import CliRunner

from src.core.maritime.phase_423_economizer_soot_wash_fire import (
    EconomizerSootWaterWashEngine,
    EconomizerSootTelemetry,
)
from src.core.maritime.phase_424_thermal_oil_heater_expansion import (
    ThermalOilHeaterExpansionEngine,
    ThermalOilTelemetry,
)
from src.core.maritime.phase_425_bilge_vacuum_evaporator import (
    BilgeVacuumEvaporatorEngine,
    BilgeVacuumEvaporatorTelemetry,
)
from src.core.maritime.phase_426_crankcase_relief_oil_mist import (
    CrankcaseReliefMistEngine,
    CrankcaseReliefMistTelemetry,
)
from src.core.maritime_soot_thermal_evap_crankcase_engine import (
    MaritimeSootThermalEvapCrankcaseEngine,
    MaritimePhases423to426Telemetry,
)
from src.cli.commands.maritime_soot_thermal_evap_crankcase_command import (
    economizer_app,
    thermal_oil_app,
    bilge_evap_app,
    crankcase_app,
)

runner = CliRunner()


def test_phase_423_economizer_kinetics_and_neutralization():
    engine = EconomizerSootWaterWashEngine()
    # Nominal
    t_nom = EconomizerSootTelemetry(differential_pressure_kpa=1.65, exhaust_gas_outlet_temp_c=175.0)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NORMAL_OPTIMAL"
    assert res_nom.emergency_soot_fire_trip is False
    assert res_nom.soot_fouling_index == 1.1

    # Thermal runaway trip (> 400°C)
    t_fire = EconomizerSootTelemetry(exhaust_gas_outlet_temp_c=415.0, temp_rise_rate_c_min=12.5)
    res_fire = engine.evaluate(t_fire)
    assert res_fire.emergency_soot_fire_trip is True
    assert res_fire.engine_slowdown_demanded is True
    assert res_fire.water_drenching_activated is True

    # Acidic wash neutralization dosing
    t_wash = EconomizerSootTelemetry(soot_wash_active=True, washwater_ph=2.5, washwater_flow_m3_h=10.0)
    res_wash = engine.evaluate(t_wash)
    assert res_wash.naoh_dosing_rate_l_h > 0.0


def test_phase_424_thermal_oil_film_and_reynolds():
    engine = ThermalOilHeaterExpansionEngine()
    # Nominal turbulent flow
    t_nom = ThermalOilTelemetry(flow_velocity_m_s=2.4, oil_kinematic_viscosity_cst=3.5)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NORMAL_OPTIMAL"
    assert res_nom.flow_turbulent is True
    assert res_nom.reynolds_number > 10000.0
    assert res_nom.burner_trip_demanded is False

    # Film temperature overheat (> 340°C)
    t_hot = ThermalOilTelemetry(heater_outlet_temp_c=310.0, heat_flux_kw_m2=60.0, heat_transfer_coeff_w_m2k=1000.0)
    res_hot = engine.evaluate(t_hot)
    assert res_hot.film_temperature_c == 370.0
    assert res_hot.film_temp_compliant is False
    assert res_hot.burner_trip_demanded is True

    # Expansion volume requirement check
    assert res_nom.required_expansion_volume_m3 > 0.5


def test_phase_425_bilge_vacuum_antoine_evaporation():
    engine = BilgeVacuumEvaporatorEngine()
    # Antoine boiling point calculation check at 0.15 bar abs
    t_boil = engine.calculate_boiling_point_c(0.15)
    assert 50.0 <= t_boil <= 60.0

    # Nominal evaluation
    t_nom = BilgeVacuumEvaporatorTelemetry(distillate_oil_ppm=2.1, sludge_concentrate_oil_pct=68.0)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "OPTIMAL_DISTILLATION"
    assert res_nom.overboard_discharge_permitted is True
    assert res_nom.distillate_purity_compliant is True

    # Foaming interlock
    t_foam = BilgeVacuumEvaporatorTelemetry(foam_detected=True)
    res_foam = engine.evaluate(t_foam)
    assert res_foam.anti_foam_demanded is True
    assert res_foam.overboard_discharge_permitted is False


def test_phase_426_crankcase_beer_lambert_omd_and_relief():
    engine = CrankcaseReliefMistEngine()
    # Nominal (I=98.0 -> mist ~0.27 mg/L)
    t_nom = CrankcaseReliefMistTelemetry(optical_intensity_i=98.0, optical_intensity_i0=100.0)
    res_nom = engine.evaluate(t_nom)
    assert res_nom.status == "NORMAL_OPTIMAL"
    assert res_nom.oil_mist_alarm is False
    assert res_nom.emergency_slowdown_trip is False
    assert res_nom.relief_area_compliant is True

    # Pre-alarm (I=90.0 -> mist ~1.4 mg/L)
    t_alarm = CrankcaseReliefMistTelemetry(optical_intensity_i=90.0, optical_intensity_i0=100.0)
    res_alarm = engine.evaluate(t_alarm)
    assert res_alarm.oil_mist_alarm is True
    assert res_alarm.status == "OIL_MIST_PRE_ALARM"

    # High optical extinction causing oil mist trip (>= 2.0 mg/L)
    t_trip = CrankcaseReliefMistTelemetry(optical_intensity_i=10.0, optical_intensity_i0=100.0)
    res_trip = engine.evaluate(t_trip)
    assert res_trip.oil_mist_concentration_mg_l >= 2.0
    assert res_trip.emergency_slowdown_trip is True
    assert res_trip.status == "EMERGENCY_SHUTDOWN_TRIP"

    # Bearing hotspot corroboration
    t_spot = CrankcaseReliefMistTelemetry(bearing_temperatures_c=(70.0, 70.0, 95.0))
    res_spot = engine.evaluate(t_spot)
    assert res_spot.hot_spot_bearing_detected is True


def test_master_facade_and_cli():
    facade = MaritimeSootThermalEvapCrankcaseEngine()
    t_all = MaritimePhases423to426Telemetry()
    res = facade.evaluate_all(t_all)
    assert res.overall_status == "NORMAL"
    assert res.all_systems_operational is True

    # Test CLI subcommands
    assert runner.invoke(economizer_app, ["--dp-kpa", "1.65"]).exit_code == 0
    assert runner.invoke(thermal_oil_app, ["--heater-outlet-c", "260.0"]).exit_code == 0
    assert runner.invoke(bilge_evap_app, ["--vac-bar", "0.15"]).exit_code == 0
    assert runner.invoke(crankcase_app, ["--volume-m3", "48.0"]).exit_code == 0
