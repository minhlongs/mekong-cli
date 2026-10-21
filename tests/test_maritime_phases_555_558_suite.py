from typer.testing import CliRunner

from src.cli.commands.maritime_safety_auxiliary_batch24_command import maritime_aux24_app
from src.core.maritime.phase_555_air_lubrication_system_als_hull_nozzle_interlock import (
    AirLubricationAlsState,
    AirLubricationAlsTelemetry,
)
from src.core.maritime.phase_556_shaft_generator_pto_frequency_converter_interlock import (
    PtoShaftGeneratorState,
    PtoShaftGeneratorTelemetry,
)
from src.core.maritime.phase_557_galley_wet_chemical_deep_fat_hood_interlock import (
    GalleyDeepFatHoodState,
    GalleyDeepFatHoodTelemetry,
)
from src.core.maritime.phase_558_roro_shell_door_weathertight_cleat_interlock import (
    RoRoShellDoorInterlockState,
    RoRoShellDoorTelemetry,
)
from src.core.maritime_safety_auxiliary_batch24_engine import (
    MaritimeSafetyAuxiliaryBatch24Engine,
)

runner = CliRunner()


def test_phase_555_air_lubrication_als_interlock() -> None:
    eval_als = MaritimeSafetyAuxiliaryBatch24Engine.evaluate_als
    trip = eval_als(AirLubricationAlsTelemetry(15.0, 11.5, 0.65, 80.0, False))
    assert trip.state == AirLubricationAlsState.WATER_BACKFLOW_OR_ROLL_ISOLATION_TRIP
    assert trip.hull_non_return_isolation_valve_close is True
    assert eval_als(AirLubricationAlsTelemetry(6.5, 2.0, 0.65, 75.0, False)).state == (
        AirLubricationAlsState.LOW_VESSEL_SPEED_AUTO_STANDBY_IDLE
    )
    assert eval_als(AirLubricationAlsTelemetry(15.0, 2.0, 0.25, 75.0, False)).state == (
        AirLubricationAlsState.HEADER_OVERPRESSURE_MARGIN_LOW_WARN
    )
    assert eval_als(AirLubricationAlsTelemetry(16.0, 2.5, 0.65, 78.0, False)).state == (
        AirLubricationAlsState.ALS_MICROBUBBLE_CARPET_NOMINAL
    )


def test_phase_556_pto_shaft_generator_interlock() -> None:
    eval_pto = MaritimeSafetyAuxiliaryBatch24Engine.evaluate_pto_shaft_gen
    trip = eval_pto(PtoShaftGeneratorTelemetry(80.0, 1180.0, 60.0, 2.5, False))
    assert trip.state == PtoShaftGeneratorState.CRASH_STOP_OR_DC_LINK_FAULT_ACB_TRIP
    assert trip.pto_acb_fast_trip_open is True
    assert eval_pto(PtoShaftGeneratorTelemetry(58.0, 980.0, 60.0, 2.5, False)).state == (
        PtoShaftGeneratorState.RPM_WINDOW_DG_AUTO_START_TRANSFER
    )
    assert eval_pto(PtoShaftGeneratorTelemetry(82.0, 980.0, 60.0, 5.8, False)).state == (
        PtoShaftGeneratorState.AFE_HARMONIC_THD_HIGH_WARN
    )
    assert eval_pto(PtoShaftGeneratorTelemetry(82.0, 980.0, 58.0, 2.4, False)).state == (
        PtoShaftGeneratorState.PTO_GRID_PARALLEL_NOMINAL
    )


def test_phase_557_galley_wet_chemical_hood_interlock() -> None:
    eval_hood = MaritimeSafetyAuxiliaryBatch24Engine.evaluate_galley_hood
    trip = eval_hood(GalleyDeepFatHoodTelemetry(365.0, 120.0, False, False))
    assert trip.state == GalleyDeepFatHoodState.WET_CHEMICAL_SAPONIFICATION_DISCHARGE_TRIP
    assert trip.wet_chemical_agent_release_cmd is True
    assert eval_hood(GalleyDeepFatHoodTelemetry(242.0, 120.0, False, False)).state == (
        GalleyDeepFatHoodState.HIGH_OIL_TEMP_THERMOSTAT_CUTOUT
    )
    assert eval_hood(GalleyDeepFatHoodTelemetry(180.0, 265.0, False, False)).state == (
        GalleyDeepFatHoodState.GREASE_FILTER_CLOGGED_DP_WARN
    )
    assert eval_hood(GalleyDeepFatHoodTelemetry(180.0, 110.0, False, False)).state == (
        GalleyDeepFatHoodState.GALLEY_HOOD_EXTRACTION_NOMINAL
    )


def test_phase_558_roro_shell_door_interlock_and_cli() -> None:
    eval_door = MaritimeSafetyAuxiliaryBatch24Engine.evaluate_roro_shell_door
    trip = eval_door(RoRoShellDoorTelemetry(False, True, 1.5, 155.0, True))
    assert trip.state == RoRoShellDoorInterlockState.UNSECURED_SHELL_DOOR_SEA_MODE_TRIP
    assert trip.departure_propulsion_inhibit_cmd is True
    assert eval_door(RoRoShellDoorTelemetry(True, True, 18.0, 155.0, True)).state == (
        RoRoShellDoorInterlockState.GASKET_LEAK_BILGE_WELL_HIGH_ALARM
    )
    assert eval_door(RoRoShellDoorTelemetry(True, True, 1.5, 95.0, True)).state == (
        RoRoShellDoorInterlockState.CLEAT_HYDRAULIC_PRESSURE_LOW_WARN
    )
    assert eval_door(RoRoShellDoorTelemetry(True, True, 1.5, 155.0, True)).state == (
        RoRoShellDoorInterlockState.SHELL_DOOR_WEATHERTIGHT_SEALED_NOMINAL
    )
    for cmd in ["als-check", "pto-check", "galley-hood-check", "roro-door-check"]:
        assert runner.invoke(maritime_aux24_app, [cmd]).exit_code == 0
