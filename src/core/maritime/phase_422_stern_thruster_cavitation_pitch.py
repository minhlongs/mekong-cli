"""Phase 422: Stern Thruster Tunnel Grate & CPP Pitch Cavitation Inception.

Implements DNV-RU-SHIP Pt.4 Ch.5 and ITTC Cavitation Inception criteria for marine
tunnel thrusters: hydrodynamic suction intake head losses, debris grate drag Delta-P,
cavitation inception index (sigma >= 0.85), high-frequency acoustic shock sensors
(10-40 kHz), and automatic CPP blade pitch derating to arrest cavitation erosion.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class SternThrusterCavitationTelemetry:
    """Telemetry readings for Stern Thruster Tunnel and CPP Propeller."""
    thruster_rpm: float = 240.0
    commanded_pitch_deg: float = 18.5
    actual_pitch_deg: float = 18.5
    max_pitch_deg: float = 25.0
    tunnel_water_velocity_m_s: float = 4.5
    propeller_tip_radius_m: float = 0.65
    submergence_depth_m: float = 4.5
    water_temperature_c: float = 24.0
    ambient_barometric_kpa: float = 101.3
    grate_differential_pressure_bar: float = 0.08
    acoustic_noise_10_40khz_db: float = 18.2
    vibration_velocity_rms_mm_s: float = 3.2


@dataclass(frozen=True)
class SternThrusterCavitationAssessment:
    """Hydrodynamic intake, cavitation inception, and pitch derate assessment."""
    cavitation_number_sigma: float
    tunnel_intake_head_loss_kpa: float
    grate_clogged: bool
    cavitation_inception_detected: bool
    recommended_pitch_deg: float
    acoustic_noise_alert: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class SternThrusterCavitationEngine:
    """Evaluates tunnel hydrodynamics, grate losses, cavitation index, and derate control."""

    CRITICAL_SIGMA_THRESHOLD: float = 0.85
    MAX_GRATE_DELTA_P_BAR: float = 0.35
    MAX_ACOUSTIC_NOISE_DB: float = 28.0
    MAX_VIBRATION_RMS_MM_S: float = 7.1  # ISO 10816-3 Zone C boundary
    SEAWATER_DENSITY_KG_M3: float = 1025.0
    GRAVITY_M_S2: float = 9.80665

    def evaluate(self, telemetry: SternThrusterCavitationTelemetry) -> SternThrusterCavitationAssessment:
        warnings: List[str] = []

        # Ambient static pressure at thruster centerline: P_amb = P_atm + rho * g * h
        p_static_pa = (
            (telemetry.ambient_barometric_kpa * 1000.0)
            + (self.SEAWATER_DENSITY_KG_M3 * self.GRAVITY_M_S2 * telemetry.submergence_depth_m)
        )

        # Saturated vapor pressure of seawater: Antoine equation approximation ~ 2.98 kPa at 24C
        # P_vap = 610.78 * exp(17.27 * T / (T + 237.3))
        p_vapor_pa = 610.78 * math.exp(
            (17.27 * telemetry.water_temperature_c) / (telemetry.water_temperature_c + 237.3)
        )

        # Propeller tip speed: v_tip = omega * R = (2 * pi * n / 60) * R
        omega_rad_s = (2.0 * math.pi * telemetry.thruster_rpm) / 60.0
        v_tip_m_s = omega_rad_s * telemetry.propeller_tip_radius_m
        relative_flow_vel_m_s = math.sqrt(v_tip_m_s ** 2 + telemetry.tunnel_water_velocity_m_s ** 2)

        # Cavitation inception index: sigma = (P_static - P_vap) / (0.5 * rho * V_rel^2)
        dynamic_head_pa = 0.5 * self.SEAWATER_DENSITY_KG_M3 * (relative_flow_vel_m_s ** 2)
        sigma = (
            (p_static_pa - p_vapor_pa) / dynamic_head_pa
            if dynamic_head_pa > 1.0
            else 10.0
        )

        # Tunnel inlet & grate head loss: Delta_P = 0.5 * rho * v_tunnel^2 * (K_inlet + zeta_grate)
        k_inlet = 0.25
        zeta_grate = (telemetry.grate_differential_pressure_bar * 100000.0) / (
            0.5 * self.SEAWATER_DENSITY_KG_M3 * (telemetry.tunnel_water_velocity_m_s ** 2 + 1e-4)
        )
        total_head_loss_kpa = (
            0.5 * self.SEAWATER_DENSITY_KG_M3 * (telemetry.tunnel_water_velocity_m_s ** 2) * (k_inlet + max(0.1, zeta_grate))
        ) / 1000.0

        grate_clogged = telemetry.grate_differential_pressure_bar >= self.MAX_GRATE_DELTA_P_BAR
        if grate_clogged:
            warnings.append(
                f"Stern thruster debris grate clogged: Delta-P {telemetry.grate_differential_pressure_bar:.2f} bar "
                f"(limit < {self.MAX_GRATE_DELTA_P_BAR:.2f} bar)"
            )

        acoustic_alert = telemetry.acoustic_noise_10_40khz_db >= self.MAX_ACOUSTIC_NOISE_DB
        if acoustic_alert:
            warnings.append(
                f"High ultrasonic acoustic emission: {telemetry.acoustic_noise_10_40khz_db:.1f} dB "
                f"(threshold < {self.MAX_ACOUSTIC_NOISE_DB:.1f} dB) - Blade tip erosion imminent"
            )

        vibration_alert = telemetry.vibration_velocity_rms_mm_s >= self.MAX_VIBRATION_RMS_MM_S
        if vibration_alert:
            warnings.append(
                f"Thruster casing vibration excessive: {telemetry.vibration_velocity_rms_mm_s:.1f} mm/s "
                f"(ISO threshold < {self.MAX_VIBRATION_RMS_MM_S:.1f} mm/s)"
            )

        cavitation_active = sigma < self.CRITICAL_SIGMA_THRESHOLD or acoustic_alert

        # CPP derate algorithm: If cavitation detected, derate blade pitch
        if cavitation_active:
            derate_factor = max(0.70, sigma / self.CRITICAL_SIGMA_THRESHOLD)
            recommended_pitch = min(telemetry.commanded_pitch_deg, telemetry.commanded_pitch_deg * derate_factor)
            status = "CAVITATING_PITCH_DERATE"
            warnings.append(
                f"Cavitation inception detected (sigma = {sigma:.2f} < {self.CRITICAL_SIGMA_THRESHOLD:.2f}). "
                f"Pitch derated from {telemetry.commanded_pitch_deg:.1f} deg to {recommended_pitch:.1f} deg"
            )
        else:
            recommended_pitch = telemetry.commanded_pitch_deg
            status = "SUB_CAVITATING_OPTIMAL"

        compliance_flags = {
            "cavitation_index_acceptable": sigma >= self.CRITICAL_SIGMA_THRESHOLD,
            "grate_debris_clear": not grate_clogged,
            "acoustic_ultrasound_normal": not acoustic_alert,
            "bearing_vibration_within_iso": not vibration_alert,
        }

        return SternThrusterCavitationAssessment(
            cavitation_number_sigma=round(sigma, 3),
            tunnel_intake_head_loss_kpa=round(total_head_loss_kpa, 2),
            grate_clogged=grate_clogged,
            cavitation_inception_detected=cavitation_active,
            recommended_pitch_deg=round(recommended_pitch, 2),
            acoustic_noise_alert=acoustic_alert,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
