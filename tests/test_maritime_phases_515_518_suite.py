"""Pytest test suite for Maritime Safety Automation Batch 14 (Phases 515-518).
Covers Anchor Windlass, Switchboard Insulation/Load Shed, Bow Visor Cleat, and Marine Elevator.
Strictly zero mocks, pure deterministic validation.
"""
from typer.testing import CliRunner

from src.core.maritime.phase_515_anchor_windlass_payout_brake import (
    AnchorWindlassPayoutBrakeEngine, AnchorWindlassTelemetry, WindlassOperatingState,
)
from src.core.maritime.phase_516_switchboard_insulation_load_shed import (
    SwitchboardBusState, SwitchboardInsulationLoadShedEngine, SwitchboardTelemetry,
)
from src.core.maritime.phase_517_bow_visor_stern_ramp_cleat import (
    BowVisorRampTelemetry, BowVisorSternRampCleatEngine, ShellDoorSealStatus,
)
from src.core.maritime.phase_518_marine_elevator_roll_governor import (
    MarineElevatorMode, MarineElevatorRollGovernorEngine, MarineElevatorTelemetry,
)
from src.core.maritime_safety_auxiliary_batch14_engine import (
    MaritimeSafetyAuxiliaryBatch14Engine,
)
from src.cli.commands.maritime_safety_auxiliary_batch14_command import maritime_aux14_app

runner = CliRunner()


def test_phase_515_anchor_windlass_payout_brake() -> None:
    res_norm = AnchorWindlassPayoutBrakeEngine.evaluate(
        AnchorWindlassTelemetry(payout_speed_m_s=3.0, remaining_shackles_in_locker=6.0)
    )
    assert res_norm.operating_state == WindlassOperatingState.CONTROLLED_ANCHOR_HANDLING
    assert res_norm.band_brake_auto_clamp is False

    res_runaway = AnchorWindlassPayoutBrakeEngine.evaluate(
        AnchorWindlassTelemetry(payout_speed_m_s=8.4, remaining_shackles_in_locker=4.0)
    )
    assert res_runaway.operating_state == WindlassOperatingState.RUNAWAY_CHAIN_EMERGENCY_BRAKE
    assert res_runaway.band_brake_auto_clamp is True

    res_bitter = AnchorWindlassPayoutBrakeEngine.evaluate(
        AnchorWindlassTelemetry(payout_speed_m_s=2.0, remaining_shackles_in_locker=1.0)
    )
    assert res_bitter.operating_state == WindlassOperatingState.BITTER_END_LOW_SHACKLE_ALARM
    assert res_bitter.bitter_end_quick_release_armed is True


def test_phase_516_switchboard_insulation_load_shed() -> None:
    res_norm = SwitchboardInsulationLoadShedEngine.evaluate(
        SwitchboardTelemetry(insulation_mohm=4.5, generator_load_pct=75.0)
    )
    assert res_norm.bus_state == SwitchboardBusState.HEALTHY_BUS_DISTRIBUTION
    assert res_norm.non_essential_loads_shed is False

    res_shed1 = SwitchboardInsulationLoadShedEngine.evaluate(
        SwitchboardTelemetry(insulation_mohm=3.0, generator_load_pct=104.0, overload_duration_sec=6.0)
    )
    assert res_shed1.bus_state == SwitchboardBusState.PREFERENTIAL_TRIP_STAGE_1_SHED
    assert res_shed1.non_essential_loads_shed is True

    res_earth = SwitchboardInsulationLoadShedEngine.evaluate(
        SwitchboardTelemetry(insulation_mohm=0.03, generator_load_pct=65.0)
    )
    assert res_earth.bus_state == SwitchboardBusState.CRITICAL_GROUND_FAULT_ALARM
    assert res_earth.earth_fault_beacon_on is True


