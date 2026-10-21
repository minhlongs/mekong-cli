"""Phase 481: Boiler Feedwater Deaerator & Condensate Salinity Engine.

Complies with:
- IACS UR M14 & BS 2486 (Boiler water treatment & deaerator criteria):
  - Condensate conductivity: normal <= 5.0 uS/cm.
  - Salinity warning alarm: 5.0 < conductivity <= 10.0 uS/cm.
  - Salinity dump to bilge: conductivity > 10.0 uS/cm.
  - Deaerator pressure band: 0.20 to 0.45 bar.
  - Saturation temperature margin: abs(tsat_c - tactual_c) <= 1.5 C for complete thermal deaeration.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class BoilerFeedwaterStatus(str, Enum):
    NORMAL = "NORMAL"
    SALINITY_HIGH_ALARM = "SALINITY_HIGH_ALARM"
    CONDENSATE_DUMP_TO_BILGE = "CONDENSATE_DUMP_TO_BILGE"
    DEAERATOR_PRESSURE_OUT_OF_RANGE = "DEAERATOR_PRESSURE_OUT_OF_RANGE"
    INSUFFICIENT_DEAERATION_MARGIN = "INSUFFICIENT_DEAERATION_MARGIN"


@dataclass(frozen=True)
class BoilerFeedwaterTelemetry:
    condensate_conductivity_us_cm: float
    deaerator_pressure_bar: float
    tsat_c: float
    tactual_c: float


@dataclass(frozen=True)
class BoilerFeedwaterAssessment:
    status: BoilerFeedwaterStatus
    condensate_dump_valve_open: bool
    salinity_alarm: bool
    deaerator_pressure_normal: bool
    deaeration_saturation_ok: bool
    remarks: str


class BoilerFeedwaterDeaeratorEngine:
    CONDUCTIVITY_WARN_LIMIT: float = 5.0
    CONDUCTIVITY_DUMP_LIMIT: float = 10.0
    DEAERATOR_P_MIN_BAR: float = 0.20
    DEAERATOR_P_MAX_BAR: float = 0.45
    MAX_SUBCOOLING_MARGIN_C: float = 1.5

    @classmethod
    def evaluate(cls, telemetry: BoilerFeedwaterTelemetry) -> BoilerFeedwaterAssessment:
        salinity_alarm = telemetry.condensate_conductivity_us_cm > cls.CONDUCTIVITY_WARN_LIMIT
        pressure_ok = cls.DEAERATOR_P_MIN_BAR <= telemetry.deaerator_pressure_bar <= cls.DEAERATOR_P_MAX_BAR
        subcooling = abs(telemetry.tsat_c - telemetry.tactual_c)
        saturation_ok = subcooling <= cls.MAX_SUBCOOLING_MARGIN_C

        if telemetry.condensate_conductivity_us_cm > cls.CONDUCTIVITY_DUMP_LIMIT:
            return BoilerFeedwaterAssessment(
                status=BoilerFeedwaterStatus.CONDENSATE_DUMP_TO_BILGE,
                condensate_dump_valve_open=True,
                salinity_alarm=True,
                deaerator_pressure_normal=pressure_ok,
                deaeration_saturation_ok=saturation_ok,
                remarks=f"IACS UR M14 CRITICAL: Condensate conductivity {telemetry.condensate_conductivity_us_cm} uS/cm > 10.0 uS/cm. Dumping to bilge.",
            )

        if not pressure_ok:
            return BoilerFeedwaterAssessment(
                status=BoilerFeedwaterStatus.DEAERATOR_PRESSURE_OUT_OF_RANGE,
                condensate_dump_valve_open=False,
                salinity_alarm=salinity_alarm,
                deaerator_pressure_normal=False,
                deaeration_saturation_ok=saturation_ok,
                remarks=f"Deaerator pressure {telemetry.deaerator_pressure_bar} bar outside allowed band [0.20, 0.45 bar].",
            )

        if not saturation_ok:
            return BoilerFeedwaterAssessment(
                status=BoilerFeedwaterStatus.INSUFFICIENT_DEAERATION_MARGIN,
                condensate_dump_valve_open=False,
                salinity_alarm=salinity_alarm,
                deaerator_pressure_normal=True,
                deaeration_saturation_ok=False,
                remarks=f"Incomplete deaeration: subcooling margin {subcooling:.2f} C > 1.5 C. Risk of dissolved O2 pitting.",
            )

        if salinity_alarm:
            return BoilerFeedwaterAssessment(
                status=BoilerFeedwaterStatus.SALINITY_HIGH_ALARM,
                condensate_dump_valve_open=False,
                salinity_alarm=True,
                deaerator_pressure_normal=True,
                deaeration_saturation_ok=True,
                remarks=f"WARNING: Condensate conductivity {telemetry.condensate_conductivity_us_cm} uS/cm > 5.0 uS/cm.",
            )

        return BoilerFeedwaterAssessment(
            status=BoilerFeedwaterStatus.NORMAL,
            condensate_dump_valve_open=False,
            salinity_alarm=False,
            deaerator_pressure_normal=True,
            deaeration_saturation_ok=True,
            remarks="Boiler feedwater purity and deaerator operating conditions nominal.",
        )
