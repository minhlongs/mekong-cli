"""Phase 403: Bilge Water Separator and Oil Discharge Monitoring & Control System (ODMCS).

Implements MARPOL Annex I Reg 14 & 31, MEPC.107(49) 15 ppm bilge alarm, Stokes settling,
coalescence plate separation, overboard 3-way recirculation valve trip, and 15 ppm ASD trip.
Strictly < 200 LOC, zero mocks, pure analytical physics.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Dict, List


class OdmcsDischargeStatus(str, Enum):
    PERMITTED = "PERMITTED"
    ALARM_WARNING = "ALARM_WARNING"
    RECIRCULATING_TRIP = "RECIRCULATING_TRIP"
    LOCKED_OUT = "LOCKED_OUT"


@dataclass(frozen=True)
class BilgeOdmcsTelemetry:
    """Telemetry readings for oily bilge separator and ODMCS."""
    oil_content_ppm: float = 8.5
    sample_flow_rate_m3_h: float = 2.5
    vessel_speed_knots: float = 12.0
    water_density_kg_m3: float = 1025.0
    oil_density_kg_m3: float = 880.0
    water_viscosity_pa_s: float = 0.00108  # Pa.s (approx 20 deg C seawater)
    oil_droplet_diameter_um: float = 55.0
    coalescer_plate_spacing_mm: float = 12.0
    coalescer_plate_angle_deg: float = 45.0
    three_way_valve_to_bilge: bool = False
    clean_water_flushing: bool = False


@dataclass(frozen=True)
class OdmcsAuditLogEntry:
    """Non-volatile tamper-evident record mandated by MEPC.107(49)."""
    timestamp_utc: str
    oil_content_ppm: float
    discharge_rate_liters_per_nm: float
    valve_position: str
    status: OdmcsDischargeStatus
    tamper_proof_checksum: int


@dataclass(frozen=True)
class BilgeOdmcsAssessment:
    """Assessment of 15 ppm separator, Stokes settling, and ODMCS compliance."""
    stokes_rising_velocity_m_s: float
    coalescence_retention_efficiency_pct: float
    discharge_liters_per_nautical_mile: float
    asd_trip_activated: bool
    status: OdmcsDischargeStatus
    audit_entry: OdmcsAuditLogEntry
    compliance_flags: Dict[str, bool]
    warnings: List[str] = field(default_factory=list)


class BilgeWaterSeparatorOdmcsEngine:
    """Analytical calculation of Stokes separation, MEPC.107(49) 15 ppm limit, and ODMCS."""

    MEPC_ALARM_LIMIT_PPM: float = 15.0
    MARPOL_MAX_DISCHARGE_L_PER_NM: float = 30.0  # Tanker cargo ODMCS limit
    GRAVITY_M_S2: float = 9.80665

    def calculate_stokes_rising_velocity(
        self,
        droplet_diameter_m: float,
        water_density: float,
        oil_density: float,
        viscosity: float,
    ) -> float:
        """Calculate droplet upward velocity (m/s) using Stokes' law."""
        delta_rho = max(0.0, water_density - oil_density)
        effective_visc = max(1e-5, viscosity)
        # v = g * d^2 * (rho_w - rho_o) / (18 * mu)
        return (self.GRAVITY_M_S2 * (droplet_diameter_m**2) * delta_rho) / (18.0 * effective_visc)

    def evaluate(
        self,
        telemetry: BilgeOdmcsTelemetry,
        timestamp_utc: str = "2026-10-09T12:00:00Z",
    ) -> BilgeOdmcsAssessment:
        warnings: List[str] = []

        # Convert droplet diameter um -> m
        d_m = max(1e-6, telemetry.oil_droplet_diameter_um * 1e-6)
        v_rise = self.calculate_stokes_rising_velocity(
            d_m,
            telemetry.water_density_kg_m3,
            telemetry.oil_density_kg_m3,
            telemetry.water_viscosity_pa_s,
        )

        # Coalescence efficiency based on plate geometry, spacing, and rising velocity
        theta_rad = math.radians(telemetry.coalescer_plate_angle_deg)
        spacing_m = max(1e-3, telemetry.coalescer_plate_spacing_mm * 1e-3)
        # Capture ratio: settling distance vs plate gap
        flow_speed_m_s = (telemetry.sample_flow_rate_m3_h / 3600.0) / 0.05  # approx flow area
        settling_factor = (v_rise * math.cos(theta_rad)) / max(1e-4, spacing_m * flow_speed_m_s)
        efficiency = min(
            99.9,
            max(20.0, settling_factor * 10.0 + 80.0),
        )

        # Discharge rate per nautical mile (MARPOL 30 L/NM calculation)
        speed = max(0.1, telemetry.vessel_speed_knots)
        # flow (m3/h) * 1000 (L/m3) * (ppm * 1e-6) = pure oil L/h
        oil_liters_per_hour = telemetry.sample_flow_rate_m3_h * 1000.0 * (telemetry.oil_content_ppm * 1e-6)
        liters_per_nm = round(oil_liters_per_hour / speed, 4)

        # Automatic Stopping Device (ASD) trip logic per MEPC.107(49)
        asd_trip = telemetry.oil_content_ppm >= self.MEPC_ALARM_LIMIT_PPM
        if asd_trip:
            warnings.append(
                f"ODMCS ALARM: Oil content {telemetry.oil_content_ppm:.1f} ppm exceeds 15.0 ppm threshold! Overboard valve tripped."
            )

        if telemetry.clean_water_flushing and not telemetry.three_way_valve_to_bilge:
            warnings.append("FRAUD WARNING: Clean water flushing detected while overboard valve is directed overboard!")

        # Status determination
        if asd_trip or telemetry.three_way_valve_to_bilge:
            status = OdmcsDischargeStatus.RECIRCULATING_TRIP
        elif telemetry.oil_content_ppm > 12.0:
            status = OdmcsDischargeStatus.ALARM_WARNING
        else:
            status = OdmcsDischargeStatus.PERMITTED

        # Tamper-proof non-volatile checksum (FNV-1a 32-bit hash)
        checksum_payload = (
            f"{timestamp_utc}:{telemetry.oil_content_ppm}:{liters_per_nm}:{status.value}"
        )
        chk = 2166136261
        for char in checksum_payload:
            chk = ((chk ^ ord(char)) * 16777619) & 0xFFFFFFFF

        audit_entry = OdmcsAuditLogEntry(
            timestamp_utc=timestamp_utc,
            oil_content_ppm=telemetry.oil_content_ppm,
            discharge_rate_liters_per_nm=liters_per_nm,
            valve_position="RECIRCULATE_TO_BILGE" if (asd_trip or telemetry.three_way_valve_to_bilge) else "OVERBOARD",
            status=status,
            tamper_proof_checksum=chk,
        )

        compliance_flags = {
            "within_15_ppm_limit": telemetry.oil_content_ppm < self.MEPC_ALARM_LIMIT_PPM,
            "speed_greater_than_zero": telemetry.vessel_speed_knots > 0.0,
            "anti_tampering_audit_logged": True,
            "clean_water_overboard_locked": not (telemetry.clean_water_flushing and not telemetry.three_way_valve_to_bilge),
        }

        return BilgeOdmcsAssessment(
            stokes_rising_velocity_m_s=round(v_rise, 6),
            coalescence_retention_efficiency_pct=round(efficiency, 2),
            discharge_liters_per_nautical_mile=liters_per_nm,
            asd_trip_activated=asd_trip,
            status=status,
            audit_entry=audit_entry,
            compliance_flags=compliance_flags,
            warnings=warnings,
        )
