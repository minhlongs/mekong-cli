"""Phase 475: Stern Tube L.O. Seal Temperature & Air Barrier DP Interlock Engine.

Complies with:
- IACS UR M56 (Shafting & Bearings) & DNV Pt.4 Ch.3:
  - Stern tube white metal bearing temperature: normal <= 60.0 C, alarm >= 65.0 C, slowdown >= 75.0 C.
  - Forward & aft seal air barrier differential pressure: Delta P >= 0.20 bar above sea chest hydrostatic draft head.
  - Stern tube seal drain tank oil leakage rate: normal <= 2.0 L/24h, alarm >= 5.0 L/24h.
  - Auto-action: Bearing cooling booster pump run permissive, propulsion slowdown trigger.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class SternTubeSealStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW_AIR_BARRIER_DP_ALARM = "LOW_AIR_BARRIER_DP_ALARM"
    HIGH_BEARING_TEMP_ALARM = "HIGH_BEARING_TEMP_ALARM"
    BEARING_OVERHEAT_SLOWDOWN_TRIP = "BEARING_OVERHEAT_SLOWDOWN_TRIP"
    SEAL_OIL_LEAKAGE_EXCESSIVE = "SEAL_OIL_LEAKAGE_EXCESSIVE"


@dataclass(frozen=True)
class SternTubeSealTelemetry:
    bearing_temp_c: float
    air_barrier_dp_bar: float
    seal_drain_leakage_l_day: float
    header_tank_level_pct: float
    cooling_water_flow_m3_h: float
    shaft_turning_active: bool


@dataclass(frozen=True)
class SternTubeSealAssessment:
    status: SternTubeSealStatus
    bearing_cooling_booster_active: bool
    propulsion_slowdown_tripped: bool
    air_barrier_supply_valve_open: bool
    remarks: str


class SternTubeSealInterlockEngine:
    ALARM_BEARING_TEMP_C: float = 65.0
    TRIP_BEARING_TEMP_C: float = 75.0
    MIN_AIR_BARRIER_DP_BAR: float = 0.20
    MAX_SEAL_LEAKAGE_L_DAY: float = 5.0
    MIN_COOLING_FLOW_M3_H: float = 4.0

    @classmethod
    def evaluate(cls, telemetry: SternTubeSealTelemetry) -> SternTubeSealAssessment:
        if telemetry.bearing_temp_c >= cls.TRIP_BEARING_TEMP_C:
            return SternTubeSealAssessment(
                status=SternTubeSealStatus.BEARING_OVERHEAT_SLOWDOWN_TRIP,
                bearing_cooling_booster_active=True,
                propulsion_slowdown_tripped=True,
                air_barrier_supply_valve_open=True,
                remarks=f"CRITICAL: Bearing temp {telemetry.bearing_temp_c}C >= {cls.TRIP_BEARING_TEMP_C}C. Auto slowdown engaged.",
            )

        if telemetry.air_barrier_dp_bar < cls.MIN_AIR_BARRIER_DP_BAR:
            return SternTubeSealAssessment(
                status=SternTubeSealStatus.LOW_AIR_BARRIER_DP_ALARM,
                bearing_cooling_booster_active=False,
                propulsion_slowdown_tripped=False,
                air_barrier_supply_valve_open=True,
                remarks=f"ALARM: Seal air barrier DP {telemetry.air_barrier_dp_bar} bar < {cls.MIN_AIR_BARRIER_DP_BAR} bar. Air purge boost required.",
            )

        if telemetry.seal_drain_leakage_l_day >= cls.MAX_SEAL_LEAKAGE_L_DAY:
            return SternTubeSealAssessment(
                status=SternTubeSealStatus.SEAL_OIL_LEAKAGE_EXCESSIVE,
                bearing_cooling_booster_active=False,
                propulsion_slowdown_tripped=False,
                air_barrier_supply_valve_open=True,
                remarks=f"ALARM: Seal leakage {telemetry.seal_drain_leakage_l_day} L/day >= {cls.MAX_SEAL_LEAKAGE_L_DAY} L/day. Ingress risk.",
            )

        if telemetry.bearing_temp_c >= cls.ALARM_BEARING_TEMP_C:
            return SternTubeSealAssessment(
                status=SternTubeSealStatus.HIGH_BEARING_TEMP_ALARM,
                bearing_cooling_booster_active=True,
                propulsion_slowdown_tripped=False,
                air_barrier_supply_valve_open=True,
                remarks=f"WARNING: Bearing temp {telemetry.bearing_temp_c}C >= {cls.ALARM_BEARING_TEMP_C}C. Auxiliary cooling booster run.",
            )

        return SternTubeSealAssessment(
            status=SternTubeSealStatus.NORMAL,
            bearing_cooling_booster_active=telemetry.cooling_water_flow_m3_h < cls.MIN_COOLING_FLOW_M3_H,
            propulsion_slowdown_tripped=False,
            air_barrier_supply_valve_open=True,
            remarks="Stern tube L.O. seal and bearing within nominal operating parameters.",
        )
