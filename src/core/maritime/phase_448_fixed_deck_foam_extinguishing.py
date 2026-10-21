"""Phase 448: Fixed Deck Foam Fire-Extinguishing System for Tankers (SOLAS II-2 Reg 10.8 / FSS Code Ch.14)."""

from dataclasses import dataclass
from enum import Enum


class DeckFoamStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    INDUCTION_WARNING = "INDUCTION_WARNING"
    INDUCTION_FAULT = "INDUCTION_FAULT"
    PRESSURE_DEFICIT_FAULT = "PRESSURE_DEFICIT_FAULT"
    APPLICATION_RATE_DEFICIT = "APPLICATION_RATE_DEFICIT"
    DURATION_DEPLETED = "DURATION_DEPLETED"


@dataclass(frozen=True)
class DeckFoamTelemetry:
    foam_solution_rate_l_min_m2: float
    induction_ratio_pct: float
    monitor_pressure_bar: float
    throw_distance_m: float
    foam_reserve_duration_min: float
    isolation_valves_open: bool = True


@dataclass(frozen=True)
class DeckFoamAssessment:
    status: DeckFoamStatus
    is_ready_or_effective: bool
    throw_margin_m: float
    duration_headroom_min: float
    action_summary: str


class DeckFoamFireSystemEngine:
    MIN_APPLICATION_RATE_L_MIN_M2: float = 0.60
    MIN_INDUCTION_RATIO_PCT: float = 2.70
    MAX_INDUCTION_RATIO_PCT: float = 3.30
    CRITICAL_MIN_INDUCTION_PCT: float = 2.40
    CRITICAL_MAX_INDUCTION_PCT: float = 3.60
    MIN_MONITOR_PRESSURE_BAR: float = 6.00
    MIN_THROW_DISTANCE_M: float = 50.00
    MIN_REQUIRED_DURATION_MIN: float = 20.00

    def evaluate(self, telem: DeckFoamTelemetry) -> DeckFoamAssessment:
        throw_margin = telem.throw_distance_m - self.MIN_THROW_DISTANCE_M
        duration_headroom = telem.foam_reserve_duration_min - self.MIN_REQUIRED_DURATION_MIN

        # Check reserve duration (SOLAS/FSS Code Ch.14 >= 20 mins required)
        if telem.foam_reserve_duration_min < self.MIN_REQUIRED_DURATION_MIN:
            return DeckFoamAssessment(
                status=DeckFoamStatus.DURATION_DEPLETED,
                is_ready_or_effective=False,
                throw_margin_m=throw_margin,
                duration_headroom_min=duration_headroom,
                action_summary="FAIL: Foam concentrate capacity insufficient (< 20 min autonomous duration)",
            )

        # Check isolation valves and solution rate
        if not telem.isolation_valves_open or telem.foam_solution_rate_l_min_m2 < self.MIN_APPLICATION_RATE_L_MIN_M2:
            return DeckFoamAssessment(
                status=DeckFoamStatus.APPLICATION_RATE_DEFICIT,
                is_ready_or_effective=False,
                throw_margin_m=throw_margin,
                duration_headroom_min=duration_headroom,
                action_summary="FAIL: Deck foam delivery rate < 0.60 L/min/m2 or deck header isolated",
            )

        # Monitor nozzle hydraulic throw & pressure
        if telem.monitor_pressure_bar < self.MIN_MONITOR_PRESSURE_BAR or telem.throw_distance_m < self.MIN_THROW_DISTANCE_M:
            return DeckFoamAssessment(
                status=DeckFoamStatus.PRESSURE_DEFICIT_FAULT,
                is_ready_or_effective=False,
                throw_margin_m=throw_margin,
                duration_headroom_min=duration_headroom,
                action_summary="FAULT: Monitor pressure < 6.0 bar or throw distance < 50.0 m",
            )

        # Proportioning induction ratio critical fault
        if telem.induction_ratio_pct < self.CRITICAL_MIN_INDUCTION_PCT or telem.induction_ratio_pct > self.CRITICAL_MAX_INDUCTION_PCT:
            return DeckFoamAssessment(
                status=DeckFoamStatus.INDUCTION_FAULT,
                is_ready_or_effective=False,
                throw_margin_m=throw_margin,
                duration_headroom_min=duration_headroom,
                action_summary="FAULT: Foam induction ratio outside critical 2.4-3.6% window",
            )

        # Proportioning induction warning (tolerable 2.7-3.3% nominal)
        if telem.induction_ratio_pct < self.MIN_INDUCTION_RATIO_PCT or telem.induction_ratio_pct > self.MAX_INDUCTION_RATIO_PCT:
            return DeckFoamAssessment(
                status=DeckFoamStatus.INDUCTION_WARNING,
                is_ready_or_effective=True,
                throw_margin_m=throw_margin,
                duration_headroom_min=duration_headroom,
                action_summary="WARN: Foam induction ratio deviates slightly from nominal 3.0% (2.7-3.3%)",
            )

        return DeckFoamAssessment(
            status=DeckFoamStatus.OPTIMAL,
            is_ready_or_effective=True,
            throw_margin_m=throw_margin,
            duration_headroom_min=duration_headroom,
            action_summary="NOMINAL: Deck foam system fully compliant with SOLAS II-2 Reg 10.8 & FSS Code",
        )
