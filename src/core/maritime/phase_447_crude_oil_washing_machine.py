"""Phase 447: Crude Oil Washing (COW) & Tank Cleaning Operation (IMO A.446(XI) / MARPOL Annex I)."""

from dataclasses import dataclass
from enum import Enum


class CowSafetyStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    PRESSURE_WARNING = "PRESSURE_WARNING"
    O2_INTERLOCK_TRIP = "O2_INTERLOCK_TRIP"
    STRIPPING_DEFICIT_TRIP = "STRIPPING_DEFICIT_TRIP"
    ROTATION_FAULT = "ROTATION_FAULT"
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"


@dataclass(frozen=True)
class CowTelemetry:
    wash_pressure_bar: float
    inert_gas_o2_vol_pct: float
    stripping_flow_m3_h: float
    washing_flow_m3_h: float
    machine_rotation_deg_s: float
    oil_drain_valve_open: bool = True


@dataclass(frozen=True)
class CowAssessment:
    status: CowSafetyStatus
    is_wash_permitted: bool
    stripping_ratio: float
    pressure_margin_bar: float
    o2_headroom_pct: float
    action_summary: str


class CrudeOilWashingEngine:
    MIN_OPERATING_PRESSURE_BAR: float = 8.0
    MIN_TRIP_PRESSURE_BAR: float = 7.0
    MAX_OPERATING_PRESSURE_BAR: float = 12.0
    MAX_O2_SAFETY_LIMIT_PCT: float = 8.0
    MIN_STRIPPING_RATIO: float = 1.25
    MIN_ROTATION_SPEED_DEG_S: float = 1.0
    MAX_ROTATION_SPEED_DEG_S: float = 3.0

    def evaluate(self, telem: CowTelemetry) -> CowAssessment:
        stripping_ratio = (
            telem.stripping_flow_m3_h / telem.washing_flow_m3_h
            if telem.washing_flow_m3_h > 0
            else 0.0
        )
        pressure_margin = telem.wash_pressure_bar - self.MIN_OPERATING_PRESSURE_BAR
        o2_headroom = self.MAX_O2_SAFETY_LIMIT_PCT - telem.inert_gas_o2_vol_pct

        # IMO A.446(XI) mandatory emergency trip if O2 > 8.0% vol
        if telem.inert_gas_o2_vol_pct > self.MAX_O2_SAFETY_LIMIT_PCT:
            return CowAssessment(
                status=CowSafetyStatus.O2_INTERLOCK_TRIP,
                is_wash_permitted=False,
                stripping_ratio=stripping_ratio,
                pressure_margin_bar=pressure_margin,
                o2_headroom_pct=o2_headroom,
                action_summary="ESD: Tank O2 exceeds 8.0% vol; COW supply trip immediately",
            )

        # Minimum stripping capacity ratio check (>= 1.25 to prevent oil accumulation)
        if stripping_ratio < self.MIN_STRIPPING_RATIO or not telem.oil_drain_valve_open:
            return CowAssessment(
                status=CowSafetyStatus.STRIPPING_DEFICIT_TRIP,
                is_wash_permitted=False,
                stripping_ratio=stripping_ratio,
                pressure_margin_bar=pressure_margin,
                o2_headroom_pct=o2_headroom,
                action_summary="ESD: Stripping ratio < 1.25 or drain shut; risk of tank bottom accumulation",
            )

        # Critical pressure trip
        if telem.wash_pressure_bar < self.MIN_TRIP_PRESSURE_BAR:
            return CowAssessment(
                status=CowSafetyStatus.EMERGENCY_SHUTDOWN,
                is_wash_permitted=False,
                stripping_ratio=stripping_ratio,
                pressure_margin_bar=pressure_margin,
                o2_headroom_pct=o2_headroom,
                action_summary="ESD: Wash supply pressure below 7.0 bar trip threshold",
            )

        # Machine rotation speed verification
        if not (self.MIN_ROTATION_SPEED_DEG_S <= telem.machine_rotation_deg_s <= self.MAX_ROTATION_SPEED_DEG_S):
            return CowAssessment(
                status=CowSafetyStatus.ROTATION_FAULT,
                is_wash_permitted=False,
                stripping_ratio=stripping_ratio,
                pressure_margin_bar=pressure_margin,
                o2_headroom_pct=o2_headroom,
                action_summary="FAULT: Cleaning machine rotational speed outside 1.0-3.0 deg/s window",
            )

        # Minor pressure warning
        if telem.wash_pressure_bar < self.MIN_OPERATING_PRESSURE_BAR or telem.wash_pressure_bar > self.MAX_OPERATING_PRESSURE_BAR:
            return CowAssessment(
                status=CowSafetyStatus.PRESSURE_WARNING,
                is_wash_permitted=True,
                stripping_ratio=stripping_ratio,
                pressure_margin_bar=pressure_margin,
                o2_headroom_pct=o2_headroom,
                action_summary="WARN: Wash supply pressure outside nominal 8.0-12.0 bar operating range",
            )

        return CowAssessment(
            status=CowSafetyStatus.OPTIMAL,
            is_wash_permitted=True,
            stripping_ratio=stripping_ratio,
            pressure_margin_bar=pressure_margin,
            o2_headroom_pct=o2_headroom,
            action_summary="NOMINAL: Crude oil washing operating within IMO A.446(XI) parameters",
        )
