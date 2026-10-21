from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch21_command import maritime_aux21_app
from src.core.maritime.phase_543_scr_urea_ammonia_slip_interlock import (
    ScrUreaAmmoniaSlipEngine,
    ScrUreaDosingState,
    ScrUreaDosingTelemetry,
)
from src.core.maritime.phase_544_cargo_tank_pv_breaker_mast_interlock import (
    CargoPvBreakerMastState,
    CargoPvBreakerMastTelemetry,
    CargoTankPvBreakerMastEngine,
)
from src.core.maritime.phase_545_azipod_slewing_seal_stator_interlock import (
    AzipodPropulsorState,
    AzipodPropulsorTelemetry,
    AzipodSlewingSealStatorEngine,
)
from src.core.maritime.phase_546_lng_esd_drybreak_erc_interlock import (
    LngEsdDrybreakErcEngine,
    LngEsdErcState,
    LngEsdErcTelemetry,
)
from src.core.maritime_safety_auxiliary_batch21_engine import MaritimeSafetyAuxiliaryBatch21Engine


def test_phase_543_scr_urea_ammonia_slip_interlock() -> None:
    sinter = ScrUreaAmmoniaSlipEngine.evaluate(ScrUreaDosingTelemetry(465.0, 0.08, 3.0))
    assert sinter.state == ScrUreaDosingState.CATALYST_THERMAL_SINTERING_BYPASS_TRIP
    assert not sinter.urea_dosing_valve_open and sinter.reactor_bypass_valve_open
    abs_foul = ScrUreaAmmoniaSlipEngine.evaluate(ScrUreaDosingTelemetry(295.0, 0.35, 3.0))
    assert abs_foul.state == ScrUreaDosingState.LOW_TEMP_BISULFATE_FOULING_DOSING_CUTOFF
    slip = ScrUreaAmmoniaSlipEngine.evaluate(ScrUreaDosingTelemetry(340.0, 0.08, 12.5))
    assert slip.state == ScrUreaDosingState.HIGH_AMMONIA_SLIP_DOSING_TRIM_ALARM


def test_phase_544_cargo_tank_pv_breaker_mast_interlock() -> None:
    fire = CargoTankPvBreakerMastEngine.evaluate(CargoPvBreakerMastTelemetry(8.0, 1850.0, 82.0))
    assert fire.state == CargoPvBreakerMastState.MAST_RISER_VENT_FIRE_N2_SNUFFING_TRIP
    assert fire.cargo_transfer_emergency_stop_cmd and fire.mast_riser_n2_snuffing_open
    blowout = CargoTankPvBreakerMastEngine.evaluate(CargoPvBreakerMastTelemetry(25.2, 1850.0, 32.0))
    assert blowout.state == CargoPvBreakerMastState.PV_BREAKER_BLOWOUT_CARGO_TRANSFER_TRIP


def test_phase_545_azipod_slewing_seal_stator_interlock() -> None:
    derate = AzipodSlewingSealStatorEngine.evaluate(AzipodPropulsorTelemetry(160.0, 4.0, 175.0))
    assert derate.state == AzipodPropulsorState.POD_CRITICAL_STATOR_OR_INGRESS_PROPULSION_DERATE
    assert derate.propulsion_power_derate_cmd and derate.cooling_air_blower_boost_cmd
    slew = AzipodSlewingSealStatorEngine.evaluate(AzipodPropulsorTelemetry(115.0, 2.0, 125.0))
    assert slew.state == AzipodPropulsorState.SLEWING_HYDRAULIC_LOW_PRESSURE_STANDBY_CUTIN
    assert slew.standby_slewing_pump_cut_in


def test_phase_546_lng_esd_drybreak_erc_interlock() -> None:
    esd2 = LngEsdDrybreakErcEngine.evaluate(LngEsdErcTelemetry(3.8, 15.0, 190.0))
    assert esd2.state == LngEsdErcState.ESD2_DRY_BREAK_ERC_DECOUPLE_TRIP
    assert esd2.esd1_manifold_valves_close_cmd and esd2.esd2_erc_collar_release_cmd
    esd1 = LngEsdDrybreakErcEngine.evaluate(LngEsdErcTelemetry(2.2, 15.0, 190.0))
    assert esd1.state == LngEsdErcState.ESD1_MANIFOLD_SHUTDOWN_TRIP
    assert esd1.esd1_manifold_valves_close_cmd and not esd1.esd2_erc_collar_release_cmd


def test_batch21_coordinator_and_cli() -> None:
    batch = MaritimeSafetyAuxiliaryBatch21Engine.evaluate_batch(
        ScrUreaDosingTelemetry(340.0, 0.08, 4.0, 1.1),
        CargoPvBreakerMastTelemetry(6.5, 1850.0, 32.0),
        AzipodPropulsorTelemetry(115.0, 2.0, 175.0, 42.0),
        LngEsdErcTelemetry(0.5, 18.0, 195.0, True),
    )
    assert not batch.any_critical_interlock_active
    runner = CliRunner()
    assert runner.invoke(maritime_aux21_app, ["scr-check"]).exit_code == 0
    assert runner.invoke(maritime_aux21_app, ["lng-esd-check", "--drift-m", "3.9"]).exit_code == 0
