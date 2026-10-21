from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime.phase_535_exhaust_valve_actuator_supervision import (
    ExhaustValveActuatorState, ExhaustValveActuatorSupervisionEngine, ExhaustValveActuatorTelemetry,
)
from src.core.maritime.phase_536_cargo_pumproom_vent_gas_interlock import (
    CargoPumproomState, CargoPumproomTelemetry, CargoPumproomVentGasInterlockEngine,
)
from src.core.maritime.phase_537_hull_stress_slamming_monitor import (
    HullStressSlammingMonitorEngine, HullStressSlammingState, HullStressSlammingTelemetry,
)
from src.core.maritime.phase_538_helideck_jp5_refueling_interlock import (
    HelideckJp5RefuelingInterlockEngine, HelideckRefuelingState, HelideckRefuelingTelemetry,
)
from src.core.maritime_safety_auxiliary_batch19_engine import MaritimeSafetyAuxiliaryBatch19Engine

runner = CliRunner()


def test_phase_535_exhaust_valve_actuator_supervision() -> None:
    ok = ExhaustValveActuatorSupervisionEngine.evaluate(ExhaustValveActuatorTelemetry(7.2, 12.0, 0.2, 75.0))
    assert ok.state == ExhaustValveActuatorState.OPTIMAL_ACTUATOR_OPERATION
    collapse = ExhaustValveActuatorSupervisionEngine.evaluate(ExhaustValveActuatorTelemetry(4.6, 10.0, 0.4, 80.0))
    assert collapse.state == ExhaustValveActuatorState.AIR_SPRING_COLLAPSE_CYLINDER_CUTOUT
    assert collapse.cylinder_fuel_cutout_cmd is True
    seize = ExhaustValveActuatorSupervisionEngine.evaluate(ExhaustValveActuatorTelemetry(7.0, 1.0, 0.3, 75.0))
    assert seize.state == ExhaustValveActuatorState.SPINDLE_ROTATION_SEIZURE_ALARM


def test_phase_536_cargo_pumproom_vent_gas_interlock() -> None:
    ok = CargoPumproomVentGasInterlockEngine.evaluate(CargoPumproomTelemetry(24.0, 1.5, 54.0, 60.0))
    assert ok.state == CargoPumproomState.SAFE_PUMPROOM_OPERATING
    trip = CargoPumproomVentGasInterlockEngine.evaluate(CargoPumproomTelemetry(22.0, 32.0, 62.0, 80.0))
    assert trip.state == CargoPumproomState.EMERGENCY_COP_SHUTDOWN_TRIP
    assert trip.cargo_oil_pump_trip_cmd is True


def test_phase_537_hull_stress_slamming_monitor() -> None:
    ok = HullStressSlammingMonitorEngine.evaluate(HullStressSlammingTelemetry(120.0, 175.0, 0, 0.15))
    assert ok.state == HullStressSlammingState.NOMINAL_HULL_GIRDER_LOAD
    slam = HullStressSlammingMonitorEngine.evaluate(HullStressSlammingTelemetry(140.0, 175.0, 5, 0.52))
    assert slam.state == HullStressSlammingState.BOW_SLAMMING_SPEED_REDUCTION_ADVICE
    assert slam.speed_course_alteration_required is True


def test_phase_538_helideck_jp5_refueling_interlock() -> None:
    ok = HelideckJp5RefuelingInterlockEngine.evaluate(HelideckRefuelingTelemetry(2.5, 4.0, 0.35, True))
    assert ok.state == HelideckRefuelingState.JP5_DISPENSING_AUTHORIZED
    assert ok.fuel_solenoid_valve_open is True
    water = HelideckJp5RefuelingInterlockEngine.evaluate(HelideckRefuelingTelemetry(2.5, 18.0, 0.40, True))
    assert water.state == HelideckRefuelingState.FREE_WATER_CONTAMINATION_SHUTOFF
    assert water.fuel_solenoid_valve_open is False


def test_batch19_coordinator_engine() -> None:
    res = MaritimeSafetyAuxiliaryBatch19Engine.evaluate_batch19(
        ExhaustValveActuatorTelemetry(7.2, 12.0, 0.2, 75.0),
        CargoPumproomTelemetry(24.0, 1.5, 54.0, 60.0),
        HullStressSlammingTelemetry(120.0, 175.0, 0, 0.15),
        HelideckRefuelingTelemetry(2.5, 4.0, 0.35, True),
    )
    assert res.overall_safe is True
    assert res.active_alarms_count == 0


def test_batch19_cli_commands() -> None:
    app = build_app()
    r1 = runner.invoke(app, ["maritime-aux19", "exhvalve-check"])
    assert r1.exit_code == 0 and "OPTIMAL_ACTUATOR_OPERATION" in r1.stdout
    r2 = runner.invoke(app, ["phukienhanghai19", "helideckjp5-check"])
    assert r2.exit_code == 0 and "JP5_DISPENSING_AUTHORIZED" in r2.stdout
