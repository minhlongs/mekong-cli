"""Phase 415: Propeller CPP & OD Box Hydraulics.

Implements DNV Pt.4 Ch.5 and SOLAS II-1 Reg 28 / Reg 31 standards for Controllable
Pitch Propeller (CPP) systems: servo oil pressure differential, pitch angle control,
Oil Distribution (OD) box dynamic seal leakage, advance ratio J, and emergency lock-pin.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class CppPropellerTelemetry:
    """Telemetry readings for CPP and OD Box Hydraulics."""
    commanded_pitch_deg: float = 18.0
    actual_pitch_deg: float = 17.8
    servo_port_a_pressure_bar: float = 48.0
    servo_port_b_pressure_bar: float = 22.0
    shaft_speed_rpm: float = 120.0
    ship_speed_knots: float = 15.0
    propeller_diameter_m: float = 4.2
    odbox_seal_differential_bar: float = 2.5
    hydraulic_oil_viscosity_cst: float = 46.0
    emergency_lock_pin_engaged: bool = False


@dataclass(frozen=True)
class CppPropellerAssessment:
    """Hydrodynamic thrust and hydraulic integrity assessment of CPP."""
    advance_ratio_j: float
    differential_servo_pressure_bar: float
    thrust_coefficient_kt: float
    thrust_force_kn: float
    torque_kilonewton_meters: float
    odbox_seal_leakage_lpm: float
    pitch_tracking_error_deg: float
    fail_safe_locked: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class CppPropellerOdBoxEngine:
    """Evaluates CPP pitch positioning, open water hydrodynamics, and OD box seals."""

    MIN_SERVO_DELTA_P_BAR: float = 8.0
    MAX_SERVO_DELTA_P_BAR: float = 75.0
    MAX_PITCH_ERROR_DEG: float = 1.5
    MAX_ODBOX_LEAKAGE_LPM: float = 3.5
    SEAWATER_DENSITY_KG_M3: float = 1025.0

    def evaluate(self, telemetry: CppPropellerTelemetry) -> CppPropellerAssessment:
        warnings: List[str] = []
        delta_p = telemetry.servo_port_a_pressure_bar - telemetry.servo_port_b_pressure_bar
        pitch_error = abs(telemetry.commanded_pitch_deg - telemetry.actual_pitch_deg)

        # Hydrodynamics: Advance ratio J = Va / (n * D)
        va_m_s = telemetry.ship_speed_knots * 0.514444 * 0.75  # wake fraction correction ~0.75
        rps = max(0.1, telemetry.shaft_speed_rpm / 60.0)
        d = max(0.5, telemetry.propeller_diameter_m)
        j = va_m_s / (rps * d)

        # Simplified Wageningen B-series approximation for Kt and Kq
        # Kt ≈ 0.35 * (P/D) - 0.25 * J; P/D roughly proportional to pitch angle in deg / 15.0
        pitch_ratio = max(0.2, telemetry.actual_pitch_deg / 15.0)
        kt = max(0.01, 0.38 * pitch_ratio - 0.26 * j)
        kq = max(0.005, 0.052 * pitch_ratio - 0.031 * j)

        # Thrust T = rho * n^2 * D^4 * Kt (N)
        thrust_n = self.SEAWATER_DENSITY_KG_M3 * (rps ** 2) * (d ** 4) * kt
        thrust_kn = thrust_n / 1000.0

        # Torque Q = rho * n^2 * D^5 * Kq (N.m)
        torque_nm = self.SEAWATER_DENSITY_KG_M3 * (rps ** 2) * (d ** 5) * kq
        torque_kn_m = torque_nm / 1000.0

        # OD box leakage: laminar annular clearance q = (pi * d * c^3 * deltaP) / (12 * mu * L)
        # Scaled engineering formulation in liters per minute
        mu_pa_s = max(0.01, telemetry.hydraulic_oil_viscosity_cst * 0.88 / 1000.0)
        leakage_lpm = max(0.05, (0.018 * abs(telemetry.odbox_seal_differential_bar)) / mu_pa_s)

        if pitch_error > self.MAX_PITCH_ERROR_DEG:
            warnings.append(
                f"High pitch tracking deviation: commanded {telemetry.commanded_pitch_deg}°, "
                f"actual {telemetry.actual_pitch_deg}° (error {pitch_error:.2f}° > {self.MAX_PITCH_ERROR_DEG}°)."
            )

        if abs(delta_p) < self.MIN_SERVO_DELTA_P_BAR and not telemetry.emergency_lock_pin_engaged:
            warnings.append(
                f"Insufficient servo differential pressure {abs(delta_p):.1f} bar (< {self.MIN_SERVO_DELTA_P_BAR} bar)."
            )

        if abs(delta_p) > self.MAX_SERVO_DELTA_P_BAR:
            warnings.append(
                f"Servo overpressure surge {abs(delta_p):.1f} bar (> {self.MAX_SERVO_DELTA_P_BAR} bar)."
            )

        if leakage_lpm > self.MAX_ODBOX_LEAKAGE_LPM:
            warnings.append(
                f"OD Box dynamic seal leakage excessive {leakage_lpm:.2f} LPM (> {self.MAX_ODBOX_LEAKAGE_LPM} LPM)."
            )

        if telemetry.emergency_lock_pin_engaged:
            warnings.append("CPP emergency ahead mechanical lock-pin is ENGAGED. Pitch fixed for ahead propulsion.")

        status = "OPTIMAL"
        if telemetry.emergency_lock_pin_engaged:
            status = "FAILSAFE_ENGAGED"
        elif leakage_lpm > self.MAX_ODBOX_LEAKAGE_LPM or pitch_error > self.MAX_PITCH_ERROR_DEG * 2:
            status = "CRITICAL"
        elif warnings:
            status = "WARNING"

        compliance_flags = {
            "solas_ii1_reg28_ahead_astern_capable": not telemetry.emergency_lock_pin_engaged or telemetry.actual_pitch_deg > 0,
            "dnv_pt4_servo_pressure_adequate": abs(delta_p) >= self.MIN_SERVO_DELTA_P_BAR,
            "dnv_pt4_odbox_seal_integrity": leakage_lpm <= self.MAX_ODBOX_LEAKAGE_LPM,
            "pitch_tracking_within_tolerance": pitch_error <= self.MAX_PITCH_ERROR_DEG,
        }

        return CppPropellerAssessment(
            advance_ratio_j=round(j, 4),
            differential_servo_pressure_bar=round(delta_p, 2),
            thrust_coefficient_kt=round(kt, 4),
            thrust_force_kn=round(thrust_kn, 2),
            torque_kilonewton_meters=round(torque_kn_m, 2),
            odbox_seal_leakage_lpm=round(leakage_lpm, 3),
            pitch_tracking_error_deg=round(pitch_error, 2),
            fail_safe_locked=telemetry.emergency_lock_pin_engaged,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
