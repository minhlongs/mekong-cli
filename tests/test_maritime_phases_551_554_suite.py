from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch23_command import maritime_aux23_app
from src.core.maritime.phase_551_cpp_controllable_pitch_propeller_servo_interlock import (
    CppPropellerServoEngine,
    CppPropellerServoState,
    CppPropellerServoTelemetry,
)
from src.core.maritime.phase_552_cargo_reliquefaction_boil_off_gcu_interlock import (
    CargoReliqBoilOffGcuEngine,
    CargoReliqBoilOffGcuState,
    CargoReliqBoilOffGcuTelemetry,
)
from src.core.maritime.phase_553_engine_room_local_water_mist_fwla_interlock import (
    EngineRoomLocalWaterMistFwlaEngine,
    LocalWaterMistFwlaState,
    LocalWaterMistFwlaTelemetry,
)
from src.core.maritime.phase_554_rudder_roll_fin_stabilizer_zero_speed_interlock import (
    FinStabilizerHousingEngine,
    FinStabilizerHousingState,
    FinStabilizerHousingTelemetry,
)
from src.core.maritime_safety_auxiliary_batch23_engine import MaritimeSafetyAuxiliaryBatch23Engine


def test_phase_551_cpp_controllable_pitch_propeller_servo_interlock() -> None:
    trip = CppPropellerServoEngine.evaluate(CppPropellerServoTelemetry(21.0, 60.0, 0.5))
    assert trip.state == CppPropellerServoState.HYDRAULIC_PRESSURE_LOSS_PITCH_FREEZE_TRIP
    assert trip.hydraulic_pitch_lock_valve_engage and trip.standby_servo_pump_start_cmd
    pre = CppPropellerServoEngine.evaluate(CppPropellerServoTelemetry(38.0, 58.0, 4.2))
    assert pre.state == CppPropellerServoState.SERVO_FEEDBACK_OR_STANDBY_PUMP_PRE_ALARM
    assert pre.standby_servo_pump_start_cmd


def test_phase_552_cargo_reliquefaction_boil_off_gcu_interlock() -> None:
    trip = CargoReliqBoilOffGcuEngine.evaluate(CargoReliqBoilOffGcuTelemetry(25.2, 110.0))
    assert trip.state == CargoReliqBoilOffGcuState.TANK_OVERPRESSURE_OR_GCU_FLAME_FAIL_TRIP
    assert trip.gcu_free_flow_valve_open_cmd and trip.emergency_mast_riser_prv_armed
    gcu = CargoReliqBoilOffGcuEngine.evaluate(CargoReliqBoilOffGcuTelemetry(19.5, 102.0))
    assert gcu.state == CargoReliqBoilOffGcuState.GCU_AUTO_THERMAL_OXIDATION_CUTIN
    assert gcu.gcu_free_flow_valve_open_cmd


def test_phase_553_engine_room_local_water_mist_fwla_interlock() -> None:
    coinc = EngineRoomLocalWaterMistFwlaEngine.evaluate(
        LocalWaterMistFwlaTelemetry(True, True, 6.5, False)
    )
    assert coinc.state == LocalWaterMistFwlaState.COINCIDENCE_HOTSPOT_MIST_DISCHARGE_TRIP
    assert coinc.section_deluge_valve_open_cmd and coinc.local_fuel_booster_trip_cmd
    single = EngineRoomLocalWaterMistFwlaEngine.evaluate(
        LocalWaterMistFwlaTelemetry(False, True, 6.5, False)
    )
    assert single.state == LocalWaterMistFwlaState.SINGLE_DETECTOR_PRE_ALARM_STANDBY
    assert not single.section_deluge_valve_open_cmd


def test_phase_554_rudder_roll_fin_stabilizer_zero_speed_interlock() -> None:
    retract = FinStabilizerHousingEngine.evaluate(FinStabilizerHousingTelemetry(2.8, 135.0))
    assert retract.state == FinStabilizerHousingState.LOW_SPEED_OR_HYDRAULIC_AUTO_RETRACT_TRIP
    assert retract.auto_center_zero_angle_cmd and retract.retract_fin_to_housing_cmd
    pin_fault = FinStabilizerHousingEngine.evaluate(
        FinStabilizerHousingTelemetry(12.0, 140.0, 50.0, False)
    )
    assert pin_fault.state == FinStabilizerHousingState.LOCKING_PIN_PROXIMITY_INTERLOCK_FAULT


def test_batch23_coordinator_and_cli() -> None:
    batch = MaritimeSafetyAuxiliaryBatch23Engine.evaluate_batch(
        CppPropellerServoTelemetry(42.0, 54.0, 0.3),
        CargoReliqBoilOffGcuTelemetry(11.5, 95.0, -125.0, True),
        LocalWaterMistFwlaTelemetry(False, False, 6.5, False),
        FinStabilizerHousingTelemetry(14.5, 140.0, 55.0, True),
    )
    assert not batch.any_critical_interlock_active
    runner = CliRunner()
    assert runner.invoke(maritime_aux23_app, ["cpp-check"]).exit_code == 0
    assert runner.invoke(maritime_aux23_app, ["finstab-check", "--speed-kn", "2.5"]).exit_code == 0
