"""Phase 410: Marine Emergency Diesel Generator (EDG) 45s Blackout Sequence.

Complies with SOLAS II-1 Reg 42 / 43 and IACS UR M35.
Monitors dead ship blackout transient state machine, cranking air/battery energy,
frequency and voltage ramp timing, and emergency bus breaker closure within 45 seconds.
Strictly < 180 LOC, zero mocks, deterministic timing & electro-mechanical evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class EdgBlackoutStatus(str, Enum):
    """Governing operational state for marine emergency power restoration."""
    BLACKOUT_STANDBY = "BLACKOUT_STANDBY"
    EDG_STARTING_RAMP = "EDG_STARTING_RAMP"
    EMERGENCY_BUS_CONNECTED = "EMERGENCY_BUS_CONNECTED"
    CRANKING_FAILURE_TRIP = "CRANKING_FAILURE_TRIP"
    OVER_TIME_SOLAS_VIOLATION = "OVER_TIME_SOLAS_VIOLATION"
    LOW_STARTING_ENERGY_LOCKOUT = "LOW_STARTING_ENERGY_LOCKOUT"


@dataclass
class EdgBlackoutInput:
    """Transient state and telemetry for dead ship blackout response."""
    msb_voltage_volts: float = 0.0  # Main Switchboard bus voltage (nominal 440V)
    blackout_elapsed_sec: float = 18.5  # Seconds since initial loss of main power
    starting_air_pressure_bar: float = 24.0  # EDG air start bottle pressure (min 18 bar)
    starter_battery_volts: float = 26.2  # 24V starter battery bank terminal voltage (min 23.0 V)
    edg_frequency_hz: float = 60.0  # EDG alternator output frequency (nominal 60.0 Hz)
    edg_voltage_volts: float = 442.0  # EDG alternator terminal voltage (nominal 440.0 V)
    esb_breaker_closed: bool = True  # Emergency Switchboard incoming breaker closed


@dataclass
class EdgBlackoutResult:
    """Compliance assessment against SOLAS 45-second emergency recovery."""
    status: EdgBlackoutStatus
    solas_45s_compliant: bool
    voltage_stabilized: bool
    frequency_stabilized: bool
    starting_energy_sufficient: bool
    elapsed_time_sec: float
    warnings: List[str] = field(default_factory=list)


class EdgBlackoutEngine:
    """SOLAS II-1 Reg 42/43 emergency power restoration state machine."""

    MSB_NOMINAL_VOLTS = 440.0
    BLACKOUT_VOLTAGE_THRESHOLD = 88.0  # 20% of 440V
    MIN_AIR_PRESSURE_BAR = 18.0  # Class minimum for 3 consecutive air starts
    MIN_BATTERY_VOLTS = 23.0  # Minimum for pneumatic/electric starter relay
    MAX_SOLAS_RESTORE_TIME_SEC = 45.0  # Mandatory SOLAS deadline for critical power
    NOMINAL_FREQ_HZ = 60.0
    FREQ_TOLERANCE_HZ = 1.8  # ± 3% steady state
    NOMINAL_VOLTS = 440.0
    VOLT_TOLERANCE_PCT = 0.035  # ± 3.5% steady state

    def evaluate(self, telemetry: EdgBlackoutInput) -> EdgBlackoutResult:
        warnings: List[str] = []

        is_blackout = telemetry.msb_voltage_volts <= self.BLACKOUT_VOLTAGE_THRESHOLD
        if not is_blackout:
            return EdgBlackoutResult(
                status=EdgBlackoutStatus.BLACKOUT_STANDBY,
                solas_45s_compliant=True,
                voltage_stabilized=True,
                frequency_stabilized=True,
                starting_energy_sufficient=True,
                elapsed_time_sec=telemetry.blackout_elapsed_sec,
                warnings=["Main switchboard energized. Emergency generator on automatic hot standby."],
            )

        starting_energy_sufficient = (
            telemetry.starting_air_pressure_bar >= self.MIN_AIR_PRESSURE_BAR
            or telemetry.starter_battery_volts >= self.MIN_BATTERY_VOLTS
        )
        if not starting_energy_sufficient:
            warnings.append(
                f"INSUFFICIENT STARTING ENERGY: Air pressure {telemetry.starting_air_pressure_bar} bar < {self.MIN_AIR_PRESSURE_BAR} bar "
                f"and battery {telemetry.starter_battery_volts} V < {self.MIN_BATTERY_VOLTS} V."
            )

        frequency_stabilized = abs(telemetry.edg_frequency_hz - self.NOMINAL_FREQ_HZ) <= self.FREQ_TOLERANCE_HZ
        voltage_stabilized = (
            abs(telemetry.edg_voltage_volts - self.NOMINAL_VOLTS) <= (self.NOMINAL_VOLTS * self.VOLT_TOLERANCE_PCT)
        )

        within_time_limit = telemetry.blackout_elapsed_sec <= self.MAX_SOLAS_RESTORE_TIME_SEC
        solas_compliant = (
            within_time_limit
            and telemetry.esb_breaker_closed
            and frequency_stabilized
            and voltage_stabilized
        )

        if not starting_energy_sufficient:
            status = EdgBlackoutStatus.LOW_STARTING_ENERGY_LOCKOUT
        elif not within_time_limit and not telemetry.esb_breaker_closed:
            status = EdgBlackoutStatus.OVER_TIME_SOLAS_VIOLATION
            warnings.append(
                f"SOLAS VIOLATION: Blackout elapsed time {telemetry.blackout_elapsed_sec:.1f}s exceeded 45.0s maximum limit!"
            )
        elif telemetry.esb_breaker_closed and frequency_stabilized and voltage_stabilized:
            status = EdgBlackoutStatus.EMERGENCY_BUS_CONNECTED
        elif telemetry.blackout_elapsed_sec > 15.0 and (not frequency_stabilized or not voltage_stabilized):
            status = EdgBlackoutStatus.CRANKING_FAILURE_TRIP
            warnings.append("EDG engine failed to ramp to nominal frequency and voltage within 15 seconds.")
        else:
            status = EdgBlackoutStatus.EDG_STARTING_RAMP

        return EdgBlackoutResult(
            status=status,
            solas_45s_compliant=solas_compliant,
            voltage_stabilized=voltage_stabilized,
            frequency_stabilized=frequency_stabilized,
            starting_energy_sufficient=starting_energy_sufficient,
            elapsed_time_sec=telemetry.blackout_elapsed_sec,
            warnings=warnings,
        )
