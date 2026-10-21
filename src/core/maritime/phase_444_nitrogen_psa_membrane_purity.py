"""Phase 444: Nitrogen PSA Inert Gas Membrane Purity & Low-Pressure Buffer Interlock.

Compliance:
- IMO MSC.98(73) FSS Code Ch.15 (Inert Gas Systems)
- SOLAS II-2 Reg 4.5.5 (Inert Gas Requirements)
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class NitrogenPsaTelemetry:
    oxygen_content_pct: float
    feed_air_pressure_bar: float
    feed_air_temp_celsius: float
    feed_air_dew_point_celsius: float
    buffer_tank_pressure_bar: float


@dataclass(frozen=True)
class NitrogenPsaAssessment:
    is_safe: bool
    oxygen_alarm: bool
    dump_valve_open: bool
    dew_point_high: bool
    buffer_pressure_low_trip: bool
    temperature_out_of_range: bool
    active_alarms: List[str]


class NitrogenPsaEngine:
    MAX_ALARM_O2_PCT: float = 4.0
    MAX_TRIP_O2_PCT: float = 5.0
    MIN_FEED_PRESSURE_BAR: float = 7.0
    MAX_FEED_PRESSURE_BAR: float = 10.0
    MIN_FEED_TEMP_C: float = 35.0
    MAX_FEED_TEMP_C: float = 50.0
    MAX_DEW_POINT_C: float = -35.0
    MIN_TRIP_BUFFER_BAR: float = 4.5

    def evaluate(self, telem: NitrogenPsaTelemetry) -> NitrogenPsaAssessment:
        alarms: List[str] = []
        o2_alarm = telem.oxygen_content_pct > self.MAX_ALARM_O2_PCT
        dump_valve = telem.oxygen_content_pct > self.MAX_TRIP_O2_PCT

        dew_high = telem.feed_air_dew_point_celsius > self.MAX_DEW_POINT_C
        buffer_trip = telem.buffer_tank_pressure_bar < self.MIN_TRIP_BUFFER_BAR
        temp_oor = not (self.MIN_FEED_TEMP_C <= telem.feed_air_temp_celsius <= self.MAX_FEED_TEMP_C)
        feed_press_low = telem.feed_air_pressure_bar < self.MIN_FEED_PRESSURE_BAR

        if dump_valve:
            alarms.append("CRITICAL: N2 purity degraded (>5.0% O2) - dumping to atmosphere")
        elif o2_alarm:
            alarms.append("WARNING: N2 oxygen concentration elevated (>4.0% O2)")

        if buffer_trip:
            alarms.append("CRITICAL: N2 buffer tank pressure collapsed (<4.5 bar)")

        if dew_high:
            alarms.append("WARNING: Compressed air dryer dew point elevated (>-35°C)")

        if temp_oor:
            alarms.append("WARNING: Membrane inlet air temperature out of spec (35-50°C)")

        if feed_press_low:
            alarms.append("WARNING: Feed air pressure below membrane rating (<7.0 bar)")

        is_safe = not (dump_valve or buffer_trip)

        return NitrogenPsaAssessment(
            is_safe=is_safe,
            oxygen_alarm=o2_alarm,
            dump_valve_open=dump_valve,
            dew_point_high=dew_high,
            buffer_pressure_low_trip=buffer_trip,
            temperature_out_of_range=temp_oor,
            active_alarms=alarms,
        )
