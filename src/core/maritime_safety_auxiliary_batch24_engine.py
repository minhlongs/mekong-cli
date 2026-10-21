from src.core.maritime.phase_555_air_lubrication_system_als_hull_nozzle_interlock import (
    AirLubricationAlsAssessment,
    AirLubricationAlsEngine,
    AirLubricationAlsState,
    AirLubricationAlsTelemetry,
)
from src.core.maritime.phase_556_shaft_generator_pto_frequency_converter_interlock import (
    PtoShaftGeneratorAssessment,
    PtoShaftGeneratorConverterEngine,
    PtoShaftGeneratorState,
    PtoShaftGeneratorTelemetry,
)
from src.core.maritime.phase_557_galley_wet_chemical_deep_fat_hood_interlock import (
    GalleyDeepFatHoodAssessment,
    GalleyDeepFatHoodState,
    GalleyDeepFatHoodTelemetry,
    GalleyWetChemicalDeepFatHoodEngine,
)
from src.core.maritime.phase_558_roro_shell_door_weathertight_cleat_interlock import (
    RoRoShellDoorAssessment,
    RoRoShellDoorIndicatorsInterlockEngine,
    RoRoShellDoorInterlockState,
    RoRoShellDoorTelemetry,
)


class MaritimeSafetyAuxiliaryBatch24Engine:
    """Unified coordinator for Maritime Auxiliary Automation Batch 24 (Phases 555-558)."""

    evaluate_als = AirLubricationAlsEngine.evaluate
    evaluate_pto_shaft_gen = PtoShaftGeneratorConverterEngine.evaluate
    evaluate_galley_hood = GalleyWetChemicalDeepFatHoodEngine.evaluate
    evaluate_roro_shell_door = RoRoShellDoorIndicatorsInterlockEngine.evaluate


__all__ = [
    "AirLubricationAlsAssessment",
    "AirLubricationAlsEngine",
    "AirLubricationAlsState",
    "AirLubricationAlsTelemetry",
    "PtoShaftGeneratorAssessment",
    "PtoShaftGeneratorConverterEngine",
    "PtoShaftGeneratorState",
    "PtoShaftGeneratorTelemetry",
    "GalleyDeepFatHoodAssessment",
    "GalleyDeepFatHoodState",
    "GalleyDeepFatHoodTelemetry",
    "GalleyWetChemicalDeepFatHoodEngine",
    "RoRoShellDoorAssessment",
    "RoRoShellDoorIndicatorsInterlockEngine",
    "RoRoShellDoorInterlockState",
    "RoRoShellDoorTelemetry",
    "MaritimeSafetyAuxiliaryBatch24Engine",
]
