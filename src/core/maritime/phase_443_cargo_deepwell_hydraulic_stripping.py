"""Phase 443: Cargo Tank Deepwell Submerged Pump Hydraulic Header & Stripping Interlock.

Compliance:
- OCIMF & SOLAS II-2 Reg 4 (Cargo Tank Pumping Safety)
- DNV-RU-SHIP Pt.4 Ch.6 (Piping and Pumping Systems)
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DeepwellPumpTelemetry:
    hydraulic_header_pressure_bar: float
    hydraulic_return_pressure_bar: float
    cofferdam_purge_leakage_l_min: float
    cargo_leakage_detected: bool
    hydraulic_oil_ingress: bool
    stripping_suction_pressure_bar: float
    cargo_temp_celsius: float


@dataclass(frozen=True)
class DeepwellPumpAssessment:
    is_safe: bool
    header_pressure_alarm: bool
    header_pressure_trip: bool
    return_overpressure_trip: bool
    cofferdam_seal_leakage_trip: bool
    stripping_cavitation_risk: bool
    recommended_flow_throttle_pct: float
    active_alarms: List[str]


class DeepwellPumpEngine:
    MIN_OPERATING_HEADER_BAR: float = 190.0
    MIN_TRIP_HEADER_BAR: float = 160.0
    MAX_SAFE_RETURN_BAR: float = 25.0
    MAX_TRIP_RETURN_BAR: float = 35.0
    MAX_COFFERDAM_LEAKAGE_L_MIN: float = 0.50
    MIN_STRIPPING_SUCTION_BAR: float = 0.15

    def evaluate(self, telem: DeepwellPumpTelemetry) -> DeepwellPumpAssessment:
        alarms: List[str] = []
        header_alarm = telem.hydraulic_header_pressure_bar < self.MIN_OPERATING_HEADER_BAR
        header_trip = telem.hydraulic_header_pressure_bar < self.MIN_TRIP_HEADER_BAR
        return_trip = telem.hydraulic_return_pressure_bar > self.MAX_TRIP_RETURN_BAR
        return_high = telem.hydraulic_return_pressure_bar > self.MAX_SAFE_RETURN_BAR

        seal_trip = (
            telem.cofferdam_purge_leakage_l_min > self.MAX_COFFERDAM_LEAKAGE_L_MIN
            or telem.cargo_leakage_detected
            or telem.hydraulic_oil_ingress
        )
        cavitation = telem.stripping_suction_pressure_bar < self.MIN_STRIPPING_SUCTION_BAR

        if header_trip:
            alarms.append("CRITICAL: Deepwell hydraulic header pressure below trip limit (<160 bar)")
        elif header_alarm:
            alarms.append("WARNING: Hydraulic header pressure low (<190 bar)")

        if return_trip:
            alarms.append("CRITICAL: Hydraulic return line severe backpressure trip (>35 bar)")
        elif return_high:
            alarms.append("WARNING: Hydraulic return line backpressure elevated (>25 bar)")

        if seal_trip:
            alarms.append("CRITICAL: Cofferdam seal failure or fluid ingress detected")

        if cavitation:
            alarms.append("WARNING: Stripping suction pressure low - pump cavitation risk")

        is_safe = not (header_trip or return_trip or seal_trip)

        throttle = 0.0
        if not is_safe:
            throttle = 100.0
        elif cavitation:
            throttle = 40.0
        elif header_alarm or return_high:
            throttle = 25.0

        return DeepwellPumpAssessment(
            is_safe=is_safe,
            header_pressure_alarm=header_alarm,
            header_pressure_trip=header_trip,
            return_overpressure_trip=return_trip,
            cofferdam_seal_leakage_trip=seal_trip,
            stripping_cavitation_risk=cavitation,
            recommended_flow_throttle_pct=throttle,
            active_alarms=alarms,
        )
