"""Phase 498: Purifier Lube Oil Operating Water Seal & Desludging Separation.

Complies with IACS UR M10 and ClassNK rules for centrifugal oil purifiers.
Monitors bowl water seal integrity, oil-water interface, and moisture transducer.
Strictly <= 95 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class PurifierSealStatus(str, Enum):
    NORMAL_PURIFYING = "normal_purifying"
    STANDBY = "standby"
    BROKEN_WATER_SEAL_TRIP = "broken_water_seal_trip"
    HIGH_MOISTURE_DESLUDGE_TRIGGER = "high_moisture_desludge_trigger"
    LOW_FEED_TEMP_ALARM = "low_feed_temp_alarm"
    SLUDGE_DISCHARGE_SEQUENCE = "sludge_discharge_sequence"


@dataclass(frozen=True)
class PurifierSealTelemetry:
    bowl_speed_rpm: float  # ~7500 - 8500 rpm nominal
    feed_oil_temp_c: float  # 85.0 to 95.0 C nominal for lube oil
    clean_oil_pressure_bar: float  # >= 1.5 bar nominal
    water_outlet_oil_detected: bool  # False in normal operation
    oil_moisture_pct: float  # < 0.5% nominal
    purifier_running: bool = True
    sludge_discharge_active: bool = False


@dataclass(frozen=True)
class PurifierSealAssessment:
    status: PurifierSealStatus
    purifier_safe: bool
    recirculation_valve_diverted: bool
    desludge_cycle_command: bool
    operating_water_shot_command: bool
    description: str


class PurifierLubeOilWaterSealEngine:
    """Evaluates centrifugal lube oil purifier water seal and separation stability."""

    @staticmethod
    def evaluate(t: PurifierSealTelemetry) -> PurifierSealAssessment:
        if not t.purifier_running:
            return PurifierSealAssessment(
                PurifierSealStatus.STANDBY, True, True, False, False,
                "Centrifugal purifier in stopped / standby condition.",
            )
        if t.sludge_discharge_active:
            return PurifierSealAssessment(
                PurifierSealStatus.SLUDGE_DISCHARGE_SEQUENCE, True, True, False, True,
                "Bowl shoot / sludge ejection sequence active with operating water shot.",
            )
        if t.water_outlet_oil_detected or t.clean_oil_pressure_bar < 1.0:
            return PurifierSealAssessment(
                PurifierSealStatus.BROKEN_WATER_SEAL_TRIP, False, True, False, True,
                "Broken water seal: clean oil pressure < 1.0 bar or oil in water outlet. 3-way diverted.",
            )
        if t.feed_oil_temp_c < 80.0:
            return PurifierSealAssessment(
                PurifierSealStatus.LOW_FEED_TEMP_ALARM, True, False, False, False,
                "Feed oil temp < 80.0 C: viscous drag risk, heater modulation required.",
            )
        if t.oil_moisture_pct > 0.5:
            return PurifierSealAssessment(
                PurifierSealStatus.HIGH_MOISTURE_DESLUDGE_TRIGGER, True, False, True, True,
                "Moisture sensor > 0.5%: interface displaced, initiating auto desludging cycle.",
            )
        return PurifierSealAssessment(
            PurifierSealStatus.NORMAL_PURIFYING, True, False, False, False,
            "Purifier water seal intact, clean oil separation nominal.",
        )
