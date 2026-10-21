"""Zero-mock unit test suite for Maritime Automation Phases 451-454.

Tests:
- Phase 451: EGR Water Treatment System & Centrifuge (MEPC.307(73))
- Phase 452: Cargo Tank High-Velocity P/V Valve (ISO 15364 / IMO MSC/Circ.677)
- Phase 453: Marine Sewage Vacuum Collection System (ISO 15749)
- Phase 454: Waste Heat Recovery ORC Evaporator Safety (IACS UR M53)
- Master Facade: MaritimeEgrPvVacuumOrcEngine
"""

import pytest

from src.core.maritime.phase_451_egr_water_treatment_system import (
    EgrWaterTreatmentEngine,
    EgrWtsTelemetry,
    EgrWtsStatus,
)
from src.core.maritime.phase_452_cargo_tank_high_velocity_pv_valve import (
    CargoPvValveEngine,
    PvValveTelemetry,
    PvValveStatus,
)
from src.core.maritime.phase_453_marine_sewage_vacuum_collection import (
    SewageVacuumSystemEngine,
    SewageVacuumTelemetry,
    SewageVacuumStatus,
)
from src.core.maritime.phase_454_waste_heat_recovery_orc_evaporator import (
    WhrOrcEvaporatorEngine,
    OrcEvaporatorTelemetry,
    OrcEvaporatorStatus,
)
from src.core.maritime_egr_pv_vacuum_orc_engine import MaritimeEgrPvVacuumOrcEngine


def test_phase_451_egr_water_treatment_nominal_and_trip():
    nominal = EgrWtsTelemetry(
        ph_level=7.8,
        turbidity_fnu=10.0,
        pah_ppb=18.0,
        centrifuge_sep_eff_pct=96.0,
        sludge_tank_capacity_pct=40.0,
    )
    res_nom = EgrWaterTreatmentEngine.evaluate(nominal)
    assert res_nom.status == EgrWtsStatus.OPTIMAL
    assert res_nom.overboard_discharge_permitted is True

    # Acidic discharge violation
    acidic = EgrWtsTelemetry(
        ph_level=6.1,
        turbidity_fnu=12.0,
        pah_ppb=20.0,
        centrifuge_sep_eff_pct=95.0,
        sludge_tank_capacity_pct=45.0,
    )
    res_acid = EgrWaterTreatmentEngine.evaluate(acidic)
    assert res_acid.status == EgrWtsStatus.DISCHARGE_PROHIBITED
    assert res_acid.recirculation_required is True

    # Sludge high level trip
    full_sludge = EgrWtsTelemetry(
        ph_level=7.5,
        turbidity_fnu=10.0,
        pah_ppb=15.0,
        centrifuge_sep_eff_pct=95.0,
        sludge_tank_capacity_pct=88.0,
    )
    res_trip = EgrWaterTreatmentEngine.evaluate(full_sludge)
    assert res_trip.status == EgrWtsStatus.EMERGENCY_SHUTDOWN
    assert res_trip.sludge_holding_alarm is True


def test_phase_452_cargo_tank_pv_valve_operation():
    # Normal closed state
    normal = PvValveTelemetry(
        tank_pressure_kpa=4.0,
        efflux_velocity_m_s=0.0,
        flame_screen_mesh_clear_pct=95.0,
        magnetic_lift_verified=True,
        disc_lift_percentage=0.0,
    )
    res_norm = CargoPvValveEngine.evaluate(normal)
    assert res_norm.status == PvValveStatus.NORMAL_CLOSED
    assert res_norm.safety_alarm is False

    # High-velocity venting
    overpressure = PvValveTelemetry(
        tank_pressure_kpa=15.2,
        efflux_velocity_m_s=36.0,
        flame_screen_mesh_clear_pct=92.0,
        magnetic_lift_verified=True,
        disc_lift_percentage=85.0,
    )
    res_vent = CargoPvValveEngine.evaluate(overpressure)
    assert res_vent.status == PvValveStatus.ACTIVE_VENTING
    assert res_vent.efflux_compliant is True

    # Sticking disc detected by magnetic check lift
    stuck = PvValveTelemetry(
        tank_pressure_kpa=16.0,
        efflux_velocity_m_s=10.0,
        flame_screen_mesh_clear_pct=90.0,
        magnetic_lift_verified=False,
        disc_lift_percentage=10.0,
    )
    res_stuck = CargoPvValveEngine.evaluate(stuck)
    assert res_stuck.status == PvValveStatus.VALVE_STUCK_ALARM
    assert res_stuck.safety_alarm is True


