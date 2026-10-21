"""Phase 456: Marine Boiler Feedwater Deaerator & Dissolved Oxygen Scavenging.

Compliant with IACS UR M52 & ASME BPVC Section I.
Regulates thermal deaeration saturation envelope, dissolved oxygen scavenging
limits, hydrazine / sulfite dosing margin, and storage vessel levels.
"""

from dataclasses import dataclass
from enum import Enum


class DeaeratorStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    DEGRADED_SCAVENGING = "DEGRADED_SCAVENGING"
    OXYGEN_CORROSION_RISK = "OXYGEN_CORROSION_RISK"
    TRIP_LEVEL = "TRIP_LEVEL"


@dataclass(frozen=True)
class DeaeratorTelemetry:
    steam_pressure_bar: float
    water_temperature_celsius: float
    dissolved_oxygen_ppb: float
    chemical_reserve_ppm: float
    storage_tank_level_pct: float


@dataclass(frozen=True)
class DeaeratorAssessment:
    status: DeaeratorStatus
    thermal_saturation_compliant: bool
    oxygen_corrosion_risk: bool
    chemical_dosing_required: bool
    storage_level_alarm: bool
    safety_alarm: bool
    remarks: str


class BoilerFeedwaterDeaeratorEngine:
    MIN_SATURATION_TEMP_CELSIUS: float = 104.0
    MAX_DISSOLVED_OXYGEN_PPB: float = 7.0
    MIN_CHEMICAL_RESERVE_PPM: float = 15.0
    MIN_TANK_LEVEL_PCT: float = 20.0
    MAX_TANK_LEVEL_PCT: float = 85.0

    @classmethod
    def evaluate(cls, telemetry: DeaeratorTelemetry) -> DeaeratorAssessment:
        level_alarm = (
            telemetry.storage_tank_level_pct < cls.MIN_TANK_LEVEL_PCT
            or telemetry.storage_tank_level_pct > cls.MAX_TANK_LEVEL_PCT
        )
        if level_alarm:
            return DeaeratorAssessment(
                status=DeaeratorStatus.TRIP_LEVEL,
                thermal_saturation_compliant=False,
                oxygen_corrosion_risk=True,
                chemical_dosing_required=False,
                storage_level_alarm=True,
                safety_alarm=True,
                remarks="Deaerator storage tank level outside 20-85% safe range",
            )

        thermal_ok = telemetry.water_temperature_celsius >= cls.MIN_SATURATION_TEMP_CELSIUS
        o2_ok = telemetry.dissolved_oxygen_ppb <= cls.MAX_DISSOLVED_OXYGEN_PPB
        chem_ok = telemetry.chemical_reserve_ppm >= cls.MIN_CHEMICAL_RESERVE_PPM

        if not o2_ok:
            return DeaeratorAssessment(
                status=DeaeratorStatus.OXYGEN_CORROSION_RISK,
                thermal_saturation_compliant=thermal_ok,
                oxygen_corrosion_risk=True,
                chemical_dosing_required=True,
                storage_level_alarm=False,
                safety_alarm=True,
                remarks="Dissolved oxygen exceeds 7 ppb limit: High economizer pitting risk",
            )

        if not (thermal_ok and chem_ok):
            return DeaeratorAssessment(
                status=DeaeratorStatus.DEGRADED_SCAVENGING,
                thermal_saturation_compliant=thermal_ok,
                oxygen_corrosion_risk=False,
                chemical_dosing_required=not chem_ok,
                storage_level_alarm=False,
                safety_alarm=False,
                remarks="Sub-saturation temperature or low chemical reserve detected",
            )

        return DeaeratorAssessment(
            status=DeaeratorStatus.OPTIMAL,
            thermal_saturation_compliant=True,
            oxygen_corrosion_risk=False,
            chemical_dosing_required=False,
            storage_level_alarm=False,
            safety_alarm=False,
            remarks="Deaerator operating at complete saturation with dissolved O2 <= 7 ppb",
        )
