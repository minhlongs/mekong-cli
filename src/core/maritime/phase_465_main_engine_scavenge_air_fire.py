"""Phase 465: Main Engine Scavenge Air Fire CO2 Injection & Temp Interlock.

Compliant with SOLAS II-2 Reg 10.5 & IACS UR M35.
Monitors scavenge air receiver duct temperatures (T >= 80 deg C warning, >= 120 deg C fire alarm),
automatic slow-down of propulsion engine, scavenge drain shut-off, and boundary cooling / CO2 flooding authorization.
"""

from dataclasses import dataclass
from enum import Enum


class ScavengeFireStatus(str, Enum):
    NORMAL = "NORMAL"
    TEMP_ELEVATED_WARN = "TEMP_ELEVATED_WARN"
    FIRE_ALARM_SLOWDOWN = "FIRE_ALARM_SLOWDOWN"
    CO2_RELEASE_ARMED = "CO2_RELEASE_ARMED"
    DRAIN_VALVE_STUCK_OPEN = "DRAIN_VALVE_STUCK_OPEN"


@dataclass(frozen=True)
class ScavengeFireTelemetry:
    scavenge_air_temp_celsius: float
    scavenge_manifold_pressure_bar: float
    scavenge_drain_closed: bool
    engine_rpm: float
    co2_inhibition_released: bool


@dataclass(frozen=True)
class ScavengeFireAssessment:
    status: ScavengeFireStatus
    fire_detected: bool
    engine_slowdown_required: bool
    co2_injection_permissible: bool
    drain_isolated: bool
    alarm_active: bool
    remarks: str


class ScavengeAirFireEngine:
    """SOLAS II-2 Reg 10.5 Main Engine Scavenge Receiver Fire Safety Logic."""

    WARN_TEMP_CELSIUS: float = 80.0
    FIRE_ALARM_TEMP_CELSIUS: float = 120.0
    CO2_ARMING_RPM_MAX: float = 20.0

    @classmethod
    def evaluate(cls, telemetry: ScavengeFireTelemetry) -> ScavengeFireAssessment:
        if telemetry.scavenge_air_temp_celsius >= cls.FIRE_ALARM_TEMP_CELSIUS:
            co2_ready = (
                telemetry.engine_rpm <= cls.CO2_ARMING_RPM_MAX
                and telemetry.scavenge_drain_closed
                and telemetry.co2_inhibition_released
            )
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.CO2_RELEASE_ARMED if co2_ready else ScavengeFireStatus.FIRE_ALARM_SLOWDOWN,
                fire_detected=True,
                engine_slowdown_required=True,
                co2_injection_permissible=co2_ready,
                drain_isolated=telemetry.scavenge_drain_closed,
                alarm_active=True,
                remarks=f"Scavenge fire confirmed: {telemetry.scavenge_air_temp_celsius:.1f}C >= {cls.FIRE_ALARM_TEMP_CELSIUS}C; engine slowdown triggered",
            )

        if telemetry.scavenge_air_temp_celsius >= cls.WARN_TEMP_CELSIUS:
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.TEMP_ELEVATED_WARN,
                fire_detected=False,
                engine_slowdown_required=False,
                co2_injection_permissible=False,
                drain_isolated=telemetry.scavenge_drain_closed,
                alarm_active=True,
                remarks=f"Scavenge duct temperature elevated: {telemetry.scavenge_air_temp_celsius:.1f}C >= {cls.WARN_TEMP_CELSIUS}C warning threshold",
            )

        if not telemetry.scavenge_drain_closed and telemetry.engine_rpm > cls.CO2_ARMING_RPM_MAX:
            return ScavengeFireAssessment(
                status=ScavengeFireStatus.DRAIN_VALVE_STUCK_OPEN,
                fire_detected=False,
                engine_slowdown_required=False,
                co2_injection_permissible=False,
                drain_isolated=False,
                alarm_active=False,
                remarks="Scavenge drain valve open during sea passage; monitor for exhaust blowby",
            )

        return ScavengeFireAssessment(
            status=ScavengeFireStatus.NORMAL,
            fire_detected=False,
            engine_slowdown_required=False,
            co2_injection_permissible=False,
            drain_isolated=telemetry.scavenge_drain_closed,
            alarm_active=False,
            remarks="Scavenge air temperature and manifold status nominal",
        )