def test_phase_517_bow_visor_stern_ramp_cleat() -> None:
    res_sea = BowVisorSternRampCleatEngine.evaluate(
        BowVisorRampTelemetry(vessel_at_sea_mode=True, all_hydraulic_cleats_locked=True, pneumatic_gasket_bar=3.2)
    )
    assert res_sea.seal_status == ShellDoorSealStatus.LOCKED_AND_WATERTIGHT_AT_SEA
    assert res_sea.bridge_departure_green_light is True

    res_unsec = BowVisorSternRampCleatEngine.evaluate(
        BowVisorRampTelemetry(vessel_at_sea_mode=True, all_hydraulic_cleats_locked=False, pneumatic_gasket_bar=3.0)
    )
    assert res_unsec.seal_status == ShellDoorSealStatus.UNSECURED_CLEAT_SEA_DEPARTURE_BLOCK
    assert res_unsec.bridge_departure_green_light is False

    res_ingress = BowVisorSternRampCleatEngine.evaluate(
        BowVisorRampTelemetry(vessel_at_sea_mode=True, all_hydraulic_cleats_locked=True, threshold_water_ingress_detected=True)
    )
    assert res_ingress.seal_status == ShellDoorSealStatus.COLLISION_BULKHEAD_WATER_INGRESS


def test_phase_518_marine_elevator_roll_governor() -> None:
    res_norm = MarineElevatorRollGovernorEngine.evaluate(
        MarineElevatorTelemetry(vessel_roll_angle_deg=4.5, car_speed_pct_rated=100.0)
    )
    assert res_norm.elevator_mode == MarineElevatorMode.NORMAL_PASSENGER_SERVICE
    assert res_norm.safety_gear_wedges_engaged is False

    res_roll = MarineElevatorRollGovernorEngine.evaluate(
        MarineElevatorTelemetry(vessel_roll_angle_deg=18.0, car_speed_pct_rated=100.0)
    )
    assert res_roll.elevator_mode == MarineElevatorMode.HEAVY_WEATHER_ROLL_HOMING_LOCK
    assert res_roll.parked_at_embarkation_deck is True

    res_gov = MarineElevatorRollGovernorEngine.evaluate(
        MarineElevatorTelemetry(vessel_roll_angle_deg=2.0, car_speed_pct_rated=122.0)
    )
    assert res_gov.elevator_mode == MarineElevatorMode.GOVERNOR_OVERSPEED_SAFETY_CLAMP
    assert res_gov.safety_gear_wedges_engaged is True


def test_maritime_auxiliary_batch14_coordinator() -> None:
    windlass = AnchorWindlassTelemetry(payout_speed_m_s=2.0, remaining_shackles_in_locker=6.0)
    msb = SwitchboardTelemetry(insulation_mohm=5.0, generator_load_pct=70.0)
    visor = BowVisorRampTelemetry(vessel_at_sea_mode=True, all_hydraulic_cleats_locked=True)
    elevator = MarineElevatorTelemetry(vessel_roll_angle_deg=3.0)

    res = MaritimeSafetyAuxiliaryBatch14Engine.evaluate_batch14(windlass, msb, visor, elevator)
    assert res.overall_safe is True
    assert res.active_alarms_count == 0
    assert res.system_health_summary == ["ALL_SYSTEMS_OPTIMAL"]


def test_maritime_auxiliary_batch14_cli() -> None:
    res1 = runner.invoke(maritime_aux14_app, ["windlass-check", "--speed-m-s", "2.5"])
    assert res1.exit_code == 0
    assert "CONTROLLED_ANCHOR_HANDLING" in res1.stdout

    res2 = runner.invoke(maritime_aux14_app, ["msb-check", "--insulation-mohm", "5.0"])
    assert res2.exit_code == 0
    assert "HEALTHY_BUS_DISTRIBUTION" in res2.stdout

    res3 = runner.invoke(maritime_aux14_app, ["visor-check"])
    assert res3.exit_code == 0
    assert "LOCKED_AND_WATERTIGHT_AT_SEA" in res3.stdout

    res4 = runner.invoke(maritime_aux14_app, ["elevator-check", "--roll-deg", "4.0"])
    assert res4.exit_code == 0
    assert "NORMAL_PASSENGER_SERVICE" in res4.stdout
