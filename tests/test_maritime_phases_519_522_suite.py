"""Pytest test suite for Maritime Safety Automation Batch 15 (Phases 519-522).
Covers Turning Gear Interlock, Grey Water Tank, Deck Crane Limiter, and Escape Trunk.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_519_turning_gear_start_interlock import (
    TurningGearInterlockState, TurningGearStartInterlockEngine, TurningGearTelemetry,
)
from src.core.maritime.phase_520_grey_water_tank_ventilation import (
    GreyWaterSystemState, GreyWaterTankVentilationEngine, GreyWaterTelemetry,
)
from src.core.maritime.phase_521_deck_crane_overload_limiter import (
    DeckCraneOperatingState, DeckCraneOverloadLimiterEngine, DeckCraneTelemetry,
)
from src.core.maritime.phase_522_escape_trunk_pressurization import (
    EscapeTrunkPressurizationEngine, EscapeTrunkStatus, EscapeTrunkTelemetry,
)
from src.core.maritime_safety_auxiliary_batch15_engine import (
    MaritimeSafetyAuxiliaryBatch15Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch15_command import maritime_aux15_app

runner = CliRunner()


def test_phase_519_turning_gear_start_interlock() -> None:
    res_ready = TurningGearStartInterlockEngine.evaluate(
        TurningGearTelemetry(turning_gear_disengaged=True, main_air_shutoff_valve_open=True, indicator_cocks_closed=True)
    )
    assert res_ready.interlock_state == TurningGearInterlockState.READY_FOR_MAIN_START
    assert res_ready.starting_air_permitted is True
    assert res_ready.bridge_start_ready_lamp is True

    res_engaged = TurningGearStartInterlockEngine.evaluate(
        TurningGearTelemetry(turning_gear_disengaged=False, main_air_shutoff_valve_open=True)
    )
    assert res_engaged.interlock_state == TurningGearInterlockState.TURNING_GEAR_ENGAGED_START_BLOCKED
    assert res_engaged.starting_air_permitted is False

    res_cocks = TurningGearStartInterlockEngine.evaluate(
        TurningGearTelemetry(turning_gear_disengaged=True, main_air_shutoff_valve_open=True, indicator_cocks_closed=False)
    )
    assert res_cocks.interlock_state == TurningGearInterlockState.INDICATOR_COCKS_OPEN_BLOWTHROUGH
    assert res_cocks.bridge_start_ready_lamp is False


def test_phase_520_grey_water_tank_ventilation() -> None:
    res_norm = GreyWaterTankVentilationEngine.evaluate(
        GreyWaterTelemetry(tank_level_pct=45.0, h2s_concentration_ppm=1.5)
    )
    assert res_norm.system_state == GreyWaterSystemState.NORMAL_COLLECTION
    assert res_norm.standby_pump_running is False

    res_h2s = GreyWaterTankVentilationEngine.evaluate(
        GreyWaterTelemetry(tank_level_pct=65.0, h2s_concentration_ppm=14.0)
    )
    assert res_h2s.system_state == GreyWaterSystemState.H2S_TOXIC_GAS_VENT_LOCKDOWN
    assert res_h2s.emergency_vent_fan_boost is True

    res_port = GreyWaterTankVentilationEngine.evaluate(
        GreyWaterTelemetry(tank_level_pct=50.0, h2s_concentration_ppm=1.0, in_zero_discharge_port_zone=True, overboard_valve_open=True)
    )
    assert res_port.system_state == GreyWaterSystemState.ILLEGAL_PORT_OVERBOARD_BLOCK


def test_phase_521_deck_crane_overload_limiter() -> None:
    res_safe = DeckCraneOverloadLimiterEngine.evaluate(
        DeckCraneTelemetry(hook_load_pct_swl=72.0, boom_angle_deg=45.0)
    )
    assert res_safe.operating_state == DeckCraneOperatingState.SAFE_CARGO_HANDLING
    assert res_safe.hoist_up_permitted is True

    res_over = DeckCraneOverloadLimiterEngine.evaluate(
        DeckCraneTelemetry(hook_load_pct_swl=108.0, boom_angle_deg=45.0)
    )
    assert res_over.operating_state == DeckCraneOperatingState.OVERLOAD_MOMENT_CUTOUT_TRIP
    assert res_over.hoist_up_permitted is False
    assert res_over.hydraulic_brake_applied is True

    res_slack = DeckCraneOverloadLimiterEngine.evaluate(
        DeckCraneTelemetry(hook_load_pct_swl=10.0, boom_angle_deg=35.0, slack_wire_detected=True)
    )
    assert res_slack.operating_state == DeckCraneOperatingState.SLACK_WIRE_DRUM_LOCKOUT


def test_phase_522_escape_trunk_pressurization() -> None:
    res_ok = EscapeTrunkPressurizationEngine.evaluate(
        EscapeTrunkTelemetry(trunk_overpressure_pa=32.0, emergency_lighting_volts=24.2)
    )
    assert res_ok.trunk_status == EscapeTrunkStatus.COMPLIANT_SAFE_EGRESS
    assert res_ok.smoke_ingress_protected is True

    res_low = EscapeTrunkPressurizationEngine.evaluate(
        EscapeTrunkTelemetry(trunk_overpressure_pa=12.0, emergency_lighting_volts=24.0)
    )
    assert res_low.trunk_status == EscapeTrunkStatus.UNDER_PRESSURIZED_SMOKE_RISK
    assert res_low.smoke_ingress_protected is False

    res_high = EscapeTrunkPressurizationEngine.evaluate(
        EscapeTrunkTelemetry(trunk_overpressure_pa=58.0, emergency_lighting_volts=24.0)
    )
    assert res_high.trunk_status == EscapeTrunkStatus.OVER_PRESSURIZED_DOOR_FORCE_HIGH
    assert res_high.relief_damper_open_cmd is True


def test_maritime_auxiliary_batch15_coordinator() -> None:
    tg = TurningGearTelemetry(turning_gear_disengaged=True, main_air_shutoff_valve_open=True)
    gw = GreyWaterTelemetry(tank_level_pct=40.0, h2s_concentration_ppm=0.5)
    crane = DeckCraneTelemetry(hook_load_pct_swl=65.0, boom_angle_deg=45.0)
    trunk = EscapeTrunkTelemetry(trunk_overpressure_pa=30.0)

    res = MaritimeSafetyAuxiliaryBatch15Engine.evaluate_batch15(tg, gw, crane, trunk)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch15_cli() -> None:
    res1 = runner.invoke(maritime_aux15_app, ["turninggear-check"])
    assert res1.exit_code == 0
    assert "READY_FOR_MAIN_START" in res1.stdout

    res2 = runner.invoke(maritime_aux15_app, ["greywater-check", "--level-pct", "45.0"])
    assert res2.exit_code == 0
    assert "NORMAL_COLLECTION" in res2.stdout

    res3 = runner.invoke(maritime_aux15_app, ["crane-check", "--load-pct", "70.0"])
    assert res3.exit_code == 0
    assert "SAFE_CARGO_HANDLING" in res3.stdout

    res4 = runner.invoke(maritime_aux15_app, ["escapetrunk-check", "--pressure-pa", "35.0"])
    assert res4.exit_code == 0
    assert "COMPLIANT_SAFE_EGRESS" in res4.stdout
