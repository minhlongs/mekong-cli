"""Unit tests for Maritime Automation Phases 455-458 Suite.

Covers:
- Phase 455: Crankcase Explosion Relief Valve & Quenching Mesh
- Phase 456: Boiler Feedwater Deaerator & Scavenging Reserve
- Phase 457: Marine Fuel Oil Homogenizer Ultrasonic Viscosity
- Phase 458: Reefer Container Socket Protection & Earth Faults
- Master Facade: MaritimeCrankcaseDeaeratorHomogenizerReeferEngine
Zero mocks, strictly deterministic physics validation.
"""

from src.core.maritime.phase_455_crankcase_explosion_relief_valve import (
    CrankcaseExplosionReliefEngine,
    CrankcaseValveTelemetry,
    CrankcaseValveStatus,
)
from src.core.maritime.phase_456_boiler_feedwater_deaerator import (
    BoilerFeedwaterDeaeratorEngine,
    DeaeratorTelemetry,
    DeaeratorStatus,
)
from src.core.maritime.phase_457_fuel_oil_homogenizer_viscosity import (
    FuelHomogenizerViscosityEngine,
    FuelHomogenizerTelemetry,
    FuelHomogenizerStatus,
)
from src.core.maritime.phase_458_reefer_container_socket_protection import (
    ReeferContainerSocketEngine,
    ReeferSocketTelemetry,
    ReeferSocketStatus,
)
from src.core.maritime_crankcase_deaerator_homogenizer_reefer_engine import (
    MaritimeCrankcaseDeaeratorHomogenizerReeferEngine,
)


def test_phase_455_crankcase_explosion_relief_nominal_and_trip() -> None:
    nom_tel = CrankcaseValveTelemetry(0.04, 0.0, True, 92.0, 45.0)
    res_nom = CrankcaseExplosionReliefEngine.evaluate(nom_tel)
    assert res_nom.status == CrankcaseValveStatus.NORMAL
    assert not res_nom.safety_alarm
    assert res_nom.flame_quenched

    # Active venting with successful re-seating
    vent_tel = CrankcaseValveTelemetry(0.25, 12.0, True, 90.0, 110.0)
    res_vent = CrankcaseExplosionReliefEngine.evaluate(vent_tel)
    assert res_vent.status == CrankcaseValveStatus.RELIEF_ACTIVE
    assert res_vent.explosion_relief_active
    assert not res_vent.air_ingress_hazard

    # Ingress hazard if failed to re-seat
    fail_tel = CrankcaseValveTelemetry(0.25, 12.0, False, 90.0, 110.0)
    res_fail = CrankcaseExplosionReliefEngine.evaluate(fail_tel)
    assert res_fail.status == CrankcaseValveStatus.AIR_INGRESS_HAZARD
    assert res_fail.air_ingress_hazard
    assert res_fail.safety_alarm

    # Critical explosion > 0.50 bar
    crit_tel = CrankcaseValveTelemetry(0.65, 25.0, False, 80.0, 220.0)
    res_crit = CrankcaseExplosionReliefEngine.evaluate(crit_tel)
    assert res_crit.status == CrankcaseValveStatus.CRITICAL_EXPLOSION
    assert res_crit.safety_alarm


def test_phase_456_boiler_feedwater_deaerator() -> None:
    nom_tel = DeaeratorTelemetry(0.4, 109.0, 4.5, 22.0, 65.0)
    res_nom = BoilerFeedwaterDeaeratorEngine.evaluate(nom_tel)
    assert res_nom.status == DeaeratorStatus.OPTIMAL
    assert res_nom.thermal_saturation_compliant
    assert not res_nom.oxygen_corrosion_risk

    # High dissolved oxygen
    o2_tel = DeaeratorTelemetry(0.4, 109.0, 12.0, 22.0, 65.0)
    res_o2 = BoilerFeedwaterDeaeratorEngine.evaluate(o2_tel)
    assert res_o2.status == DeaeratorStatus.OXYGEN_CORROSION_RISK
    assert res_o2.oxygen_corrosion_risk
    assert res_o2.chemical_dosing_required
    assert res_o2.safety_alarm

    # Low storage tank level trip
    lvl_tel = DeaeratorTelemetry(0.4, 109.0, 4.5, 22.0, 15.0)
    res_lvl = BoilerFeedwaterDeaeratorEngine.evaluate(lvl_tel)
    assert res_lvl.status == DeaeratorStatus.TRIP_LEVEL
    assert res_lvl.storage_level_alarm


