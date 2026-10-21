"""Phase 446: Double-Bottom Fuel Tank Emergency High-Level Radar Overfill Protection.

Compliance:
- SOLAS II-1 Reg 20 & MARPOL Annex I Reg 12A (Oil Fuel Tank Protection)
- USCG 46 CFR 39.2009 (Dual-Level Independent Overfill Prevention)
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TankOverfillTelemetry:
    radar_sounding_pct: float
    independent_high_high_sensor: bool
    bunker_flow_rate_m3_h: float
    manifold_valve_closed: bool
    vent_trunk_pressure_mbar: float


@dataclass(frozen=True)
class TankOverfillAssessment:
    is_safe: bool
    high_level_alarm_95: bool
    high_high_trip_98: bool
    manifold_shutdown_tripped: bool
    vent_overpressure_risk: bool
    time_to_overflow_seconds: float
    active_alarms: List[str]


class TankOverfillEngine:
    HIGH_LEVEL_THRESHOLD_PCT: float = 95.0
    HIGH_HIGH_TRIP_PCT: float = 98.0
    MAX_VENT_PRESSURE_MBAR: float = 25.0
    MIN_VENT_PRESSURE_MBAR: float = -10.0

    def evaluate(
        self, telem: TankOverfillTelemetry, tank_total_capacity_m3: float = 500.0
    ) -> TankOverfillAssessment:
        alarms: List[str] = []
        hl_alarm = telem.radar_sounding_pct >= self.HIGH_LEVEL_THRESHOLD_PCT
        hh_trip = (
            telem.radar_sounding_pct >= self.HIGH_HIGH_TRIP_PCT
            or telem.independent_high_high_sensor
        )

        vent_risk = (
            telem.vent_trunk_pressure_mbar > self.MAX_VENT_PRESSURE_MBAR
            or telem.vent_trunk_pressure_mbar < self.MIN_VENT_PRESSURE_MBAR
        )

        if hh_trip:
            alarms.append("CRITICAL: Tank 98% High-High reached - emergency manifold valve tripped")
        elif hl_alarm:
            alarms.append("WARNING: Tank 95% High-Level warning - reduce bunkering rate")

        if vent_risk:
            alarms.append("WARNING: Vent trunk expansion pressure outside limits (-10 to +25 mbar)")

        # Calculate time to overflow (100% capacity)
        remaining_vol = max(0.0, (100.0 - telem.radar_sounding_pct) / 100.0 * tank_total_capacity_m3)
        if telem.bunker_flow_rate_m3_h > 0 and not telem.manifold_valve_closed:
            seconds_remaining = (remaining_vol / telem.bunker_flow_rate_m3_h) * 3600.0
        else:
            seconds_remaining = float("inf")

        manifold_trip = hh_trip or (seconds_remaining < 60.0 and seconds_remaining != float("inf"))

        is_safe = not hh_trip and not (seconds_remaining < 60.0 and seconds_remaining != float("inf"))

        return TankOverfillAssessment(
            is_safe=is_safe,
            high_level_alarm_95=hl_alarm,
            high_high_trip_98=hh_trip,
            manifold_shutdown_tripped=manifold_trip,
            vent_overpressure_risk=vent_risk,
            time_to_overflow_seconds=round(seconds_remaining, 1),
            active_alarms=alarms,
        )
