"""Phase 491: ME Thrust Bearing Pad Temperature & Oil Wedge Film Protection.

Compliant with IACS UR M3 & M10.
Monitors white-metal pad temperature, hydrodynamic wedge oil pressure,
and shaft axial displacement to prevent catastrophic bearing wipeout.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class ThrustBearingStatus(str, Enum):
    NORMAL = "normal"
    PAD_TEMP_HIGH_ALARM = "pad_temp_high_alarm"
    PAD_TEMP_SLOWDOWN_TRIP = "pad_temp_slowdown_trip"
    OIL_FILM_PRESSURE_LOW = "oil_film_pressure_low"
    AXIAL_DISPLACEMENT_TRIP = "axial_displacement_trip"


@dataclass(frozen=True)
class ThrustBearingTelemetry:
    ahead_pad_temp_c: float
    astern_pad_temp_c: float
    oil_wedge_pressure_bar: float
    shaft_axial_displacement_mm: float
    standby_booster_pump_available: bool = True


@dataclass(frozen=True)
class ThrustBearingAssessment:
    status: ThrustBearingStatus
    slowdown_trip_command: bool
    standby_pump_command: bool
    bearing_safe: bool
    remarks: str


class ThrustBearingPadTempEngine:
    """IACS UR M3/M10 ME Thrust Bearing Safety Evaluation Engine."""

    MAX_PAD_TEMP_TRIP_C = 85.0
    HIGH_PAD_TEMP_ALARM_C = 80.0
    MIN_OIL_PRESSURE_BAR = 0.8
    MAX_AXIAL_DISPLACEMENT_MM = 1.2

    @classmethod
    def evaluate(cls, telem: ThrustBearingTelemetry) -> ThrustBearingAssessment:
        max_pad_temp = max(telem.ahead_pad_temp_c, telem.astern_pad_temp_c)

        # 1. Critical axial displacement trip (bearing white metal failure / collar runout)
        if abs(telem.shaft_axial_displacement_mm) >= cls.MAX_AXIAL_DISPLACEMENT_MM:
            return ThrustBearingAssessment(
                status=ThrustBearingStatus.AXIAL_DISPLACEMENT_TRIP,
                slowdown_trip_command=True,
                standby_pump_command=False,
                bearing_safe=False,
                remarks=f"Shaft axial displacement {telem.shaft_axial_displacement_mm:.2f} mm exceeds {cls.MAX_AXIAL_DISPLACEMENT_MM} mm limit",
            )

        # 2. White-metal pad overtemperature trip
        if max_pad_temp >= cls.MAX_PAD_TEMP_TRIP_C:
            return ThrustBearingAssessment(
                status=ThrustBearingStatus.PAD_TEMP_SLOWDOWN_TRIP,
                slowdown_trip_command=True,
                standby_pump_command=False,
                bearing_safe=False,
                remarks=f"Thrust pad temperature {max_pad_temp:.1f} °C >= {cls.MAX_PAD_TEMP_TRIP_C} °C slowdown trip threshold",
            )

        # 3. Hydrodynamic wedge lube oil pressure loss
        if telem.oil_wedge_pressure_bar < cls.MIN_OIL_PRESSURE_BAR:
            return ThrustBearingAssessment(
                status=ThrustBearingStatus.OIL_FILM_PRESSURE_LOW,
                slowdown_trip_command=not telem.standby_booster_pump_available,
                standby_pump_command=telem.standby_booster_pump_available,
                bearing_safe=False,
                remarks=f"Wedge oil pressure {telem.oil_wedge_pressure_bar:.2f} bar below {cls.MIN_OIL_PRESSURE_BAR} bar minimum",
            )

        # 4. High pad temperature pre-alarm
        if max_pad_temp >= cls.HIGH_PAD_TEMP_ALARM_C:
            return ThrustBearingAssessment(
                status=ThrustBearingStatus.PAD_TEMP_HIGH_ALARM,
                slowdown_trip_command=False,
                standby_pump_command=False,
                bearing_safe=True,
                remarks=f"Thrust pad temperature {max_pad_temp:.1f} °C elevated above warning {cls.HIGH_PAD_TEMP_ALARM_C} °C",
            )

        return ThrustBearingAssessment(
            status=ThrustBearingStatus.NORMAL,
            slowdown_trip_command=False,
            standby_pump_command=False,
            bearing_safe=True,
            remarks=f"Thrust bearing nominal. Max temp: {max_pad_temp:.1f} °C, pressure: {telem.oil_wedge_pressure_bar:.2f} bar",
        )
