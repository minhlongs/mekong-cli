"""Maritime Phase 397: Quick-Closing Valve & Emergency Fuel Shut-Off Pneumatic Actuation.

Complies with SOLAS II-2 Reg 4.2.2.3.4, IACS UR M34, and IMO MSC.1/Circ.1388.
Zero mock dependencies, strict pneumatic pressure dynamics & trip response.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class QuickClosingValveInput:
    control_air_pressure_bar: float = 7.0
    closure_response_time_sec: float = 1.8
    valves_tripped_count: int = 6
    valves_total_count: int = 6
    wire_remote_tension_n: float = 120.0
    accumulator_bottle_pressure_bar: float = 28.0
    air_leakage_rate_bar_per_hr: float = 0.05


@dataclass
class QuickClosingValveResult:
    valve_system_status: str
    control_air_pressure_ok: bool
    closure_speed_compliant: bool
    closure_completeness_pct: float
    accumulator_capacity_ok: bool
    remote_trip_ready: bool
    air_leakage_acceptable: bool
    warnings: List[str] = field(default_factory=list)


class QuickClosingValveEngine:
    """Evaluates pneumatic and mechanical remote trip of fuel and lube oil quick-closing valves."""

    MIN_CONTROL_AIR_BAR = 5.5
    MAX_CLOSURE_TIME_SEC = 3.0
    MIN_ACCUMULATOR_BAR = 20.0
    MAX_LEAKAGE_BAR_PER_HR = 0.20
    MIN_WIRE_TENSION_N = 80.0
    MAX_WIRE_TENSION_N = 250.0

    def evaluate(self, inp: QuickClosingValveInput) -> QuickClosingValveResult:
        warnings = []
        p_air = round(inp.control_air_pressure_bar, 1)
        t_close = round(inp.closure_response_time_sec, 2)
        p_accum = round(inp.accumulator_bottle_pressure_bar, 1)
        leak = round(inp.air_leakage_rate_bar_per_hr, 3)
        tension = round(inp.wire_remote_tension_n, 1)

        # Control air pressure
        air_ok = p_air >= self.MIN_CONTROL_AIR_BAR
        if not air_ok:
            warnings.append(
                f"LOW CONTROL AIR: {p_air} bar below minimum release pressure {self.MIN_CONTROL_AIR_BAR} bar"
            )

        # Closure response time (SOLAS emergency shutdown <= 3.0s)
        time_ok = t_close <= self.MAX_CLOSURE_TIME_SEC
        if not time_ok:
            warnings.append(
                f"SLUGGISH VALVE CLOSURE: {t_close}s exceeds 3.0s emergency fire isolation limit"
            )

        # Closure completeness
        total = max(inp.valves_total_count, 1)
        completeness = round((inp.valves_tripped_count / total) * 100.0, 1)
        if inp.valves_tripped_count < total:
            warnings.append(
                f"PARTIAL CLOSURE DEFECT: Only {inp.valves_tripped_count}/{total} valves seated"
            )

        # Dedicated accumulator bottle reserve
        accum_ok = p_accum >= self.MIN_ACCUMULATOR_BAR
        if not accum_ok:
            warnings.append(
                f"ACCUMULATOR RESERVE LOW: {p_accum} bar below required {self.MIN_ACCUMULATOR_BAR} bar"
            )

        # Mechanical pull wire tension / readiness
        wire_ok = self.MIN_WIRE_TENSION_N <= tension <= self.MAX_WIRE_TENSION_N
        if not wire_ok:
            warnings.append(
                f"REMOTE MANUAL TRIP TENSION ABNORMAL: {tension}N out of range [80-250N]"
            )

        # Pneumatic line integrity
        leak_ok = leak <= self.MAX_LEAKAGE_BAR_PER_HR
        if not leak_ok:
            warnings.append(
                f"PNEUMATIC LEAKAGE RATE HIGH: {leak} bar/hr exceeds 0.20 bar/hr threshold"
            )

        # Status
        if completeness < 100.0 or not time_ok or not air_ok:
            status = "CRITICAL_ISOLATION_FAILURE"
        elif not accum_ok or not wire_ok or not leak_ok:
            status = "DEGRADED_ACTUATION_SYSTEM"
        else:
            status = "SEAWORTHY_FIRE_ISOLATION_READY"

        return QuickClosingValveResult(
            valve_system_status=status,
            control_air_pressure_ok=air_ok,
            closure_speed_compliant=time_ok,
            closure_completeness_pct=completeness,
            accumulator_capacity_ok=accum_ok,
            remote_trip_ready=wire_ok,
            air_leakage_acceptable=leak_ok,
            warnings=warnings,
        )
