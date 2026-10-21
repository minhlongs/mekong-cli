from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch22_command import maritime_aux22_app
from src.core.maritime.phase_547_fgss_glycol_vaporizer_gvu_interlock import (
    FgssGlycolGvuState,
    FgssGlycolGvuTelemetry,
    FgssGlycolVaporizerGvuEngine,
)
from src.core.maritime.phase_548_charge_air_cooler_condensate_interlock import (
    ChargeAirCondensateState,
    ChargeAirCondensateTelemetry,
    ChargeAirCoolerCondensateEngine,
)
from src.core.maritime.phase_549_high_expansion_foam_generator_interlock import (
    HighExpansionFoamGeneratorEngine,
    HighExpFoamGeneratorState,
    HighExpFoamGeneratorTelemetry,
)
from src.core.maritime.phase_550_dp_bus_tie_wcsf_redundancy_interlock import (
    DpBusTieRedundancyState,
    DpBusTieRedundancyTelemetry,
    DpBusTieWcsfRedundancyEngine,
)
from src.core.maritime_safety_auxiliary_batch22_engine import MaritimeSafetyAuxiliaryBatch22Engine


def test_phase_547_fgss_glycol_vaporizer_gvu_interlock() -> None:
    trip = FgssGlycolVaporizerGvuEngine.evaluate(FgssGlycolGvuTelemetry(-4.0, 5.0, 35.0))
    assert trip.state == FgssGlycolGvuState.CRYOGENIC_CARRYOVER_OR_GVU_GAS_MGFV_TRIP
    assert trip.master_gas_fuel_valve_close_cmd and trip.nitrogen_dbb_purge_open_cmd
    pre = FgssGlycolVaporizerGvuEngine.evaluate(FgssGlycolGvuTelemetry(32.0, 24.0, 35.0))
    assert pre.state == FgssGlycolGvuState.GVU_ENCLOSURE_VENT_OR_LEAK_PRE_ALARM
    assert pre.gvu_extraction_fan_boost_cmd


def test_phase_548_charge_air_cooler_condensate_interlock() -> None:
    leak = ChargeAirCoolerCondensateEngine.evaluate(ChargeAirCondensateTelemetry(45.0, 620.0))
    assert leak.state == ChargeAirCondensateState.TUBE_LEAK_OR_CARRYOVER_SLOWDOWN_TRIP
    assert leak.engine_slowdown_cmd and leak.continuous_blowdown_valve_open
    blow = ChargeAirCoolerCondensateEngine.evaluate(ChargeAirCondensateTelemetry(68.0, 20.0))
    assert blow.state == ChargeAirCondensateState.HIGH_HUMIDITY_CONTINUOUS_BLOWDOWN_ACTIVE


def test_phase_549_high_expansion_foam_generator_interlock() -> None:
    lock = HighExpansionFoamGeneratorEngine.evaluate(
        HighExpFoamGeneratorTelemetry(6.5, 2.1, 50.0, False)
    )
    assert lock.state == HighExpFoamGeneratorState.QCV_OR_VENT_DAMPER_OPEN_DISCHARGE_LOCKOUT
    assert not lock.foam_generator_valve_open
    res_pump = HighExpansionFoamGeneratorEngine.evaluate(
        HighExpFoamGeneratorTelemetry(4.8, 2.1, 165.0, True)
    )
    assert res_pump.state == HighExpFoamGeneratorState.FOAM_MANIFOLD_OR_PROPORTIONER_RESERVE_CUTIN
    assert res_pump.reserve_foam_pump_cut_in and res_pump.overpressure_relief_damper_open


def test_phase_550_dp_bus_tie_wcsf_redundancy_interlock() -> None:
    split = DpBusTieWcsfRedundancyEngine.evaluate(DpBusTieRedundancyTelemetry(81.0, 0.2, 70.0))
    assert split.state == DpBusTieRedundancyState.WCSF_OR_FAULT_BUS_TIE_SPLIT_TRIP
    assert split.bus_tie_breaker_open_split_cmd and split.standby_thruster_auto_start_cmd
    yellow = DpBusTieWcsfRedundancyEngine.evaluate(
        DpBusTieRedundancyTelemetry(99.0, 0.1, 72.0, 15.0)
    )
    assert yellow.state == DpBusTieRedundancyState.DP_THRUSTER_MARGIN_YELLOW_ADVISORY


def test_batch22_coordinator_and_cli() -> None:
    batch = MaritimeSafetyAuxiliaryBatch22Engine.evaluate_batch(
        FgssGlycolGvuTelemetry(35.0, 0.0, 36.0, 45.0),
        ChargeAirCondensateTelemetry(22.0, 15.0, 2.1),
        HighExpFoamGeneratorTelemetry(6.8, 2.1, 65.0, True),
        DpBusTieRedundancyTelemetry(99.5, 0.1, 68.0, 35.0),
    )
    assert not batch.any_critical_interlock_active
    runner = CliRunner()
    assert runner.invoke(maritime_aux22_app, ["fgss-check"]).exit_code == 0
    assert runner.invoke(maritime_aux22_app, ["dpbustie-check", "--volt-pct", "80.0"]).exit_code == 0
