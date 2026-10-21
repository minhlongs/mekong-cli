"""Phase 385: Automatic Anti-Heeling Ballast Pumping & Counter-Flooding Engine.

Implements IMO Res. MSC.267(85), DNV classification rules, and container cargo
handling safety standards for dynamic list prevention and rapid ballast transfer.
"""

from dataclasses import dataclass, field
import math
from typing import List


@dataclass
class AntiHeelingInput:
    """Input telemetry for container vessel anti-heeling ballast control."""
    current_heel_deg: float = 0.8  # Positive = Starboard, Negative = Port
    heel_rate_deg_s: float = 0.05  # d(theta)/dt
    displacement_tonnes: float = 85000.0
    gm_transverse_m: float = 1.85
    port_tank_level_pct: float = 65.0
    starboard_tank_level_pct: float = 35.0
    pump_capacity_m3_h: float = 1200.0
    pump_operational: bool = True
    valve_reversal_time_s: float = 6.5


@dataclass
class AntiHeelingResult:
    """Evaluation result for vessel heeling stability and pump response."""
    restoring_moment_kn_m: float
    target_pump_action: str  # IDLE, PUMP_PORT_TO_STBD, PUMP_STBD_TO_PORT, EMERGENCY_STOP
    operational_status: str  # SAFE, LIST_WARNING, CRITICAL_SHUTDOWN
    rapid_response_triggered: bool
    pump_flow_demand_m3_h: float
    warnings: List[str] = field(default_factory=list)


class AntiHeelingBallastEngine:
    """Evaluates container vessel list angle and commands rapid counter-ballasting."""

    MAX_STATIC_LIST_SAFE_DEG = 1.0
    LIST_WARNING_DEG = 1.5
    CRANE_EMERGENCY_STOP_DEG = 2.5
    RAPID_HEEL_RATE_TRIGGER_DEG_S = 0.15
    MIN_TANK_LEVEL_PCT = 5.0   # Cavitation interlock
    MAX_TANK_LEVEL_PCT = 95.0  # Overfill interlock

    def evaluate(self, telemetry: AntiHeelingInput) -> AntiHeelingResult:
        warnings: List[str] = []
        abs_heel = abs(telemetry.current_heel_deg)

        # 1. Restoring Moment Calculation: M = Delta * g * GM * sin(theta)
        # 1 tonne * 9.80665 m/s^2 = 9.80665 kN
        theta_rad = math.radians(telemetry.current_heel_deg)
        restoring_moment = round(
            telemetry.displacement_tonnes * 9.80665 * telemetry.gm_transverse_m * math.sin(theta_rad), 1
        )

        # 2. Dynamic Rapid Heel Rate trigger
        rapid_response_triggered = abs(telemetry.heel_rate_deg_s) >= self.RAPID_HEEL_RATE_TRIGGER_DEG_S
        if rapid_response_triggered:
            warnings.append(
                f"RAPID LIST RATE: Rate {telemetry.heel_rate_deg_s} deg/s >= "
                f"{self.RAPID_HEEL_RATE_TRIGGER_DEG_S} deg/s trigger limit."
            )

        # 3. Overall Operational Status
        if abs_heel >= self.CRANE_EMERGENCY_STOP_DEG:
            operational_status = "CRITICAL_SHUTDOWN"
            warnings.append(
                f"CONTAINER CRANE SHUTDOWN: Heel {abs_heel} deg >= {self.CRANE_EMERGENCY_STOP_DEG} deg limit."
            )
        elif abs_heel > self.LIST_WARNING_DEG:
            operational_status = "LIST_WARNING"
            warnings.append(
                f"LIST WARNING: Heel {abs_heel} deg exceeds normal operation limit {self.LIST_WARNING_DEG} deg."
            )
        else:
            operational_status = "SAFE"

        # 4. Target Ballast Pump Action & Interlocks
        # If listed to starboard (> 0), pump from STBD to PORT to restore upright
        # If listed to port (< 0), pump from PORT to STBD
        target_action = "IDLE"
        flow_demand = 0.0

        if not telemetry.pump_operational:
            target_action = "EMERGENCY_STOP"
            warnings.append("ANTI-HEELING PUMP FAULT: Main ballast pump unavailable.")
        elif abs_heel >= self.CRANE_EMERGENCY_STOP_DEG:
            target_action = "EMERGENCY_STOP"
        elif abs_heel > self.MAX_STATIC_LIST_SAFE_DEG or rapid_response_triggered:
            if telemetry.current_heel_deg > 0:
                # Starboard list -> Transfer to Port
                if (
                    telemetry.starboard_tank_level_pct <= self.MIN_TANK_LEVEL_PCT
                    or telemetry.port_tank_level_pct >= self.MAX_TANK_LEVEL_PCT
                ):
                    target_action = "IDLE"
                    warnings.append("BALLAST INTERLOCK: Tank boundary limits reached during stbd correction.")
                else:
                    target_action = "PUMP_STBD_TO_PORT"
                    flow_demand = telemetry.pump_capacity_m3_h
            else:
                # Port list -> Transfer to Starboard
                if (
                    telemetry.port_tank_level_pct <= self.MIN_TANK_LEVEL_PCT
                    or telemetry.starboard_tank_level_pct >= self.MAX_TANK_LEVEL_PCT
                ):
                    target_action = "IDLE"
                    warnings.append("BALLAST INTERLOCK: Tank boundary limits reached during port correction.")
                else:
                    target_action = "PUMP_PORT_TO_STBD"
                    flow_demand = telemetry.pump_capacity_m3_h

        return AntiHeelingResult(
            restoring_moment_kn_m=restoring_moment,
            target_pump_action=target_action,
            operational_status=operational_status,
            rapid_response_triggered=rapid_response_triggered,
            pump_flow_demand_m3_h=flow_demand,
            warnings=warnings,
        )
