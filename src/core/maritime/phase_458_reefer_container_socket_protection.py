"""Phase 458: Marine Refrigerated Container Socket Monitoring & Earth Leakage Protection.

Compliant with IEC 60309-2 & DNV Rules Pt. 5 Ch. 10 (Refrigerated Cargo).
Monitors reefer socket 440V 32A contactor thermals, earth leakage current (30 mA),
supply voltage stability (+/- 5%), and mechanical rotary interlock state.
"""

from dataclasses import dataclass
from enum import Enum


class ReeferSocketStatus(str, Enum):
    NORMAL = "NORMAL"
    THERMAL_WARNING = "THERMAL_WARNING"
    EARTH_FAULT_TRIP = "EARTH_FAULT_TRIP"
    VOLTAGE_ANOMALY = "VOLTAGE_ANOMALY"
    INTERLOCK_VIOLATION = "INTERLOCK_VIOLATION"


@dataclass(frozen=True)
class ReeferSocketTelemetry:
    voltage_l_l_volts: float
    current_load_amps: float
    earth_leakage_ma: float
    pin_temperature_celsius: float
    rotary_switch_engaged: bool
    plug_inserted: bool


@dataclass(frozen=True)
class ReeferSocketAssessment:
    status: ReeferSocketStatus
    breaker_tripped: bool
    earth_fault_detected: bool
    temperature_in_spec: bool
    safe_to_operate: bool
    safety_alarm: bool
    remarks: str


class ReeferContainerSocketEngine:
    MIN_VOLTAGE_VOLTS: float = 418.0
    MAX_VOLTAGE_VOLTS: float = 462.0
    MAX_LOAD_AMPS: float = 32.0
    MAX_EARTH_LEAKAGE_MA: float = 30.0
    WARN_PIN_TEMP_CELSIUS: float = 70.0
    TRIP_PIN_TEMP_CELSIUS: float = 85.0

    @classmethod
    def evaluate(cls, telemetry: ReeferSocketTelemetry) -> ReeferSocketAssessment:
        if telemetry.rotary_switch_engaged and not telemetry.plug_inserted:
            return ReeferSocketAssessment(
                status=ReeferSocketStatus.INTERLOCK_VIOLATION,
                breaker_tripped=True,
                earth_fault_detected=False,
                temperature_in_spec=True,
                safe_to_operate=False,
                safety_alarm=True,
                remarks="Mechanical interlock violation: Socket powered without secure plug seating",
            )

        if telemetry.earth_leakage_ma >= cls.MAX_EARTH_LEAKAGE_MA:
            return ReeferSocketAssessment(
                status=ReeferSocketStatus.EARTH_FAULT_TRIP,
                breaker_tripped=True,
                earth_fault_detected=True,
                temperature_in_spec=True,
                safe_to_operate=False,
                safety_alarm=True,
                remarks="RCD trip: Earth fault current >= 30 mA posing hazardous hull shock risk",
            )

        if telemetry.pin_temperature_celsius >= cls.TRIP_PIN_TEMP_CELSIUS:
            return ReeferSocketAssessment(
                status=ReeferSocketStatus.THERMAL_WARNING,
                breaker_tripped=True,
                earth_fault_detected=False,
                temperature_in_spec=False,
                safe_to_operate=False,
                safety_alarm=True,
                remarks="Socket thermal runaway: Contact pin temperature >= 85 C",
            )

        volt_out = not (cls.MIN_VOLTAGE_VOLTS <= telemetry.voltage_l_l_volts <= cls.MAX_VOLTAGE_VOLTS)
        overload = telemetry.current_load_amps > cls.MAX_LOAD_AMPS

        if volt_out or overload:
            return ReeferSocketAssessment(
                status=ReeferSocketStatus.VOLTAGE_ANOMALY,
                breaker_tripped=False,
                earth_fault_detected=False,
                temperature_in_spec=True,
                safe_to_operate=False,
                safety_alarm=True,
                remarks="Feeder voltage outside 418-462V band or load exceeds 32A rated capacity",
            )

        if telemetry.pin_temperature_celsius >= cls.WARN_PIN_TEMP_CELSIUS:
            return ReeferSocketAssessment(
                status=ReeferSocketStatus.THERMAL_WARNING,
                breaker_tripped=False,
                earth_fault_detected=False,
                temperature_in_spec=True,
                safe_to_operate=True,
                safety_alarm=False,
                remarks="Socket pin temperature elevated above 70 C warning threshold",
            )

        return ReeferSocketAssessment(
            status=ReeferSocketStatus.NORMAL,
            breaker_tripped=False,
            earth_fault_detected=False,
            temperature_in_spec=True,
            safe_to_operate=True,
            safety_alarm=False,
            remarks="Reefer container socket nominal at 440V with zero ground leakage",
        )
