"""Phase 402: Marine Closed Vapor Emission Control System (VECS / VRU).

Complies with IMO MSC/Circ.585 and USCG 46 CFR Part 39.
Evaluates manifold P/V pressure envelope, oxygen limit, overfill interlocks, and flame arrester DP.
Strictly < 200 LOC, zero-mock deterministic gas dynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class VECSPressureStatus(str, Enum):
    """Vapor manifold pressure state."""
    NOMINAL_SAFE = "NOMINAL_SAFE"
    HIGH_PRESSURE_ALARM = "HIGH_PRESSURE_ALARM"
    HIGH_PRESSURE_TRIP = "HIGH_PRESSURE_TRIP"
    VACUUM_ALARM = "VACUUM_ALARM"
    VACUUM_TRIP = "VACUUM_TRIP"


class OverfillAlarmLevel(str, Enum):
    """Cargo tank overfill protection levels."""
    NORMAL_ULLAGE = "NORMAL_ULLAGE"
    HIGH_LEVEL_95PCT = "HIGH_LEVEL_95PCT"
    HIGH_HIGH_SHUTDOWN_98PCT = "HIGH_HIGH_SHUTDOWN_98PCT"


@dataclass
class VECSInput:
    """Telemetry for marine vapor emission control manifold & cargo tanks."""
    manifold_pressure_bar: float = 0.04
    cargo_level_pct: float = 85.0
    vapor_oxygen_pct: float = 4.5
    arrester_dp_bar: float = 0.02
    arrester_temp_c: float = 28.0
    loading_rate_m3_h: float = 2500.0


@dataclass
class VECSResult:
    """Operational validation and interlock trip status for VECS."""
    pressure_status: VECSPressureStatus
    overfill_level: OverfillAlarmLevel
    oxygen_safe: bool
    arrester_pass: bool
    cargo_loading_permitted: bool
    max_allowable_loading_rate_m3_h: float
    warnings: List[str] = field(default_factory=list)


class VECSEngine:
    """Core physics and safety interlock engine for tanker VECS."""

    HIGH_PRESS_ALARM_BAR = 0.10
    HIGH_PRESS_TRIP_BAR = 0.14
    LOW_VAC_ALARM_BAR = -0.020
    LOW_VAC_TRIP_BAR = -0.035
    MAX_O2_PCT = 8.0
    MAX_ARRESTER_DP_BAR = 0.05
    MAX_ARRESTER_TEMP_C = 60.0

    def evaluate(self, inp: VECSInput) -> VECSResult:
        """Evaluate vapor control pressure, inert gas limits, and overfill trips."""
        warnings: List[str] = []
        trip = False

        # Pressure envelope
        if inp.manifold_pressure_bar >= self.HIGH_PRESS_TRIP_BAR:
            p_status = VECSPressureStatus.HIGH_PRESSURE_TRIP
            trip = True
            warnings.append(
                f"Manifold high pressure trip ({inp.manifold_pressure_bar} bar >= {self.HIGH_PRESS_TRIP_BAR} bar)"
            )
        elif inp.manifold_pressure_bar >= self.HIGH_PRESS_ALARM_BAR:
            p_status = VECSPressureStatus.HIGH_PRESSURE_ALARM
            warnings.append(
                f"Manifold high pressure alarm ({inp.manifold_pressure_bar} bar >= {self.HIGH_PRESS_ALARM_BAR} bar)"
            )
        elif inp.manifold_pressure_bar <= self.LOW_VAC_TRIP_BAR:
            p_status = VECSPressureStatus.VACUUM_TRIP
            trip = True
            warnings.append(
                f"Manifold vacuum trip ({inp.manifold_pressure_bar} bar <= {self.LOW_VAC_TRIP_BAR} bar)"
            )
        elif inp.manifold_pressure_bar <= self.LOW_VAC_ALARM_BAR:
            p_status = VECSPressureStatus.VACUUM_ALARM
            warnings.append(
                f"Manifold vacuum alarm ({inp.manifold_pressure_bar} bar <= {self.LOW_VAC_ALARM_BAR} bar)"
            )
        else:
            p_status = VECSPressureStatus.NOMINAL_SAFE

        # Overfill protection (46 CFR 39.20-9)
        if inp.cargo_level_pct >= 98.0:
            overfill = OverfillAlarmLevel.HIGH_HIGH_SHUTDOWN_98PCT
            trip = True
            warnings.append(f"High-High tank level ({inp.cargo_level_pct}% >= 98%): automated pump trip")
        elif inp.cargo_level_pct >= 95.0:
            overfill = OverfillAlarmLevel.HIGH_LEVEL_95PCT
            warnings.append(f"High tank level warning ({inp.cargo_level_pct}% >= 95%)")
        else:
            overfill = OverfillAlarmLevel.NORMAL_ULLAGE

        # Oxygen concentration limit (< 8.0% vol per IMO MSC/Circ.585)
        o2_safe = inp.vapor_oxygen_pct < self.MAX_O2_PCT
        if not o2_safe:
            trip = True
            warnings.append(
                f"High oxygen in vapor stream ({inp.vapor_oxygen_pct}% >= {self.MAX_O2_PCT}%): explosion risk"
            )

        # Detonation flame arrester integrity
        arrester_ok = (
            inp.arrester_dp_bar <= self.MAX_ARRESTER_DP_BAR
            and inp.arrester_temp_c <= self.MAX_ARRESTER_TEMP_C
        )
        if inp.arrester_dp_bar > self.MAX_ARRESTER_DP_BAR:
            warnings.append(
                f"Flame arrester high DP ({inp.arrester_dp_bar} bar > {self.MAX_ARRESTER_DP_BAR} bar): screen fouling"
            )
            if inp.arrester_dp_bar > 0.08:
                trip = True
        if inp.arrester_temp_c > self.MAX_ARRESTER_TEMP_C:
            trip = True
            warnings.append(
                f"Flame arrester high temp ({inp.arrester_temp_c} C > {self.MAX_ARRESTER_TEMP_C} C): flash back detected"
            )

        loading_permitted = not trip
        max_rate = inp.loading_rate_m3_h if loading_permitted else 0.0

        return VECSResult(
            pressure_status=p_status,
            overfill_level=overfill,
            oxygen_safe=o2_safe,
            arrester_pass=arrester_ok,
            cargo_loading_permitted=loading_permitted,
            max_allowable_loading_rate_m3_h=max_rate,
            warnings=warnings,
        )
