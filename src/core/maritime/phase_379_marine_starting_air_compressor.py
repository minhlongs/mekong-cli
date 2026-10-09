"""Phase 379: Marine Starting Air & Air Reservoir Compressor Automation.

Implements SOLAS Chapter II-1 Reg 26, ClassNK, and DNV machinery rules for main
engine compressed air starting systems under 200 lines.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import List


class EngineReversibility(str, Enum):
    REVERSIBLE = "REVERSIBLE"
    NON_REVERSIBLE = "NON_REVERSIBLE"


@dataclass
class StartingAirInput:
    vessel_id: str
    engine_type: EngineReversibility = EngineReversibility.REVERSIBLE
    working_pressure_bar: float = 30.0
    current_pressure_bar: float = 30.0
    receiver_total_volume_m3: float = 4.0
    air_consumption_per_start_bar: float = 1.2
    compressor_charge_time_min: float = 48.0
    last_drain_elapsed_min: float = 25.0
    moisture_drain_interval_min: float = 30.0
    relief_valve_setting_bar: float = 33.0


@dataclass
class StartingAirReport:
    vessel_id: str
    engine_type: str
    current_pressure_bar: float
    required_starts: int
    available_starts: int
    is_solas_compliant: bool
    is_recharge_time_compliant: bool
    is_emergency_floor_safe: bool
    is_moisture_drain_ok: bool
    system_status: str
    warnings: List[str] = field(default_factory=list)


class MarineStartingAirCompressorEngine:
    """Evaluates main propulsion starting air capacity and compressor automation."""

    EMERGENCY_PRESSURE_FLOOR_BAR: float = 12.0
    LOW_PRESSURE_ALARM_BAR: float = 18.0
    MAX_RECHARGE_TIME_MIN: float = 60.0

    def evaluate(self, inp: StartingAirInput) -> StartingAirReport:
        warnings: List[str] = []

        # 1. SOLAS II-1 Reg 26: 12 starts for reversible, 6 for non-reversible
        req_starts = 12 if inp.engine_type == EngineReversibility.REVERSIBLE else 6

        # Usable pressure above the 12 bar emergency cutoff
        usable_pressure = max(0.0, inp.current_pressure_bar - self.EMERGENCY_PRESSURE_FLOOR_BAR)
        avail_starts = math.floor(usable_pressure / max(0.1, inp.air_consumption_per_start_bar))

        is_solas_ok = avail_starts >= req_starts
        if not is_solas_ok:
            warnings.append(
                f"SOLAS non-compliance: {avail_starts} starts available < {req_starts} required"
            )

        # 2. Emergency floor and low pressure checks
        is_floor_safe = inp.current_pressure_bar >= self.EMERGENCY_PRESSURE_FLOOR_BAR
        if not is_floor_safe:
            warnings.append(
                f"Critical: pressure {inp.current_pressure_bar:.1f} bar below emergency floor (12.0 bar)"
            )
        elif inp.current_pressure_bar < self.LOW_PRESSURE_ALARM_BAR:
            warnings.append(
                f"Warning: low air pressure {inp.current_pressure_bar:.1f} bar (< 18.0 bar threshold)"
            )

        # 3. Dual compressor charging rate (<= 60 min to full pressure)
        is_recharge_ok = inp.compressor_charge_time_min <= self.MAX_RECHARGE_TIME_MIN
        if not is_recharge_ok:
            warnings.append(
                f"Compressor recharge time {inp.compressor_charge_time_min:.1f}m exceeds 60m SOLAS limit"
            )

        # 4. Moisture blowdown interlock
        is_drain_ok = inp.last_drain_elapsed_min <= inp.moisture_drain_interval_min
        if not is_drain_ok:
            warnings.append(
                f"Moisture drain overdue: {inp.last_drain_elapsed_min:.1f}m > {inp.moisture_drain_interval_min:.1f}m interval"
            )

        # 5. Overpressure relief valve check
        if inp.current_pressure_bar > inp.relief_valve_setting_bar:
            warnings.append(
                f"Air receiver overpressure: {inp.current_pressure_bar:.1f} bar > relief setpoint {inp.relief_valve_setting_bar:.1f} bar"
            )

        # Determine overall status
        if not is_floor_safe or inp.current_pressure_bar > inp.relief_valve_setting_bar:
            status = "CRITICAL_ALARM"
        elif not is_solas_ok or not is_recharge_ok or not is_drain_ok:
            status = "WARNING"
        else:
            status = "OPTIMAL"

        return StartingAirReport(
            vessel_id=inp.vessel_id,
            engine_type=inp.engine_type.value,
            current_pressure_bar=round(inp.current_pressure_bar, 2),
            required_starts=req_starts,
            available_starts=avail_starts,
            is_solas_compliant=is_solas_ok,
            is_recharge_time_compliant=is_recharge_ok,
            is_emergency_floor_safe=is_floor_safe,
            is_moisture_drain_ok=is_drain_ok,
            system_status=status,
            warnings=warnings,
        )
