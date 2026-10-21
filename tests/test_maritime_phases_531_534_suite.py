from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime.phase_531_double_wall_fuel_pipe_leak import (
    DoubleWallFuelPipeLeakEngine, DoubleWallFuelPipeState, DoubleWallFuelPipeTelemetry,
)
from src.core.maritime.phase_532_inert_gas_generator_stoichiometry import (
    InertGasGeneratorState, InertGasGeneratorStoichiometryEngine, InertGasGeneratorTelemetry,
)
from src.core.maritime.phase_533_stern_tube_airguard_seal_balance import (
    SternTubeAirguardSealBalanceEngine, SternTubeAirguardState, SternTubeAirguardTelemetry,
)
from src.core.maritime.phase_534_enclosed_space_entry_gas_interlock import (
    EnclosedSpaceEntryGasInterlockEngine, EnclosedSpaceEntryState, EnclosedSpaceEntryTelemetry,
)
from src.core.maritime_safety_auxiliary_batch18_engine import MaritimeSafetyAuxiliaryBatch18Engine

runner = CliRunner()


def test_phase_531_double_wall_fuel_pipe_leak() -> None:
    ok = DoubleWallFuelPipeLeakEngine.evaluate(DoubleWallFuelPipeTelemetry(0.05, 10.0, 145.0, 6.5))
    assert ok.state == DoubleWallFuelPipeState.NORMAL_JACKETED_INTEGRITY
    rupture = DoubleWallFuelPipeLeakEngine.evaluate(DoubleWallFuelPipeTelemetry(1.8, 85.0, 160.0, 6.5))
    assert rupture.state == DoubleWallFuelPipeState.HIGH_PRESSURE_FUEL_RUPTURE_ALARM
    assert rupture.engine_slowdown_required is True
    hot = DoubleWallFuelPipeLeakEngine.evaluate(DoubleWallFuelPipeTelemetry(0.1, 15.0, 232.0, 6.5))
    assert hot.state == DoubleWallFuelPipeState.HOT_SURFACE_SHIELD_OVERHEAT_ALARM


def test_phase_532_inert_gas_generator_stoichiometry() -> None:
    ok = InertGasGeneratorStoichiometryEngine.evaluate(InertGasGeneratorTelemetry(3.8, 42.0, 2.8, 1.03))
    assert ok.state == InertGasGeneratorState.OPTIMAL_INERT_DELIVERY
    assert ok.deck_main_isolation_valve_open is True
    vent = InertGasGeneratorStoichiometryEngine.evaluate(InertGasGeneratorTelemetry(8.4, 48.0, 2.5, 1.25))
    assert vent.state == InertGasGeneratorState.HIGH_HIGH_O2_VENT_TO_ATMOSPHERE_TRIP
    assert vent.deck_main_isolation_valve_open is False
    assert vent.vent_to_atmosphere_open is True


def test_phase_533_stern_tube_airguard_seal_balance() -> None:
    ok = SternTubeAirguardSealBalanceEngine.evaluate(SternTubeAirguardTelemetry(1.65, 1.40, 22.0, 0.15, 48.0))
    assert ok.state == SternTubeAirguardState.BALANCED_AIRGUARD_BARRIER
    assert ok.air_over_sea_dp_bar == 0.25
    low_dp = SternTubeAirguardSealBalanceEngine.evaluate(SternTubeAirguardTelemetry(1.44, 1.40, 25.0, 0.20, 50.0))
    assert low_dp.state == SternTubeAirguardState.AIR_BARRIER_COLLAPSE_INGRESS_ALARM
    assert low_dp.standby_air_regulator_cutin is True


def test_phase_534_enclosed_space_entry_gas_interlock() -> None:
    ok = EnclosedSpaceEntryGasInterlockEngine.evaluate(
        EnclosedSpaceEntryTelemetry(20.9, 0.0, 0.0, 0.0, 45.0, 12.0)
    )
    assert ok.state == EnclosedSpaceEntryState.ENTRY_PERMIT_SAFE_AUTHORIZED
    assert ok.entry_hatch_interlock_released is True
    toxic = EnclosedSpaceEntryGasInterlockEngine.evaluate(
        EnclosedSpaceEntryTelemetry(20.9, 0.2, 12.0, 7.5, 45.0, 12.0)
    )
    assert toxic.state == EnclosedSpaceEntryState.TOXIC_OR_FLAMMABLE_GAS_HAZARD_LOCKOUT
    assert toxic.entry_hatch_interlock_released is False


def test_batch18_coordinator_engine() -> None:
    res = MaritimeSafetyAuxiliaryBatch18Engine.evaluate_batch18(
        DoubleWallFuelPipeTelemetry(0.05, 10.0, 145.0, 6.5),
        InertGasGeneratorTelemetry(3.8, 42.0, 2.8, 1.03),
        SternTubeAirguardTelemetry(1.65, 1.40, 22.0, 0.15, 48.0),
        EnclosedSpaceEntryTelemetry(20.9, 0.0, 0.0, 0.0, 45.0, 12.0),
    )
    assert res.overall_safe is True
    assert res.active_alarms_count == 0


def test_batch18_cli_commands() -> None:
    app = build_app()
    r1 = runner.invoke(app, ["maritime-aux18", "fuelpipe-check"])
    assert r1.exit_code == 0 and "NORMAL_JACKETED_INTEGRITY" in r1.stdout
    r2 = runner.invoke(app, ["phukienhanghai18", "enclosedspace-check"])
    assert r2.exit_code == 0 and "ENTRY_PERMIT_SAFE_AUTHORIZED" in r2.stdout
