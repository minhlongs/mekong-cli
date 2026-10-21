"""Phase 522: Engine Room Emergency Escape Trunk Pressurization & Lighting.
Complies with SOLAS II-2 Reg 13.4.2 and IMO FSS Code Chapter 13.
Strictly < 85 LOC, zero mocks, pure deterministic safety state machine.
"""
from dataclasses import dataclass
from enum import Enum


class EscapeTrunkStatus(str, Enum):
    COMPLIANT_SAFE_EGRESS = "COMPLIANT_SAFE_EGRESS"
    UNDER_PRESSURIZED_SMOKE_RISK = "UNDER_PRESSURIZED_SMOKE_RISK"
    OVER_PRESSURIZED_DOOR_FORCE_HIGH = "OVER_PRESSURIZED_DOOR_FORCE_HIGH"
    EMERGENCY_LIGHTING_BATTERY_FAULT = "EMERGENCY_LIGHTING_BATTERY_FAULT"


@dataclass(frozen=True)
class EscapeTrunkTelemetry:
    trunk_overpressure_pa: float
    emergency_lighting_volts: float = 24.5
    lower_fire_door_closed: bool = True


@dataclass(frozen=True)
class EscapeTrunkAssessment:
    trunk_status: EscapeTrunkStatus
    relief_damper_open_cmd: bool
    smoke_ingress_protected: bool
    alarm_active: bool
    alarm_code: str


class EscapeTrunkPressurizationEngine:
    """Evaluates escape trunk overpressure (20-50 Pa) and 24V emergency lighting."""

    MIN_PRESSURE_PA: float = 20.0
    MAX_PRESSURE_PA: float = 50.0
    MIN_BATTERY_V: float = 21.6

    @classmethod
    def evaluate(cls, t: EscapeTrunkTelemetry) -> EscapeTrunkAssessment:
        if t.emergency_lighting_volts < cls.MIN_BATTERY_V:
            return EscapeTrunkAssessment(
                EscapeTrunkStatus.EMERGENCY_LIGHTING_BATTERY_FAULT,
                False,
                t.trunk_overpressure_pa >= cls.MIN_PRESSURE_PA,
                True,
                "ESCAPE_TRUNK_24V_LUMINAIRE_LOW_VOLTAGE",
            )
        if t.trunk_overpressure_pa < cls.MIN_PRESSURE_PA:
            return EscapeTrunkAssessment(
                EscapeTrunkStatus.UNDER_PRESSURIZED_SMOKE_RISK,
                False,
                False,
                True,
                "SOLAS_ESCAPE_TRUNK_LOSS_OF_OVERPRESSURE",
            )
        if t.trunk_overpressure_pa > cls.MAX_PRESSURE_PA:
            return EscapeTrunkAssessment(
                EscapeTrunkStatus.OVER_PRESSURIZED_DOOR_FORCE_HIGH,
                True,
                True,
                True,
                "ESCAPE_TRUNK_EXCESS_PRESSURE_RELIEF_OPEN",
            )
        return EscapeTrunkAssessment(
            EscapeTrunkStatus.COMPLIANT_SAFE_EGRESS,
            False,
            True,
            False,
            "NONE",
        )
