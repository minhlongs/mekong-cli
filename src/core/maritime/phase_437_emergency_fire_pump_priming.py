"""Phase 437: Emergency Fire Pump Independent Suction & Priming Interlock.

Implements SOLAS II-2 Reg 10.2.2.3.1.2 & IACS UR F28:
- Discharge delivery pressure head (minimum >= 2.7 bar / 0.27 N/mm2 under full flow).
- Priming time under design maximum suction lift (light ship draft <= 30.0 s, vacuum <= -0.6 bar).
- Diesel prime mover independent fuel autonomy (>= 3.0 hours full load run time).
Strictly < 150 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class EmergencyFirePumpTelemetry:
    """Telemetry readings for emergency fire pump suction, prime, and discharge pressure."""
    discharge_pressure_bar: float = 3.2   # Required >= 2.7 bar
    suction_vacuum_bar: float = -0.65     # Gauge vacuum achieved during priming (<= -0.6 bar)
    priming_time_s: float = 18.5          # Measured time to prime (<= 30.0 s)
    suction_lift_m: float = 3.8           # Static suction lift from sea water level (<= 4.5 m)
    water_flow_m3_h: float = 45.0         # Minimum delivered flow capacity
    diesel_fuel_hours_remaining: float = 4.5  # Fuel autonomy at 100% MCR (>= 3.0 h)
    engine_rpm: float = 1800.0
    casing_flooded: bool = True           # Casing water presence detected by optical sensor


@dataclass(frozen=True)
class EmergencyFirePumpAssessment:
    """Readiness, priming efficiency, and delivery head compliance assessment."""
    pressure_compliant: bool
    priming_compliant: bool
    fuel_compliant: bool
    pump_operational_ready: bool
    status: str
    warnings: List[str]
    compliance_flags: Dict[str, bool]


class EmergencyFirePumpEngine:
    """Evaluates emergency fire pump suction performance and SOLAS compliance."""

    MIN_DISCHARGE_PRESS_BAR: float = 2.70
    MAX_PRIMING_TIME_S: float = 30.0
    MIN_VACUUM_BAR: float = -0.60
    MAX_SUCTION_LIFT_M: float = 4.5
    MIN_FUEL_AUTONOMY_HOURS: float = 3.0

    def evaluate(self, telemetry: EmergencyFirePumpTelemetry) -> EmergencyFirePumpAssessment:
        warnings: List[str] = []

        press_ok = telemetry.discharge_pressure_bar >= self.MIN_DISCHARGE_PRESS_BAR
        prime_time_ok = telemetry.priming_time_s <= self.MAX_PRIMING_TIME_S
        vac_ok = telemetry.suction_vacuum_bar <= self.MIN_VACUUM_BAR
        lift_ok = telemetry.suction_lift_m <= self.MAX_SUCTION_LIFT_M
        fuel_ok = telemetry.diesel_fuel_hours_remaining >= self.MIN_FUEL_AUTONOMY_HOURS

        priming_ok = prime_time_ok and vac_ok and lift_ok and telemetry.casing_flooded

        if not press_ok:
            warnings.append(f"Discharge pressure below SOLAS limit ({telemetry.discharge_pressure_bar:.2f} < {self.MIN_DISCHARGE_PRESS_BAR} bar)")
        if not prime_time_ok:
            warnings.append(f"Priming took too long ({telemetry.priming_time_s:.1f} > {self.MAX_PRIMING_TIME_S} s)")
        if not vac_ok:
            warnings.append(f"Priming vacuum insufficient ({telemetry.suction_vacuum_bar:.2f} > {self.MIN_VACUUM_BAR} bar)")
        if not lift_ok:
            warnings.append(f"Suction lift exceeds design ({telemetry.suction_lift_m:.1f} > {self.MAX_SUCTION_LIFT_M} m)")
        if not fuel_ok:
            warnings.append(f"Emergency fuel autonomy low ({telemetry.diesel_fuel_hours_remaining:.1f} < {self.MIN_FUEL_AUTONOMY_HOURS} h)")
        if not telemetry.casing_flooded:
            warnings.append("Pump casing dry — suction line loss of prime detected")

        ready = press_ok and priming_ok and fuel_ok

        if ready:
            status = "SOLAS_EMERGENCY_READY"
        elif not priming_ok:
            status = "PRIMING_FAILURE_CHECK_SUCTION"
        elif not press_ok:
            status = "LOW_DISCHARGE_PRESSURE_ALARM"
        else:
            status = "INSUFFICIENT_FUEL_RESERVE"

        compliance_flags = {
            "SOLAS_II_2_REG10_COMPLIANT": ready,
            "IACS_UR_F28_HEAD_SATISFIED": press_ok,
            "PRIMING_WITHIN_30S": prime_time_ok,
            "THREE_HOUR_FUEL_AUTONOMY": fuel_ok,
        }

        return EmergencyFirePumpAssessment(
            pressure_compliant=press_ok,
            priming_compliant=priming_ok,
            fuel_compliant=fuel_ok,
            pump_operational_ready=ready,
            status=status,
            warnings=warnings,
            compliance_flags=compliance_flags,
        )
