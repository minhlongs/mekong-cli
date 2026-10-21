"""Phase 384: Auxiliary Emergency Steering Gear & Hydraulic Actuation Engine.

Implements SOLAS II-1 Reg 29 & 30, IMO Res. A.1052(27), and classification rules
for main and emergency rudder actuation travel times, failover, and hydraulic integrity.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SteeringGearInput:
    """Input parameters and telemetry for steering gear evaluation."""
    mode: str = "MAIN"  # MAIN, AUXILIARY_EMERGENCY
    current_angle_deg: float = -35.0  # Port 35
    target_angle_deg: float = 30.0    # Starboard 30
    elapsed_time_s: float = 24.5
    vessel_speed_knots: float = 22.0
    max_service_speed_knots: float = 22.0
    hydraulic_pressure_bar: float = 195.0
    working_pressure_bar: float = 200.0
    oil_tank_level_pct: float = 78.0
    main_power_available: bool = True
    emergency_power_active: bool = False
    rudder_demand_diff_deg: float = 1.2
    rudder_demand_diff_duration_s: float = 0.5


@dataclass
class SteeringGearResult:
    """Evaluation result for steering gear compliance and readiness."""
    mode: str
    travel_time_s: float
    time_limit_s: float
    travel_compliant: bool
    failover_ready: bool
    steering_status: str  # OPERATIONAL, DEGRADED, ALARM, TRIPPED
    hydraulic_integrity: str  # NORMAL, LOW_LEVEL, OVERPRESSURE
    warnings: List[str] = field(default_factory=list)


class AuxiliaryEmergencySteeringEngine:
    """Evaluates main and emergency steering gear response times and SOLAS rules."""

    SOLAS_MAIN_TIME_LIMIT_S = 28.0  # 35 deg port to 30 deg stbd at max ahead speed
    SOLAS_EMERGENCY_TIME_LIMIT_S = 60.0  # 15 deg port to 15 deg stbd at half speed or 7 kts
    MIN_OIL_LEVEL_PCT = 40.0
    MAX_RUDDER_HUNTING_DIFF_DEG = 4.0
    MAX_RUDDER_HUNTING_TIME_S = 3.0

    def evaluate(self, telemetry: SteeringGearInput) -> SteeringGearResult:
        warnings: List[str] = []

        # 1. Travel Time Limit determination
        if telemetry.mode.upper() == "MAIN":
            time_limit = self.SOLAS_MAIN_TIME_LIMIT_S
            travel_compliant = telemetry.elapsed_time_s <= time_limit
            if not travel_compliant:
                warnings.append(
                    f"SOLAS II-1 R29 VIOLATION: Main steering travel time {telemetry.elapsed_time_s}s "
                    f"exceeds {time_limit}s limit."
                )
        else:
            time_limit = self.SOLAS_EMERGENCY_TIME_LIMIT_S
            travel_compliant = telemetry.elapsed_time_s <= time_limit
            if not travel_compliant:
                warnings.append(
                    f"SOLAS II-1 R29 VIOLATION: Emergency steering travel time {telemetry.elapsed_time_s}s "
                    f"exceeds {time_limit}s limit."
                )

        # 2. Hydraulic System Integrity
        relief_valve_limit = 1.25 * telemetry.working_pressure_bar
        if telemetry.oil_tank_level_pct < self.MIN_OIL_LEVEL_PCT:
            hydraulic_integrity = "LOW_LEVEL"
            warnings.append(
                f"HYDRAULIC OIL LOW: Header tank {telemetry.oil_tank_level_pct}% < {self.MIN_OIL_LEVEL_PCT}% alarm limit."
            )
        elif telemetry.hydraulic_pressure_bar > relief_valve_limit:
            hydraulic_integrity = "OVERPRESSURE"
            warnings.append(
                f"OVERPRESSURE HAZARD: System pressure {telemetry.hydraulic_pressure_bar} bar "
                f"exceeds relief valve setpoint {relief_valve_limit} bar."
            )
        else:
            hydraulic_integrity = "NORMAL"

        # 3. Rudder hunting & transmitter angle divergence
        if (
            telemetry.rudder_demand_diff_deg > self.MAX_RUDDER_HUNTING_DIFF_DEG
            and telemetry.rudder_demand_diff_duration_s >= self.MAX_RUDDER_HUNTING_TIME_S
        ):
            warnings.append(
                f"STEERING LAG ALARM: Rudder follow-up error {telemetry.rudder_demand_diff_deg} deg "
                f"persisted for {telemetry.rudder_demand_diff_duration_s}s."
            )

        # 4. Power failover readiness
        failover_ready = telemetry.emergency_power_active or telemetry.main_power_available

        # 5. Composite Steering Status
        if not telemetry.main_power_available and not telemetry.emergency_power_active:
            steering_status = "TRIPPED"
            warnings.append("TOTAL POWER LOSS: Steering gear inoperative, blacked out.")
        elif hydraulic_integrity in ("LOW_LEVEL", "OVERPRESSURE") or not travel_compliant:
            steering_status = "ALARM"
        elif not telemetry.main_power_available and telemetry.emergency_power_active:
            steering_status = "DEGRADED"
            warnings.append("EMERGENCY POWER ACTIVE: Operating on emergency switchboard feed.")
        else:
            steering_status = "OPERATIONAL"

        return SteeringGearResult(
            mode=telemetry.mode.upper(),
            travel_time_s=telemetry.elapsed_time_s,
            time_limit_s=time_limit,
            travel_compliant=travel_compliant,
            failover_ready=failover_ready,
            steering_status=steering_status,
            hydraulic_integrity=hydraulic_integrity,
            warnings=warnings,
        )
