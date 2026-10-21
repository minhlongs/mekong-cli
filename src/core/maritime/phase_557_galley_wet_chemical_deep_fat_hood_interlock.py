from dataclasses import dataclass
from enum import Enum


class GalleyDeepFatHoodState(str, Enum):
    GALLEY_HOOD_EXTRACTION_NOMINAL = "GALLEY_HOOD_EXTRACTION_NOMINAL"
    GREASE_FILTER_CLOGGED_DP_WARN = "GREASE_FILTER_CLOGGED_DP_WARN"
    HIGH_OIL_TEMP_THERMOSTAT_CUTOUT = "HIGH_OIL_TEMP_THERMOSTAT_CUTOUT"
    WET_CHEMICAL_SAPONIFICATION_DISCHARGE_TRIP = "WET_CHEMICAL_SAPONIFICATION_DISCHARGE_TRIP"


@dataclass(frozen=True)
class GalleyDeepFatHoodTelemetry:
    cooking_oil_temp_c: float
    grease_filter_dp_pa: float = 110.0
    plenum_flame_detected: bool = False
    manual_release_pulled: bool = False


@dataclass(frozen=True)
class GalleyDeepFatHoodAssessment:
    state: GalleyDeepFatHoodState
    wet_chemical_agent_release_cmd: bool
    galley_power_shunt_trip_cmd: bool
    exhaust_duct_fire_damper_close: bool
    interlock_code: str


class GalleyWetChemicalDeepFatHoodEngine:
    """SOLAS II-2 Reg 10.6.4 & ISO 15371 Galley Deep-Fat Cooking Fire Extinguishing Interlock."""

    @classmethod
    def evaluate(cls, t: GalleyDeepFatHoodTelemetry) -> GalleyDeepFatHoodAssessment:
        if (
            t.cooking_oil_temp_c >= 360.0
            or t.plenum_flame_detected
            or t.manual_release_pulled
        ):
            return GalleyDeepFatHoodAssessment(
                GalleyDeepFatHoodState.WET_CHEMICAL_SAPONIFICATION_DISCHARGE_TRIP,
                True,
                True,
                True,
                "SOLAS_II2_R10_6_4_GALLEY_WET_CHEM_RELEASE_AND_SHUNT_TRIP",
            )
        if t.cooking_oil_temp_c >= 235.0:
            return GalleyDeepFatHoodAssessment(
                GalleyDeepFatHoodState.HIGH_OIL_TEMP_THERMOSTAT_CUTOUT,
                False,
                True,
                False,
                "ISO_15371_DEEP_FAT_FRYER_OVERHEAT_SAFETY_THERMOSTAT_CUTOUT",
            )
        if t.grease_filter_dp_pa >= 250.0:
            return GalleyDeepFatHoodAssessment(
                GalleyDeepFatHoodState.GREASE_FILTER_CLOGGED_DP_WARN,
                False,
                False,
                False,
                "SOLAS_II2_GALLEY_HOOD_GREASE_TRAP_HIGH_DP_CLEANING_WARN",
            )
        return GalleyDeepFatHoodAssessment(
            GalleyDeepFatHoodState.GALLEY_HOOD_EXTRACTION_NOMINAL,
            False,
            False,
            False,
            "NONE",
        )
