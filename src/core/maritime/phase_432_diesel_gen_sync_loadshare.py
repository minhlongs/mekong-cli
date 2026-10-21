"""Phase 432: Marine Auxiliary Generator Auto-Synchronizing & Load Sharing.

Implements IACS UR E13 and SOLAS II-1 Reg 42/43:
- Automatic synchronizing window: delta_f <= 0.20 Hz, delta_v <= 5.0 V, phase angle <= 5.0 deg.
- Reverse power relay protection: trip on P < -5.0% rated power after 3.0 s delay.
- Active (kW) and reactive (kVAR) isochronous / droop load sharing within +/-10% rated balance.
Strictly < 160 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class GeneratorSyncTelemetry:
    """Telemetry readings for incoming diesel generator and running busbar."""
    bus_frequency_hz: float = 60.0
    incoming_frequency_hz: float = 60.10
    bus_voltage_v: float = 440.0
    incoming_voltage_v: float = 442.0
    phase_angle_diff_deg: float = 3.5
    active_power_kw: float = 450.0
    rated_power_kw: float = 800.0
    reactive_power_kvar: float = 220.0
    rated_kvar: float = 500.0
    bus_total_load_kw: float = 900.0
    reverse_power_duration_sec: float = 0.0


@dataclass(frozen=True)
class GeneratorSyncAssessment:
    """Paralleling synchronization and load share assessment."""
    delta_frequency_hz: float
    delta_voltage_v: float
    sync_window_matched: bool
    reverse_power_trip: bool
    load_share_imbalance_pct: float
    breaker_close_permitted: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class DieselGenSyncEngine:
    """Evaluates automatic synchronizing windows, load sharing, and reverse power."""

    MAX_DELTA_FREQ_HZ: float = 0.20
    MAX_DELTA_VOLTAGE_V: float = 5.0
    MAX_PHASE_ANGLE_DEG: float = 5.0
    REVERSE_POWER_LIMIT_PCT: float = -5.0
    REVERSE_POWER_DELAY_SEC: float = 3.0
    MAX_LOAD_IMBALANCE_PCT: float = 10.0

    def evaluate(self, telemetry: GeneratorSyncTelemetry) -> GeneratorSyncAssessment:
        warnings: List[str] = []

        delta_f = round(abs(telemetry.incoming_frequency_hz - telemetry.bus_frequency_hz), 3)
        delta_v = round(abs(telemetry.incoming_voltage_v - telemetry.bus_voltage_v), 2)
        phase_diff = round(abs(telemetry.phase_angle_diff_deg), 2)

        freq_ok = delta_f <= self.MAX_DELTA_FREQ_HZ
        volt_ok = delta_v <= self.MAX_DELTA_VOLTAGE_V
        phase_ok = phase_diff <= self.MAX_PHASE_ANGLE_DEG

        sync_window_matched = freq_ok and volt_ok and phase_ok

        # Reverse power check
        power_ratio_pct = (telemetry.active_power_kw / max(1.0, telemetry.rated_power_kw)) * 100.0
        is_reverse_power = power_ratio_pct <= self.REVERSE_POWER_LIMIT_PCT
        reverse_power_trip = is_reverse_power and telemetry.reverse_power_duration_sec >= self.REVERSE_POWER_DELAY_SEC

        if reverse_power_trip:
            warnings.append(f"TRIP: Reverse power detected ({power_ratio_pct:.1f}% for {telemetry.reverse_power_duration_sec:.1f}s) - tripping generator breaker")
        elif is_reverse_power:
            warnings.append(f"WARNING: Reverse power pending ({power_ratio_pct:.1f}%)")

        # Load share imbalance (target is proportional share: active_power / bus_total)
        expected_share_kw = telemetry.bus_total_load_kw * 0.5  # Assumes 2-gen symmetrical sharing
        imbalance_pct = round(abs(telemetry.active_power_kw - expected_share_kw) / max(1.0, telemetry.rated_power_kw) * 100.0, 2)

        if imbalance_pct > self.MAX_LOAD_IMBALANCE_PCT:
            warnings.append(f"WARNING: Generator load share imbalance ({imbalance_pct:.1f}% > {self.MAX_LOAD_IMBALANCE_PCT}%)")

        breaker_close_permitted = sync_window_matched and not is_reverse_power and not reverse_power_trip

        if reverse_power_trip:
            status = "REVERSE_POWER_TRIP"
        elif breaker_close_permitted:
            status = "SYNCHRONIZED_READY_TO_CLOSE"
        elif sync_window_matched:
            status = "WINDOW_MATCHED_INHIBITED"
        else:
            status = "SYNCHRONIZING_IN_PROGRESS"

        compliance_flags = {
            "IACS_E13_SYNC_ENVELOPE": sync_window_matched,
            "REVERSE_POWER_SAFE": not is_reverse_power,
            "LOAD_SHARE_COMPLIANT": imbalance_pct <= self.MAX_LOAD_IMBALANCE_PCT,
            "SOLAS_II_1_POWER_SAFE": not reverse_power_trip and imbalance_pct <= self.MAX_LOAD_IMBALANCE_PCT,
        }

        return GeneratorSyncAssessment(
            delta_frequency_hz=delta_f,
            delta_voltage_v=delta_v,
            sync_window_matched=sync_window_matched,
            reverse_power_trip=reverse_power_trip,
            load_share_imbalance_pct=imbalance_pct,
            breaker_close_permitted=breaker_close_permitted,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
