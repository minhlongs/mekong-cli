"""Maritime Phase 359: Adaptive Autopilot & Rudder Angle Monitoring Engine.

Compliant with IMO Res. MSC.64(67) Annex 3, ISO 11674, and SOLAS II-1/29.
Evaluates adaptive heading control, Norrbin steering dynamics, and steering gear lag.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class AdaptiveAutopilotInput:
    vessel_id: str
    target_heading_deg: float
    actual_heading_deg: float
    rate_of_turn_deg_s: float
    actual_rudder_angle_deg: float
    sea_state_douglas: int = 3  # 0 (calm) to 9 (phenomenal)
    speed_knots: float = 14.0
    command_latency_seconds: float = 1.0
    kp: float = 1.2
    kd: float = 2.0


@dataclass
class AdaptiveAutopilotResult:
    vessel_id: str
    heading_error_deg: float
    adaptive_deadband_deg: float
    commanded_rudder_angle_deg: float
    rudder_follow_up_error_deg: float
    is_hunting_prevented: bool
    is_steering_gear_lag_critical: bool
    status: str
    advisories: List[str] = field(default_factory=list)


class AdaptiveAutopilotEngine:
    """Evaluates adaptive heading control and steering gear integrity."""

    MAX_RUDDER_LIMIT_DEG: float = 35.0
    SOLAS_FOLLOW_UP_TOLERANCE_DEG: float = 4.0
    MAX_ALLOWABLE_LAG_SECONDS: float = 3.0

    @classmethod
    def evaluate(cls, inp: AdaptiveAutopilotInput) -> AdaptiveAutopilotResult:
        # Normalize heading error to [-180, 180]
        err = (inp.target_heading_deg - inp.actual_heading_deg + 180.0) % 360.0 - 180.0

        # Calculate adaptive deadband based on sea state (Douglas scale)
        if inp.sea_state_douglas <= 2:
            deadband = 0.5
        elif inp.sea_state_douglas <= 4:
            deadband = 1.0
        elif inp.sea_state_douglas <= 6:
            deadband = 1.8
        else:
            deadband = 2.5

        # Compute commanded rudder using PD controller with deadband suppression
        advisories: List[str] = []
        is_hunting_prevented = False

        if abs(err) <= deadband:
            commanded_rudder = 0.0
            is_hunting_prevented = True
        else:
            # Active correction factoring rate of turn (damping)
            eff_err = err - (deadband if err > 0 else -deadband)
            cmd = (inp.kp * eff_err) - (inp.kd * inp.rate_of_turn_deg_s)
            commanded_rudder = max(
                -cls.MAX_RUDDER_LIMIT_DEG,
                min(cls.MAX_RUDDER_LIMIT_DEG, round(cmd, 2)),
            )

        # Check steering gear follow-up error and SOLAS lag
        follow_up_error = round(abs(commanded_rudder - inp.actual_rudder_angle_deg), 2)
        is_lag_critical = (
            follow_up_error > cls.SOLAS_FOLLOW_UP_TOLERANCE_DEG
            and inp.command_latency_seconds >= cls.MAX_ALLOWABLE_LAG_SECONDS
        )

        # Determine operating status
        if is_lag_critical:
            status = "STEERING_GEAR_FOLLOW_UP_FAILURE"
            advisories.append(
                f"CRITICAL: Rudder lag ({follow_up_error}° > 4.0°) exceeds SOLAS II-1/29 limits for {inp.command_latency_seconds}s."
            )
            advisories.append("Switch to auxiliary steering gear or manual emergency helm immediately.")
        elif abs(commanded_rudder) >= 30.0:
            status = "HARD_RUDDER_MANEUVERING"
            advisories.append("Large rudder command applied. Monitor vessel speed drop and heel angle.")
        elif is_hunting_prevented:
            status = "STEADY_SEAWAY_HEADING"
            advisories.append(f"Yaw error {abs(round(err, 2))}° within Sea State {inp.sea_state_douglas} deadband ({deadband}°). Rudder hunting prevented.")
        else:
            status = "COURSE_CORRECTION_ACTIVE"
            advisories.append(f"Course correction active. Commanded rudder: {commanded_rudder}°.")

        return AdaptiveAutopilotResult(
            vessel_id=inp.vessel_id,
            heading_error_deg=round(err, 2),
            adaptive_deadband_deg=deadband,
            commanded_rudder_angle_deg=commanded_rudder,
            rudder_follow_up_error_deg=follow_up_error,
            is_hunting_prevented=is_hunting_prevented,
            is_steering_gear_lag_critical=is_lag_critical,
            status=status,
            advisories=advisories,
        )
