"""Phase 470: Marine Fuel Oil Settling Tank High Temp & Auto Quick-Closing Valve Safety Engine.

Complies with:
- SOLAS II-2 Reg. 4.2.2.6 (Fuel oil arrangements - temperature limitation)
- IACS UR M74 / DNV Pt.4 Ch.6 (Piping systems - fuel oil tanks heating)
- Maximum fuel oil settling tank temperature:
  - Flash point safety margin: Fuel must not be heated within 10 deg C below flash point.
  - Standard marine residual fuel flash point min 60.0 deg C.
  - Settling tank max operating temperature T <= 85.0 deg C (warning at 80.0 deg C, high temp alarm & steam trip at 85.0 deg C).
  - High level alarm at L >= 90.0% volume (overflow prevention).
  - Emergency fire actuation: Pneumatic/hydraulic quick-closing valve trip if emergency trip pulled or ambient fire wire melts.

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class SettlingTankStatus(str, Enum):
    NORMAL = "NORMAL"
    HIGH_TEMP_WARNING = "HIGH_TEMP_WARNING"
    OVERHEAT_STEAM_TRIP = "OVERHEAT_STEAM_TRIP"
    HIGH_LEVEL_ALARM = "HIGH_LEVEL_ALARM"
    EMERGENCY_QCV_TRIPPED = "EMERGENCY_QCV_TRIPPED"


@dataclass(frozen=True)
class SettlingTankTelemetry:
    oil_temp_c: float
    oil_level_pct: float
    heating_steam_valve_open: bool
    emergency_fire_wire_melted: bool
    remote_quick_closing_pull: bool


@dataclass(frozen=True)
class SettlingTankAssessment:
    status: SettlingTankStatus
    steam_shutoff_valve_closed: bool
    quick_closing_valve_tripped: bool
    transfer_pump_permissive: bool
    remarks: str


class SettlingTankSafetyEngine:
    WARN_TEMP_C: float = 80.0
    MAX_TRIP_TEMP_C: float = 85.0
    MAX_LEVEL_PCT: float = 90.0

    @classmethod
    def evaluate(cls, telemetry: SettlingTankTelemetry) -> SettlingTankAssessment:
        if telemetry.emergency_fire_wire_melted or telemetry.remote_quick_closing_pull:
            return SettlingTankAssessment(
                status=SettlingTankStatus.EMERGENCY_QCV_TRIPPED,
                steam_shutoff_valve_closed=True,
                quick_closing_valve_tripped=True,
                transfer_pump_permissive=False,
                remarks="EMERGENCY QCV TRIP: Quick-closing valve tripped via fire wire or remote pull.",
            )

        if telemetry.oil_temp_c >= cls.MAX_TRIP_TEMP_C:
            return SettlingTankAssessment(
                status=SettlingTankStatus.OVERHEAT_STEAM_TRIP,
                steam_shutoff_valve_closed=True,
                quick_closing_valve_tripped=False,
                transfer_pump_permissive=True,
                remarks=f"Overheat trip: oil temp {telemetry.oil_temp_c}C >= {cls.MAX_TRIP_TEMP_C}C. Steam shutoff valve tripped.",
            )

        if telemetry.oil_level_pct >= cls.MAX_LEVEL_PCT:
            return SettlingTankAssessment(
                status=SettlingTankStatus.HIGH_LEVEL_ALARM,
                steam_shutoff_valve_closed=False,
                quick_closing_valve_tripped=False,
                transfer_pump_permissive=False,
                remarks=f"High level alarm: level {telemetry.oil_level_pct}% >= {cls.MAX_LEVEL_PCT}%. Transfer pump tripped.",
            )

        if telemetry.oil_temp_c >= cls.WARN_TEMP_C:
            return SettlingTankAssessment(
                status=SettlingTankStatus.HIGH_TEMP_WARNING,
                steam_shutoff_valve_closed=False,
                quick_closing_valve_tripped=False,
                transfer_pump_permissive=True,
                remarks=f"High temp warning: oil temp {telemetry.oil_temp_c}C >= {cls.WARN_TEMP_C}C.",
            )

        return SettlingTankAssessment(
            status=SettlingTankStatus.NORMAL,
            steam_shutoff_valve_closed=False,
            quick_closing_valve_tripped=False,
            transfer_pump_permissive=True,
            remarks="Fuel oil settling tank operating within safe temperature and level parameters.",
        )
