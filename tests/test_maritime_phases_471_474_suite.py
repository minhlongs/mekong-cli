"""Unit & Integration Tests for Maritime Automation Phases 471-474.

Covers:
- Phase 471: Tunnel Bow Thruster Hydraulic Pitch & Prime Mover Interlock
- Phase 472: Emergency Fire Pump Sea Suction Priming & Head Protection
- Phase 473: Engine Crankcase Oil Mist Optical Detector & Auto Slowdown
- Phase 474: Scrubber Washwater Effluent pH & PAH Environmental Safety
- Master Coordinator: MaritimeSafetyAuxiliaryBatch3Engine

Strictly zero mocks, < 140 LOC.
"""

import pytest

from src.core.maritime.phase_471_bow_thruster_interlock import (
    BowThrusterInterlockEngine,
    BowThrusterStatus,
    BowThrusterTelemetry,
)
from src.core.maritime.phase_472_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpSafetyEngine,
    EmergencyFirePumpStatus,
    EmergencyFirePumpTelemetry,
)
from src.core.maritime.phase_473_crankcase_oil_mist_optical_detector import (
    OilMistDetectorEngine,
    OilMistStatus,
    OilMistTelemetry,
)
from src.core.maritime.phase_474_scrubber_effluent_ph_polycyclic_aromatic import (
    ScrubberEffluentSafetyEngine,
    ScrubberEffluentStatus,
    ScrubberEffluentTelemetry,
)
from src.core.maritime_safety_auxiliary_batch3_engine import (
    MaritimePhases471to474Telemetry,
    MaritimeSafetyAuxiliaryBatch3Engine,
)


def test_phase_471_bow_thruster_interlock():
    # Normal operation
    normal_telem = BowThrusterTelemetry(55.0, 60.0, 70.0, 80.0, 0.15, True)
    res_normal = BowThrusterInterlockEngine.evaluate(normal_telem)
    assert res_normal.status == BowThrusterStatus.NORMAL
    assert res_normal.allowed_pitch_pct == 80.0
    assert res_normal.thruster_run_permissive is True

    # Low header tank level trip (level <= 25%)
    low_level_telem = BowThrusterTelemetry(55.0, 20.0, 70.0, 80.0, 0.15, True)
    res_low_level = BowThrusterInterlockEngine.evaluate(low_level_telem)
    assert res_low_level.status == BowThrusterStatus.LOW_HEADER_LEVEL_TRIP
    assert res_low_level.thruster_run_permissive is False

    # Generator overload pitch reduction (load >= 90%)
    gen_overload_telem = BowThrusterTelemetry(55.0, 60.0, 92.0, 85.0, 0.15, True)
    res_gen = BowThrusterInterlockEngine.evaluate(gen_overload_telem)
    assert res_gen.status == BowThrusterStatus.GENERATOR_OVERLOAD_PITCH_REDUCTION
    assert res_gen.allowed_pitch_pct == 50.0


def test_phase_472_emergency_fire_pump_sea_suction():
    # Standby normal
    standby_telem = EmergencyFirePumpTelemetry(3.2, 0.0, 0.0, 0.0, 24.0, False)
    res_standby = EmergencyFirePumpSafetyEngine.evaluate(standby_telem)
    assert res_standby.status == EmergencyFirePumpStatus.NORMAL
    assert res_standby.sea_suction_permissive is True

    # Suction head exceeded (> 4.5 m)
    excess_head_telem = EmergencyFirePumpTelemetry(4.8, 0.0, 0.0, 0.0, 24.0, False)
    res_head = EmergencyFirePumpSafetyEngine.evaluate(excess_head_telem)
    assert res_head.status == EmergencyFirePumpStatus.SUCTION_HEAD_EXCEEDED
    assert res_head.sea_suction_permissive is False

    # Priming timed out (> 45s while pressure < 2.7 bar)
    timeout_telem = EmergencyFirePumpTelemetry(3.2, -0.3, 48.0, 1.2, 24.0, True)
    res_timeout = EmergencyFirePumpSafetyEngine.evaluate(timeout_telem)
    assert res_timeout.status == EmergencyFirePumpStatus.PRIMING_TIMEOUT_TRIP
    assert res_timeout.reprime_command_active is False


def test_phase_473_crankcase_oil_mist_optical_detector():
    # Normal operation
    normal_telem = OilMistTelemetry(0.4, 3.0, 95.0, True, True)
    res_normal = OilMistDetectorEngine.evaluate(normal_telem)
    assert res_normal.status == OilMistStatus.NORMAL
    assert res_normal.engine_slowdown_tripped is False

    # High mist trip (mist >= 2.0 mg/L)
    trip_telem = OilMistTelemetry(2.3, 3.0, 95.0, True, True)
    res_trip = OilMistDetectorEngine.evaluate(trip_telem)
    assert res_trip.status == OilMistStatus.HIGH_MIST_SLOWDOWN_TRIP
    assert res_trip.engine_slowdown_tripped is True
    assert res_trip.crankcase_door_open_permitted is False

    # Dirty lens warning (obscuration >= 15%)
    dirty_telem = OilMistTelemetry(0.4, 16.5, 95.0, True, True)
    res_dirty = OilMistDetectorEngine.evaluate(dirty_telem)
    assert res_dirty.status == OilMistStatus.OPTICAL_LENS_DIRTY
    assert res_dirty.optical_service_required is True


def test_phase_474_scrubber_effluent_ph_polycyclic_aromatic():
    # Normal compliant
    normal_telem = ScrubberEffluentTelemetry(7.2, 12.0, 8.0, 15.0, False, True)
    res_normal = ScrubberEffluentSafetyEngine.evaluate(normal_telem)
    assert res_normal.status == ScrubberEffluentStatus.NORMAL
    assert res_normal.overboard_discharge_permitted is True

    # Acidic washwater trip (pH < 6.5)
    acidic_telem = ScrubberEffluentTelemetry(5.8, 12.0, 8.0, 15.0, False, True)
    res_acidic = ScrubberEffluentSafetyEngine.evaluate(acidic_telem)
    assert res_acidic.status == ScrubberEffluentStatus.LOW_PH_ALARM
    assert res_acidic.overboard_discharge_permitted is False
    assert res_acidic.holding_tank_diversion_valve_open is True


def test_master_maritime_auxiliary_batch3_engine():
    telem = MaritimePhases471to474Telemetry(
        bow_thruster=BowThrusterTelemetry(55.0, 60.0, 70.0, 80.0, 0.15, True),
        emergency_fire_pump=EmergencyFirePumpTelemetry(3.2, -0.65, 20.0, 4.5, 24.0, True),
        oil_mist=OilMistTelemetry(0.4, 3.0, 95.0, True, True),
        scrubber_effluent=ScrubberEffluentTelemetry(7.2, 12.0, 8.0, 15.0, False, True),
    )
    res = MaritimeSafetyAuxiliaryBatch3Engine.evaluate(telem)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
