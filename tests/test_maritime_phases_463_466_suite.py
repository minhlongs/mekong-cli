"""Unit and integration test suite for Maritime Automation Phases 463-466.

Covers:
- Phase 463: Stern Tube Gravity Tank (IACS UR M56)
- Phase 464: Inert Gas Deck Water Seal (SOLAS II-2 Reg 4.5.5)
- Phase 465: Scavenge Air Receiver Fire Protection (SOLAS II-2 Reg 10.5)
- Phase 466: Fresh Water Generator Salinometer (MARPOL & DNV Rules)
- Master Facade: MaritimeSafetyAuxiliaryMasterEngine
Strictly zero mocks, < 150 LOC.
"""

import pytest

from src.core.maritime.phase_463_stern_tube_gravity_tank import (
    SternTubeGravityTankEngine,
    SternTubeGravityTelemetry,
    SternTubeGravityStatus,
)
from src.core.maritime.phase_464_deck_water_seal_inert_gas import (
    DeckWaterSealEngine,
    DeckWaterSealTelemetry,
    DeckWaterSealStatus,
)
from src.core.maritime.phase_465_main_engine_scavenge_air_fire import (
    ScavengeAirFireEngine,
    ScavengeFireTelemetry,
    ScavengeFireStatus,
)
from src.core.maritime.phase_466_fresh_water_generator_salinometer import (
    FreshWaterGeneratorEngine,
    FwgSalinometerTelemetry,
    FwgSalinometerStatus,
)
from src.core.maritime_safety_auxiliary_master_engine import (
    MaritimeSafetyAuxiliaryMasterEngine,
)


def test_phase_463_stern_tube_gravity_tank():
    normal_telem = SternTubeGravityTelemetry(55.0, 45.0, 0.25, 0.01, True)
    assessment = SternTubeGravityTankEngine.evaluate(normal_telem)
    assert assessment.status == SternTubeGravityStatus.NORMAL
    assert assessment.hydrostatic_head_adequate is True
    assert assessment.seal_protection_intact is True

    water_telem = SternTubeGravityTelemetry(55.0, 45.0, 0.25, 0.12, True)
    water_res = SternTubeGravityTankEngine.evaluate(water_telem)
    assert water_res.status == SternTubeGravityStatus.WATER_CONTAMINATION
    assert water_res.water_ingress_detected is True

    low_level_telem = SternTubeGravityTelemetry(20.0, 45.0, 0.20, 0.01, True)
    low_res = SternTubeGravityTankEngine.evaluate(low_level_telem)
    assert low_res.status == SternTubeGravityStatus.LEVEL_CRITICAL_TRIP
    assert low_res.emergency_pump_triggered is True


def test_phase_464_deck_water_seal():
    normal_telem = DeckWaterSealTelemetry(500.0, 12.0, 18.0, 5.0, False)
    assessment = DeckWaterSealEngine.evaluate(normal_telem)
    assert assessment.status == DeckWaterSealStatus.NORMAL
    assert assessment.seal_integrity_intact is True
    assert assessment.backflow_risk is False

    gas_telem = DeckWaterSealTelemetry(500.0, 12.0, 18.0, 120.0, False)
    gas_res = DeckWaterSealEngine.evaluate(gas_telem)
    assert gas_res.status == DeckWaterSealStatus.GAS_BACKFLOW_DETECTED
    assert gas_res.trip_ig_plant_required is True

    low_water_telem = DeckWaterSealTelemetry(350.0, 12.0, 18.0, 10.0, False)
    low_res = DeckWaterSealEngine.evaluate(low_water_telem)
    assert low_res.status == DeckWaterSealStatus.SEAL_WATER_LOW
    assert low_res.trip_ig_plant_required is True


def test_phase_465_main_engine_scavenge_air_fire():
    normal_telem = ScavengeFireTelemetry(45.0, 2.3, True, 85.0, False)
    assessment = ScavengeAirFireEngine.evaluate(normal_telem)
    assert assessment.status == ScavengeFireStatus.NORMAL
    assert assessment.fire_detected is False

    fire_telem = ScavengeFireTelemetry(135.0, 2.1, True, 15.0, True)
    fire_res = ScavengeAirFireEngine.evaluate(fire_telem)
    assert fire_res.status == ScavengeFireStatus.CO2_RELEASE_ARMED
    assert fire_res.fire_detected is True
    assert fire_res.engine_slowdown_required is True
    assert fire_res.co2_injection_permissible is True


def test_phase_466_fresh_water_generator_salinometer():
    normal_telem = FwgSalinometerTelemetry(3.5, 92.0, 80.0, 28.0, False)
    assessment = FreshWaterGeneratorEngine.evaluate(normal_telem)
    assert assessment.status == FwgSalinometerStatus.NORMAL
    assert assessment.distillate_fit_for_potable_tank is True

    saline_telem = FwgSalinometerTelemetry(18.0, 92.0, 80.0, 28.0, True)
    saline_res = FreshWaterGeneratorEngine.evaluate(saline_telem)
    assert saline_res.status == FwgSalinometerStatus.SALINITY_HIGH_DUMPING
    assert saline_res.dump_valve_energized is True

    loss_vac_telem = FwgSalinometerTelemetry(3.5, 75.0, 80.0, 10.0, False)
    vac_res = FreshWaterGeneratorEngine.evaluate(loss_vac_telem)
    assert vac_res.status == FwgSalinometerStatus.VACUUM_INSUFFICIENT


def test_master_maritime_safety_auxiliary_facade():
    stern = SternTubeGravityTelemetry(55.0, 45.0, 0.25, 0.01, True)
    seal = DeckWaterSealTelemetry(500.0, 12.0, 18.0, 5.0, False)
    scavenge = ScavengeFireTelemetry(45.0, 2.3, True, 85.0, False)
    fwg = FwgSalinometerTelemetry(3.5, 92.0, 80.0, 28.0, False)

    master_res = MaritimeSafetyAuxiliaryMasterEngine.evaluate_all(stern, seal, scavenge, fwg)
    assert master_res.overall_safety_interlock_ok is True
    assert master_res.engine_slowdown_tripped is False
