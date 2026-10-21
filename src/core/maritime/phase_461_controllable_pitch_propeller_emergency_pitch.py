"""Phase 461: Controllable Pitch Propeller (CPP) Emergency Pitch Control & Locking.

Compliant with SOLAS II-1 Reg 29 & DNV Rules Pt. 4 Ch. 5 (Propulsion Systems).
Monitors CPP servo oil actuation pressure (P >= 25 bar), mechanical pitch locking pin status,
demanded vs actual pitch angle tracking deviation (|theta_dev| <= 1.5 deg), and dual potentiometer feedback error.
"""

from dataclasses import dataclass
from enum import Enum


class CppEmergencyPitchStatus(str, Enum):
    NORMAL = "NORMAL"
    SERVO_PRESSURE_LOSS = "SERVO_PRESSURE_LOSS"
    PITCH_FEEDBACK_MISMATCH = "PITCH_FEEDBACK_MISMATCH"
    PITCH_FOLLOW_UP_LAG = "PITCH_FOLLOW_UP_LAG"
    EMERGENCY_MANUAL_LOCKED = "EMERGENCY_MANUAL_LOCKED"


@dataclass(frozen=True)
class CppPitchTelemetry:
    servo_oil_pressure_bar: float
    pitch_demanded_deg: float
    pitch_actual_ch_a_deg: float
    pitch_actual_ch_b_deg: float
    emergency_lock_pin_engaged: bool
    manual_hand_pump_active: bool


@dataclass(frozen=True)
class CppPitchAssessment:
    status: CppEmergencyPitchStatus
    pitch_deviation_deg: float
    pitch_tracking_acceptable: bool
    servo_pressure_adequate: bool
    safety_alarm: bool
    fail_as_is_engaged: bool
    remarks: str


class CppEmergencyPitchEngine:
    """SOLAS II-1 Reg 29 CPP Emergency Pitch Control & Safety Locking Logic."""

    MIN_SERVO_PRESSURE_BAR: float = 25.0
    MAX_CHANNEL_MISMATCH_DEG: float = 1.0
    MAX_TRACKING_DEVIATION_DEG: float = 1.5

    @classmethod
    def evaluate(cls, telemetry: CppPitchTelemetry) -> CppPitchAssessment:
        channel_diff = abs(telemetry.pitch_actual_ch_a_deg - telemetry.pitch_actual_ch_b_deg)
        if channel_diff > cls.MAX_CHANNEL_MISMATCH_DEG:
            return CppPitchAssessment(
                status=CppEmergencyPitchStatus.PITCH_FEEDBACK_MISMATCH,
                pitch_deviation_deg=channel_diff,
                pitch_tracking_acceptable=False,
                servo_pressure_adequate=telemetry.servo_oil_pressure_bar >= cls.MIN_SERVO_PRESSURE_BAR,
                safety_alarm=True,
                fail_as_is_engaged=True,
                remarks=f"Dual pitch feedback sensor discrepancy {channel_diff:.2f}° exceeds 1.0° tolerance.",
            )

        mean_actual = (telemetry.pitch_actual_ch_a_deg + telemetry.pitch_actual_ch_b_deg) / 2.0
        tracking_dev = abs(telemetry.pitch_demanded_deg - mean_actual)

        if telemetry.emergency_lock_pin_engaged:
            return CppPitchAssessment(
                status=CppEmergencyPitchStatus.EMERGENCY_MANUAL_LOCKED,
                pitch_deviation_deg=tracking_dev,
                pitch_tracking_acceptable=True,
                servo_pressure_adequate=telemetry.servo_oil_pressure_bar >= cls.MIN_SERVO_PRESSURE_BAR,
                safety_alarm=False,
                fail_as_is_engaged=True,
                remarks="CPP mechanical locking pin engaged: blades secured in emergency ahead pitch position.",
            )

        if telemetry.servo_oil_pressure_bar < cls.MIN_SERVO_PRESSURE_BAR:
            return CppPitchAssessment(
                status=CppEmergencyPitchStatus.SERVO_PRESSURE_LOSS,
                pitch_deviation_deg=tracking_dev,
                pitch_tracking_acceptable=False,
                servo_pressure_adequate=False,
                safety_alarm=True,
                fail_as_is_engaged=True,
                remarks=f"Hydraulic servo oil pressure {telemetry.servo_oil_pressure_bar:.1f} bar below 25 bar limit; fail-freeze active.",
            )

        if tracking_dev > cls.MAX_TRACKING_DEVIATION_DEG:
            return CppPitchAssessment(
                status=CppEmergencyPitchStatus.PITCH_FOLLOW_UP_LAG,
                pitch_deviation_deg=tracking_dev,
                pitch_tracking_acceptable=False,
                servo_pressure_adequate=True,
                safety_alarm=True,
                fail_as_is_engaged=False,
                remarks=f"Pitch follow-up lag {tracking_dev:.2f}° exceeds 1.5° operational threshold.",
            )

        return CppPitchAssessment(
            status=CppEmergencyPitchStatus.NORMAL,
            pitch_deviation_deg=tracking_dev,
            pitch_tracking_acceptable=True,
            servo_pressure_adequate=True,
            safety_alarm=False,
            fail_as_is_engaged=False,
            remarks="CPP hydraulic positioning and follow-up telemetry operating within SOLAS parameters.",
        )
