"""Maritime Phase 395: Emergency Fire Pump & Sea Suction Priming.

Complies with SOLAS II-2 Reg 10.2.2.4, FSS Code Ch. 12, and IACS UR F20.
Zero mock dependencies, strict physical hydraulics & maritime safety checks.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EmergencyFirePumpInput:
    discharge_flow_rate_m3_h: float = 35.0
    discharge_pressure_bar: float = 3.2
    suction_lift_head_m: float = 3.5
    priming_duration_seconds: float = 65.0
    diesel_fuel_endurance_hours: float = 3.5
    starting_battery_voltage_v: float = 24.8
    ambient_temp_c: float = 18.0


@dataclass
class EmergencyFirePumpResult:
    pump_operational_status: str
    discharge_capacity_compliant: bool
    discharge_pressure_compliant: bool
    suction_priming_compliant: bool
    endurance_compliant: bool
    starting_system_ready: bool
    fire_hose_jets_supported: int
    warnings: List[str] = field(default_factory=list)


class EmergencyFirePumpEngine:
    """Evaluates emergency fire pump hydraulic output, sea suction priming, and autonomy."""

    MIN_CAPACITY_M3_H = 25.0
    MIN_PRESSURE_BAR = 2.7
    MAX_SUCTION_HEAD_M = 4.5
    MAX_PRIMING_TIME_SEC = 180.0
    MIN_FUEL_ENDURANCE_HRS = 3.0
    MIN_BATTERY_VOLTS = 22.0
    NOMINAL_JET_FLOW_M3_H = 12.0

    def evaluate(self, inp: EmergencyFirePumpInput) -> EmergencyFirePumpResult:
        warnings = []
        flow = round(inp.discharge_flow_rate_m3_h, 1)
        pressure = round(inp.discharge_pressure_bar, 2)
        suction = round(inp.suction_lift_head_m, 2)
        prime_sec = round(inp.priming_duration_seconds, 1)
        fuel_hrs = round(inp.diesel_fuel_endurance_hours, 2)
        volts = round(inp.starting_battery_voltage_v, 1)

        # Flow rate check
        capacity_ok = flow >= self.MIN_CAPACITY_M3_H
        if not capacity_ok:
            warnings.append(
                f"INSUFFICIENT FLOW: {flow} m3/h below SOLAS minimum {self.MIN_CAPACITY_M3_H} m3/h"
            )

        # Discharge pressure check (at at least 2 hydrants)
        pressure_ok = pressure >= self.MIN_PRESSURE_BAR
        if not pressure_ok:
            warnings.append(
                f"INSUFFICIENT PRESSURE: {pressure} bar below required {self.MIN_PRESSURE_BAR} bar"
            )

        # Suction lift & automatic priming
        if suction > self.MAX_SUCTION_HEAD_M:
            warnings.append(
                f"EXCESSIVE SUCTION HEAD: {suction}m exceeds 4.5m cavitation limit"
            )
            suction_ok = False
        elif prime_sec > self.MAX_PRIMING_TIME_SEC:
            warnings.append(
                f"PRIMING DELAY: {prime_sec}s exceeds SOLAS 180s limit"
            )
            suction_ok = False
        else:
            suction_ok = True

        # Diesel fuel autonomy
        endurance_ok = fuel_hrs >= self.MIN_FUEL_ENDURANCE_HRS
        if not endurance_ok:
            warnings.append(
                f"FUEL DEFICIT: {fuel_hrs} hrs below mandatory 3.0 hrs continuous operation"
            )

        # Starting battery
        battery_ok = volts >= self.MIN_BATTERY_VOLTS
        if not battery_ok:
            warnings.append(
                f"LOW BATTERY VOLTAGE: {volts}V insufficient for cold start (<22.0V)"
            )

        # Fire hose jets supported
        jets = int(flow // self.NOMINAL_JET_FLOW_M3_H) if pressure_ok else 0

        # Overall status
        if not capacity_ok or not pressure_ok or not suction_ok:
            status = "CRITICAL_DEFECT_NOT_SEAWORTHY"
        elif not endurance_ok or not battery_ok:
            status = "DEGRADED_AUTONOMY_DEFICIT"
        else:
            status = "SEAWORTHY_OPTIMAL"

        return EmergencyFirePumpResult(
            pump_operational_status=status,
            discharge_capacity_compliant=capacity_ok,
            discharge_pressure_compliant=pressure_ok,
            suction_priming_compliant=suction_ok,
            endurance_compliant=endurance_ok,
            starting_system_ready=battery_ok,
            fire_hose_jets_supported=jets,
            warnings=warnings,
        )