def test_phase_457_fuel_oil_homogenizer() -> None:
    nom_tel = FuelHomogenizerTelemetry(25.0, 3.2, 12.8, 8.0, 130.0)
    res_nom = FuelHomogenizerViscosityEngine.evaluate(nom_tel)
    assert res_nom.status == FuelHomogenizerStatus.OPTIMAL
    assert res_nom.cavitation_efficient
    assert res_nom.viscosity_in_spec
    assert not res_nom.safety_alarm

    # Low booster pressure -> vapor lock trip
    p_tel = FuelHomogenizerTelemetry(25.0, 3.2, 12.8, 4.5, 130.0)
    res_p = FuelHomogenizerViscosityEngine.evaluate(p_tel)
    assert res_p.status == FuelHomogenizerStatus.FLASH_OFF_VAPOR_LOCK_TRIP
    assert not res_p.vapor_lock_prevented
    assert res_p.safety_alarm

    # Viscosity out of bounds
    visc_tel = FuelHomogenizerTelemetry(25.0, 3.2, 18.5, 8.0, 110.0)
    res_visc = FuelHomogenizerViscosityEngine.evaluate(visc_tel)
    assert res_visc.status == FuelHomogenizerStatus.VISCOSITY_OUT_OF_BOUNDS
    assert res_visc.safety_alarm


def test_phase_458_reefer_container_socket() -> None:
    nom_tel = ReeferSocketTelemetry(440.0, 20.0, 4.0, 50.0, True, True)
    res_nom = ReeferContainerSocketEngine.evaluate(nom_tel)
    assert res_nom.status == ReeferSocketStatus.NORMAL
    assert res_nom.safe_to_operate
    assert not res_nom.breaker_tripped

    # Mechanical interlock violation (engaged without plug)
    intl_tel = ReeferSocketTelemetry(440.0, 0.0, 0.0, 25.0, True, False)
    res_intl = ReeferContainerSocketEngine.evaluate(intl_tel)
    assert res_intl.status == ReeferSocketStatus.INTERLOCK_VIOLATION
    assert res_intl.breaker_tripped
    assert res_intl.safety_alarm

    # Earth leakage >= 30 mA RCD trip
    rcd_tel = ReeferSocketTelemetry(440.0, 20.0, 35.0, 50.0, True, True)
    res_rcd = ReeferContainerSocketEngine.evaluate(rcd_tel)
    assert res_rcd.status == ReeferSocketStatus.EARTH_FAULT_TRIP
    assert res_rcd.earth_fault_detected
    assert res_rcd.breaker_tripped


def test_master_facade_all_clear() -> None:
    crank_tel = CrankcaseValveTelemetry(0.04, 0.0, True, 92.0, 45.0)
    deaer_tel = DeaeratorTelemetry(0.4, 109.0, 4.5, 22.0, 65.0)
    homog_tel = FuelHomogenizerTelemetry(25.0, 3.2, 12.8, 8.0, 130.0)
    reefer_tel = ReeferSocketTelemetry(440.0, 20.0, 4.0, 50.0, True, True)

    assessment = MaritimeCrankcaseDeaeratorHomogenizerReeferEngine.evaluate_all(
        crank_tel, deaer_tel, homog_tel, reefer_tel
    )
    assert assessment.overall_all_clear
    d = assessment.to_dict()
    assert d["crankcase_valve_status"] == "NORMAL"
    assert d["deaerator_status"] == "OPTIMAL"
    assert d["fuel_homogenizer_status"] == "OPTIMAL"
    assert d["reefer_socket_status"] == "NORMAL"
