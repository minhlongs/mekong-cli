"""Tests for Maritime Phases 459-462 Propulsion & Cargo Auxiliary Safety Systems.

Verifies:
- Phase 459: Ballast Tank Stripping Eductor & Venturi Vacuum
- Phase 460: Cargo Pump Room Gas Detection & Ventilation
- Phase 461: Controllable Pitch Propeller Emergency Pitch Locking
- Phase 462: Propulsion Intermediate Shaft Bearing Cooling
- Master Facade cross-system unified assessment
Strictly zero mocks, < 150 LOC.
"""

from src.core.maritime.phase_459_ballast_tank_stripping_eductor import (
    BallastTankStrippingEductorEngine,
    BallastEductorTelemetry,
    BallastEductorStatus,
)
from src.core.maritime.phase_460_cargo_pump_room_gas_detection import (
    CargoPumpRoomGasDetectionEngine,
    PumpRoomGasTelemetry,
    PumpRoomGasStatus,
)
from src.core.maritime.phase_461_controllable_pitch_propeller_emergency_pitch import (
    CppEmergencyPitchEngine,
    CppPitchTelemetry,
    CppEmergencyPitchStatus,
)
from src.core.maritime.phase_462_intermediate_shaft_bearing_cooling import (
    IntermediateShaftBearingEngine,
    ShaftBearingTelemetry,
    ShaftBearingStatus,
)
from src.core.maritime_ballast_eductor_pumproom_cpp_shaft_engine import (
    MaritimeAuxiliaryPropulsionMasterFacade,
)


def test_phase_459_ballast_tank_stripping_eductor():
    # Nominal stripping
    t_nominal = BallastEductorTelemetry(4.8, -0.85, 1.2, 3.0, 20.0)
    res_nominal = BallastTankStrippingEductorEngine.evaluate(t_nominal)
    assert res_nominal.status == BallastEductorStatus.NORMAL_STRIPPING
    assert res_nominal.effective_vacuum_adequate
    assert not res_nominal.safety_alarm

    # Insufficient drive pressure
    t_low = BallastEductorTelemetry(3.2, -0.40, 1.0, 2.0, 5.0)
    res_low = BallastTankStrippingEductorEngine.evaluate(t_low)
    assert res_low.status == BallastEductorStatus.INSUFFICIENT_DRIVE_PRESSURE
    assert res_low.safety_alarm

    # Stripped dry condition
    t_dry = BallastEductorTelemetry(5.0, -0.88, 1.0, 2.5, 0.8)
    res_dry = BallastTankStrippingEductorEngine.evaluate(t_dry)
    assert res_dry.status == BallastEductorStatus.SUCTION_LOSS_DRY
    assert res_dry.tank_stripped_dry


def test_phase_460_cargo_pump_room_gas_detection():
    # Safe condition
    t_safe = PumpRoomGasTelemetry(2.5, 0.5, 80.0, False, 25.0)
    res_safe = CargoPumpRoomGasDetectionEngine.evaluate(t_safe)
    assert res_safe.status == PumpRoomGasStatus.SAFE
    assert res_safe.gas_free
    assert not res_safe.pump_room_isolated

    # Critical LEL trip (22% LEL >= 20%)
    t_trip = PumpRoomGasTelemetry(22.0, 1.0, 80.0, False, 25.0)
    res_trip = CargoPumpRoomGasDetectionEngine.evaluate(t_trip)
    assert res_trip.status == PumpRoomGasStatus.LEL_CRITICAL_TRIP
    assert res_trip.pump_room_isolated
    assert res_trip.safety_alarm

    # Toxic H2S alarm (8.0 ppm >= 5 ppm)
    t_h2s = PumpRoomGasTelemetry(3.0, 8.0, 75.0, False, 20.0)
    res_h2s = CargoPumpRoomGasDetectionEngine.evaluate(t_h2s)
    assert res_h2s.status == PumpRoomGasStatus.TOXIC_H2S_ALARM
    assert res_h2s.safety_alarm


def test_phase_461_cpp_emergency_pitch():
    # Nominal pitch follow-up
    t_nom = CppPitchTelemetry(35.0, 15.0, 15.2, 15.1, False, False)
    res_nom = CppEmergencyPitchEngine.evaluate(t_nom)
    assert res_nom.status == CppEmergencyPitchStatus.NORMAL
    assert res_nom.pitch_tracking_acceptable

    # Servo oil pressure loss
    t_loss = CppPitchTelemetry(18.0, 15.0, 15.0, 15.0, False, False)
    res_loss = CppEmergencyPitchEngine.evaluate(t_loss)
    assert res_loss.status == CppEmergencyPitchStatus.SERVO_PRESSURE_LOSS
    assert res_loss.fail_as_is_engaged
    assert res_loss.safety_alarm

    # Emergency mechanical lock pin
    t_lock = CppPitchTelemetry(30.0, 15.0, 10.0, 10.0, True, False)
    res_lock = CppEmergencyPitchEngine.evaluate(t_lock)
    assert res_lock.status == CppEmergencyPitchStatus.EMERGENCY_MANUAL_LOCKED
    assert res_lock.fail_as_is_engaged


def test_phase_462_intermediate_shaft_bearing_cooling():
    # Nominal bearing
    t_nom = ShaftBearingTelemetry(54.0, 45.0, 25.0, True, 0.03)
    res_nom = IntermediateShaftBearingEngine.evaluate(t_nom)
    assert res_nom.status == ShaftBearingStatus.NORMAL
    assert not res_nom.engine_slowdown_required

    # Critical overheat (78°C >= 75°C)
    t_crit = ShaftBearingTelemetry(78.5, 68.0, 20.0, True, 0.04)
    res_crit = IntermediateShaftBearingEngine.evaluate(t_crit)
    assert res_crit.status == ShaftBearingStatus.BEARING_OVERHEAT_CRITICAL
    assert res_crit.engine_slowdown_required
    assert res_crit.safety_alarm

    # Oil ring stopped rotation
    t_ring = ShaftBearingTelemetry(58.0, 48.0, 20.0, False, 0.02)
    res_ring = IntermediateShaftBearingEngine.evaluate(t_ring)
    assert res_ring.status == ShaftBearingStatus.OIL_RING_STOPPED
    assert res_ring.engine_slowdown_required


def test_master_facade_all_clear():
    t_eductor = BallastEductorTelemetry(4.8, -0.85, 1.2, 3.0, 20.0)
    t_gas = PumpRoomGasTelemetry(2.5, 0.5, 80.0, False, 25.0)
    t_cpp = CppPitchTelemetry(35.0, 15.0, 15.2, 15.1, False, False)
    t_bearing = ShaftBearingTelemetry(54.0, 45.0, 25.0, True, 0.03)

    unified = MaritimeAuxiliaryPropulsionMasterFacade.evaluate_all(
        t_eductor, t_gas, t_cpp, t_bearing
    )
    assert unified.all_systems_nominal
    assert not unified.critical_shutdown_active
    d = unified.to_dict()
    assert d["all_systems_nominal"] is True