def test_phase_453_marine_sewage_vacuum_collection():
    # Vacuum nominal operation
    nominal = SewageVacuumTelemetry(
        vacuum_pressure_kpa=-52.0,
        buffer_tank_level_pct=35.0,
        ejector_motive_pressure_bar=3.0,
        distance_to_shore_nm=18.0,
    )
    res_nom = SewageVacuumSystemEngine.evaluate(nominal)
    assert res_nom.status == SewageVacuumStatus.NORMAL
    assert res_nom.vacuum_pump_call is False
    assert res_nom.discharge_valve_open is True

    # High buffer tank level lockout
    high_level = SewageVacuumTelemetry(
        vacuum_pressure_kpa=-45.0,
        buffer_tank_level_pct=85.0,
        ejector_motive_pressure_bar=3.0,
        distance_to_shore_nm=20.0,
    )
    res_hl = SewageVacuumSystemEngine.evaluate(high_level)
    assert res_hl.status == SewageVacuumStatus.TANK_HIGH_LEVEL_LOCKOUT
    assert res_hl.alarm_active is True

    # Coastal zone discharge lock (< 12 nm)
    coastal = SewageVacuumTelemetry(
        vacuum_pressure_kpa=-55.0,
        buffer_tank_level_pct=50.0,
        ejector_motive_pressure_bar=3.0,
        distance_to_shore_nm=8.5,
    )
    res_coast = SewageVacuumSystemEngine.evaluate(coastal)
    assert res_coast.status == SewageVacuumStatus.SHORE_PROXIMITY_LOCK
    assert res_coast.discharge_valve_open is False


def test_phase_454_waste_heat_recovery_orc_evaporator():
    nominal = OrcEvaporatorTelemetry(
        film_temp_celsius=255.0,
        superheat_margin_celsius=24.0,
        exhaust_diverter_open_pct=100.0,
        hydrocarbon_leak_detected=False,
        expander_inlet_pressure_bar=20.0,
    )
    res_nom = WhrOrcEvaporatorEngine.evaluate(nominal)
    assert res_nom.status == OrcEvaporatorStatus.NORMAL
    assert res_nom.safety_alarm is False

    # Flammable vapor leak in exhaust uptake
    leak = OrcEvaporatorTelemetry(
        film_temp_celsius=250.0,
        superheat_margin_celsius=20.0,
        exhaust_diverter_open_pct=100.0,
        hydrocarbon_leak_detected=True,
        expander_inlet_pressure_bar=18.0,
    )
    res_leak = WhrOrcEvaporatorEngine.evaluate(leak)
    assert res_leak.status == OrcEvaporatorStatus.FLAMMABLE_LEAK_ALARM
    assert res_leak.diverter_bypass_tripped is True
    assert res_leak.working_fluid_pump_trip is True

    # Extreme film temperature trip
    overheat = OrcEvaporatorTelemetry(
        film_temp_celsius=310.0,
        superheat_margin_celsius=30.0,
        exhaust_diverter_open_pct=100.0,
        hydrocarbon_leak_detected=False,
        expander_inlet_pressure_bar=22.0,
    )
    res_hot = WhrOrcEvaporatorEngine.evaluate(overheat)
    assert res_hot.status == OrcEvaporatorStatus.EMERGENCY_DAMPER_TRIP
    assert res_hot.diverter_bypass_tripped is True


def test_master_facade_all_clear():
    egr = EgrWtsTelemetry(7.4, 12.0, 20.0, 95.0, 30.0)
    pv = PvValveTelemetry(3.0, 0.0, 90.0, True, 0.0)
    sewage = SewageVacuumTelemetry(-50.0, 40.0, 3.0, 16.0)
    orc = OrcEvaporatorTelemetry(240.0, 25.0, 100.0, False, 18.0)

    facade_res = MaritimeEgrPvVacuumOrcEngine.evaluate_all(egr, pv, sewage, orc)
    assert facade_res.overall_all_clear is True
    d = facade_res.to_dict()
    assert d["overall_all_clear"] is True
