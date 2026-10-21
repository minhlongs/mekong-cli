"""Phase 434: Machinery Space Emergency Bilge Suction Direct Valve Interlock.

Implements SOLAS II-1 Reg 35-1 and IACS UR M29:
- Direct emergency bilge suction through largest independent power pump (main SW cooling pump).
- Suction valve bore >= 2/3 of pump inlet branch diameter.
- Extended spindle handwheel above floor plates with open/close mechanical position indicator.
- Bilge high-level (>= 300 mm) warning and critical flooding (>= 600 mm) emergency trip.
Strictly < 160 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EmergencyBilgeTelemetry:
    """Telemetry readings for machinery space bilge well and emergency suction valve."""
    bilge_water_level_mm: float = 120.0
    engine_room_flooding_sensor: bool = False
    emergency_valve_open_pct: float = 0.0
    main_sea_chest_valve_open_pct: float = 100.0
    cooling_pump_running: bool = True
    cooling_pump_capacity_m3_h: float = 1200.0
    suction_pipe_diameter_mm: float = 350.0
    pump_suction_branch_diameter_mm: float = 450.0
    extended_spindle_locked: bool = True


@dataclass(frozen=True)
class EmergencyBilgeAssessment:
    """Emergency suction readiness, flooding severity, and valve interlock assessment."""
    diameter_ratio: float
    valve_sizing_compliant: bool
    bilge_alarm_state: str
    emergency_suction_activated: bool
    sea_chest_interlock_safe: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class EmergencyBilgeSuctionEngine:
    """Evaluates emergency bilge suction valve position, sizing, and flooding interlocks."""

    HIGH_LEVEL_ALARM_MM: float = 300.0
    CRITICAL_FLOODING_ALARM_MM: float = 600.0
    MIN_DIAMETER_RATIO: float = 0.6667  # 2/3 of pump inlet branch

    def evaluate(self, telemetry: EmergencyBilgeTelemetry) -> EmergencyBilgeAssessment:
        warnings: List[str] = []

        diameter_ratio = round(
            telemetry.suction_pipe_diameter_mm / max(1.0, telemetry.pump_suction_branch_diameter_mm), 3
        )
        valve_sizing_compliant = diameter_ratio >= self.MIN_DIAMETER_RATIO
        if not valve_sizing_compliant:
            warnings.append(f"NON_COMPLIANT: Suction bore ratio ({diameter_ratio:.3f} < {self.MIN_DIAMETER_RATIO:.3f})")

        # Bilge flooding alarm state
        if telemetry.bilge_water_level_mm >= self.CRITICAL_FLOODING_ALARM_MM or telemetry.engine_room_flooding_sensor:
            bilge_alarm_state = "CRITICAL_FLOODING_TRIP"
            warnings.append(f"CRITICAL: Engine room flooding ({telemetry.bilge_water_level_mm:.1f} mm >= {self.CRITICAL_FLOODING_ALARM_MM} mm)")
        elif telemetry.bilge_water_level_mm >= self.HIGH_LEVEL_ALARM_MM:
            bilge_alarm_state = "HIGH_BILGE_LEVEL_WARNING"
            warnings.append(f"WARNING: High bilge level ({telemetry.bilge_water_level_mm:.1f} mm >= {self.HIGH_LEVEL_ALARM_MM} mm)")
        else:
            bilge_alarm_state = "NORMAL_LEVEL"

        emergency_suction_activated = telemetry.emergency_valve_open_pct > 0.0 and telemetry.cooling_pump_running

        # Sea chest interlock: when emergency bilge valve opens, main sea chest should be throttled
        sea_chest_interlock_safe = True
        if emergency_suction_activated:
            if telemetry.main_sea_chest_valve_open_pct > 50.0:
                sea_chest_interlock_safe = False
                warnings.append("WARNING: Main sea chest valve still > 50% open during emergency bilge suction")

        if not telemetry.extended_spindle_locked and not emergency_suction_activated:
            warnings.append("NOTICE: Extended spindle handwheel unlocked during nominal voyage")

        if bilge_alarm_state == "CRITICAL_FLOODING_TRIP":
            status = "EMERGENCY_DEWATERING_MANDATORY"
        elif emergency_suction_activated:
            status = "EMERGENCY_BILGE_SUCTION_ACTIVE"
        elif bilge_alarm_state == "HIGH_BILGE_LEVEL_WARNING":
            status = "HIGH_BILGE_MONITORING"
        else:
            status = "STANDBY_READY"

        compliance_flags = {
            "SOLAS_BORE_SIZING": valve_sizing_compliant,
            "SPINDLE_READY": telemetry.extended_spindle_locked or emergency_suction_activated,
            "PUMP_AVAILABLE": telemetry.cooling_pump_running,
            "IACS_UR_M29_COMPLIANT": valve_sizing_compliant and telemetry.cooling_pump_running,
        }

        return EmergencyBilgeAssessment(
            diameter_ratio=diameter_ratio,
            valve_sizing_compliant=valve_sizing_compliant,
            bilge_alarm_state=bilge_alarm_state,
            emergency_suction_activated=emergency_suction_activated,
            sea_chest_interlock_safe=sea_chest_interlock_safe,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
