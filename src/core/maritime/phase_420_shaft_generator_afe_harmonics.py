"""Phase 420: Shaft Generator Active Front End (AFE) Harmonics & Grid Quality.

Implements IACS UR E24, IEEE 519-2022, and DNV Pt.4 Ch.8 standards for marine
Shaft Generator AFE variable-frequency converters: Total Harmonic Distortion (THD_V <= 5.0%),
individual harmonic limits (5th, 7th, 11th <= 3.0%), voltage unbalance, Grid Fault
Ride-Through (GFRT), and anti-motoring reverse power protection breaker trip.
Strictly < 200 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List
import math


@dataclass(frozen=True)
class ShaftGeneratorAfeTelemetry:
    """Telemetry readings for Shaft Generator AFE Converter and Busbar."""
    bus_voltage_v: float = 440.0
    nominal_voltage_v: float = 440.0
    grid_frequency_hz: float = 60.02
    nominal_frequency_hz: float = 60.0
    active_power_kw: float = 1850.0
    rated_power_kw: float = 2200.0
    reactive_power_kvar: float = 420.0
    harmonic_5th_pct: float = 1.4
    harmonic_7th_pct: float = 1.1
    harmonic_11th_pct: float = 0.8
    harmonic_13th_pct: float = 0.5
    voltage_unbalance_pct: float = 0.85
    voltage_dip_duration_ms: float = 0.0
    reverse_power_duration_s: float = 0.0


@dataclass(frozen=True)
class ShaftGeneratorAfeAssessment:
    """Power quality, harmonic distortion, and breaker protection assessment."""
    thd_voltage_pct: float
    power_factor: float
    individual_harmonics_compliant: bool
    thd_compliant: bool
    voltage_unbalance_compliant: bool
    gfrt_ride_through_active: bool
    reverse_power_trip_active: bool
    breaker_status: str
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class ShaftGeneratorAfeHarmonicsEngine:
    """Evaluates Shaft Gen AFE harmonic distortion, grid quality, and trip interlocks."""

    MAX_THD_PCT: float = 5.0
    MAX_INDIVIDUAL_HARMONIC_PCT: float = 3.0
    MAX_VOLTAGE_UNBALANCE_PCT: float = 2.0
    MAX_GFRT_DURATION_MS: float = 150.0
    REVERSE_POWER_TRIP_THRESHOLD_PCT: float = -5.0
    REVERSE_POWER_TRIP_DELAY_S: float = 3.0

    def evaluate(self, telemetry: ShaftGeneratorAfeTelemetry) -> ShaftGeneratorAfeAssessment:
        warnings: List[str] = []

        # Total Harmonic Distortion: THD = sqrt(sum(V_h^2))
        harmonic_sum_sq = (
            telemetry.harmonic_5th_pct ** 2
            + telemetry.harmonic_7th_pct ** 2
            + telemetry.harmonic_11th_pct ** 2
            + telemetry.harmonic_13th_pct ** 2
        )
        thd_v = math.sqrt(harmonic_sum_sq)

        # Power factor cos(phi) = P / S = P / sqrt(P^2 + Q^2)
        apparent_power_kva = math.sqrt(
            telemetry.active_power_kw ** 2 + telemetry.reactive_power_kvar ** 2
        )
        pf = (
            abs(telemetry.active_power_kw) / apparent_power_kva
            if apparent_power_kva > 1e-3
            else 1.0
        )

        ind_compliant = (
            telemetry.harmonic_5th_pct <= self.MAX_INDIVIDUAL_HARMONIC_PCT
            and telemetry.harmonic_7th_pct <= self.MAX_INDIVIDUAL_HARMONIC_PCT
            and telemetry.harmonic_11th_pct <= self.MAX_INDIVIDUAL_HARMONIC_PCT
            and telemetry.harmonic_13th_pct <= self.MAX_INDIVIDUAL_HARMONIC_PCT
        )
        thd_compliant = thd_v <= self.MAX_THD_PCT
        unbalance_compliant = telemetry.voltage_unbalance_pct <= self.MAX_VOLTAGE_UNBALANCE_PCT

        if not thd_compliant:
            warnings.append(
                f"Bus THD_V exceeds IACS limit: {thd_v:.2f}% (limit <= {self.MAX_THD_PCT:.1f}%)"
            )
        if not ind_compliant:
            warnings.append(
                f"Individual harmonic component exceeds limit <= {self.MAX_INDIVIDUAL_HARMONIC_PCT:.1f}%"
            )
        if not unbalance_compliant:
            warnings.append(
                f"Voltage unbalance exceeds limit: {telemetry.voltage_unbalance_pct:.2f}% "
                f"(limit <= {self.MAX_VOLTAGE_UNBALANCE_PCT:.1f}%)"
            )

        # Grid Fault Ride-Through (GFRT)
        gfrt_active = (
            telemetry.voltage_dip_duration_ms > 0.0
            and telemetry.voltage_dip_duration_ms <= self.MAX_GFRT_DURATION_MS
        )
        if telemetry.voltage_dip_duration_ms > self.MAX_GFRT_DURATION_MS:
            warnings.append(
                f"Voltage dip exceeded GFRT limit: {telemetry.voltage_dip_duration_ms:.1f} ms "
                f"(limit {self.MAX_GFRT_DURATION_MS:.1f} ms) - Grid Trip"
            )

        # Reverse Power Protection (Anti-motoring): P / P_rated < -5% for > 3.0 s
        power_ratio_pct = (telemetry.active_power_kw / telemetry.rated_power_kw) * 100.0
        is_reverse_power = power_ratio_pct <= self.REVERSE_POWER_TRIP_THRESHOLD_PCT
        reverse_trip = (
            is_reverse_power
            and telemetry.reverse_power_duration_s >= self.REVERSE_POWER_TRIP_DELAY_S
        )

        if reverse_trip:
            warnings.append(
                f"Shaft Generator Reverse Power Trip activated! Power {power_ratio_pct:.1f}% "
                f"for {telemetry.reverse_power_duration_s:.1f}s"
            )

        breaker_open = reverse_trip or (
            telemetry.voltage_dip_duration_ms > self.MAX_GFRT_DURATION_MS
        )
        breaker_status = "TRIPPED_OPEN" if breaker_open else "CLOSED_CONNECTED"

        if breaker_open:
            status = "TRIP_PROTECTED"
        elif not (thd_compliant and ind_compliant and unbalance_compliant):
            status = "HARMONIC_WARNING"
        elif gfrt_active:
            status = "GFRT_RIDING_THROUGH"
        else:
            status = "AFE_STABLE"

        compliance_flags = {
            "thd_within_limits": thd_compliant,
            "individual_harmonics_within_limits": ind_compliant,
            "voltage_unbalance_ok": unbalance_compliant,
            "gfrt_supported": not (telemetry.voltage_dip_duration_ms > self.MAX_GFRT_DURATION_MS),
            "no_reverse_power_trip": not reverse_trip,
            "breaker_closed": not breaker_open,
        }

        return ShaftGeneratorAfeAssessment(
            thd_voltage_pct=round(thd_v, 2),
            power_factor=round(pf, 3),
            individual_harmonics_compliant=ind_compliant,
            thd_compliant=thd_compliant,
            voltage_unbalance_compliant=unbalance_compliant,
            gfrt_ride_through_active=gfrt_active,
            reverse_power_trip_active=reverse_trip,
            breaker_status=breaker_status,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
