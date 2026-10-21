from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.maritime.phase_539_piston_rod_stuffing_box_drain import (
    PistonRodStuffingBoxDrainEngine, StuffingBoxDrainState, StuffingBoxDrainTelemetry,
)
from src.core.maritime.phase_540_bess_thermal_runaway_offgas_interlock import (
    BessThermalRunawayOffgasEngine, BessThermalRunawayState, BessThermalRunawayTelemetry,
)
from src.core.maritime.phase_541_dry_chemical_powder_nitrogen_interlock import (
    DryChemicalPowderNitrogenEngine, DryPowderSystemState, DryPowderSystemTelemetry,
)
from src.core.maritime.phase_542_common_rail_fuel_booster_interlock import (
    CommonRailBoosterState, CommonRailBoosterTelemetry, CommonRailFuelBoosterEngine,
)
from src.core.maritime_safety_auxiliary_batch20_engine import MaritimeSafetyAuxiliaryBatch20Engine

runner = CliRunner()


def test_phase_539_piston_rod_stuffing_box_drain() -> None:
    ok = PistonRodStuffingBoxDrainEngine.evaluate(StuffingBoxDrainTelemetry(0.08, 52.0, 6.0, 40.0))
    assert ok.state == StuffingBoxDrainState.OPTIMAL_STUFFING_BOX_SEALING
    blowby = PistonRodStuffingBoxDrainEngine.evaluate(StuffingBoxDrainTelemetry(0.42, 88.0, 12.0, 55.0))
    assert blowby.state == StuffingBoxDrainState.GAS_BLOWBY_SEALING_RING_FAILURE_SLOWDOWN
    assert blowby.engine_slowdown_cmd is True
    fe = PistonRodStuffingBoxDrainEngine.evaluate(StuffingBoxDrainTelemetry(0.10, 58.0, 8.0, 175.0))
    assert fe.state == StuffingBoxDrainState.STUFFING_BOX_CONTAMINATION_SLUDGE_DIVERT
    assert fe.divert_drain_to_sludge_tank is True


def test_phase_540_bess_thermal_runaway_offgas_interlock() -> None:
    ok = BessThermalRunawayOffgasEngine.evaluate(BessThermalRunawayTelemetry(32.0, 0.0, 2.0, 28.0))
    assert ok.state == BessThermalRunawayState.NOMINAL_BESS_ENCLOSURE
    runaway = BessThermalRunawayOffgasEngine.evaluate(BessThermalRunawayTelemetry(68.0, 28.0, 120.0, 25.0))
    assert runaway.state == BessThermalRunawayState.THERMAL_RUNAWAY_DELUGE_DC_ISOLATION_TRIP
    assert runaway.water_mist_deluge_release_cmd is True


def test_phase_541_dry_chemical_powder_nitrogen_interlock() -> None:
    standby = DryChemicalPowderNitrogenEngine.evaluate(DryPowderSystemTelemetry(190.0, 14.5, 20.0, False))
    assert standby.state == DryPowderSystemState.DCP_STANDBY_READY
    hold = DryChemicalPowderNitrogenEngine.evaluate(DryPowderSystemTelemetry(185.0, 9.5, 8.0, True))
    assert hold.state == DryPowderSystemState.FLUIDIZATION_INCOMPLETE_HOLD_INTERLOCK
    assert hold.main_powder_release_valve_open is False
    fire = DryChemicalPowderNitrogenEngine.evaluate(DryPowderSystemTelemetry(185.0, 14.5, 18.0, True))
    assert fire.state == DryPowderSystemState.DCP_MONITOR_DISCHARGE_ACTIVE
    assert fire.main_powder_release_valve_open is True


def test_phase_542_common_rail_fuel_booster_interlock() -> None:
    ok = CommonRailFuelBoosterEngine.evaluate(CommonRailBoosterTelemetry(850.0, 220.0, False, False))
    assert ok.state == CommonRailBoosterState.NOMINAL_COMMON_RAIL_PRESSURE
    eprv = CommonRailFuelBoosterEngine.evaluate(CommonRailBoosterTelemetry(1080.0, 220.0, True, False))
    assert eprv.state == CommonRailBoosterState.RAIL_OVERPRESSURE_EPRV_LIFT_SLOWDOWN
    assert eprv.engine_slowdown_cmd is True


def test_batch20_coordinator_engine() -> None:
    res = MaritimeSafetyAuxiliaryBatch20Engine.evaluate_batch20(
        StuffingBoxDrainTelemetry(0.08, 52.0, 6.0, 40.0),
        BessThermalRunawayTelemetry(32.0, 0.0, 2.0, 28.0),
        DryPowderSystemTelemetry(190.0, 14.5, 20.0, False),
        CommonRailBoosterTelemetry(850.0, 220.0, False, False),
    )
    assert res.overall_safe is True
    assert res.active_alarms_count == 0


def test_batch20_cli_commands() -> None:
    app = build_app()
    r1 = runner.invoke(app, ["maritime-aux20", "stuffingbox-check"])
    assert r1.exit_code == 0 and "OPTIMAL_STUFFING_BOX_SEALING" in r1.stdout
    r2 = runner.invoke(app, ["phukienhanghai20", "commonrail-check"])
    assert r2.exit_code == 0 and "NOMINAL_COMMON_RAIL_PRESSURE" in r2.stdout
