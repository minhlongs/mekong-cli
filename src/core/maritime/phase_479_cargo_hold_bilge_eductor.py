"""Phase 479: Cargo Hold Bilge Eductor & Flooding Detection Interlock Engine.

Complies with:
- SOLAS XII/9 (Bulk carrier cargo hold bilge pumping & water ingress prevention)
- IACS UR S24 & IACS UR SC18:
  - Minimum driving pressure: P_motive >= 4.5 bar.
  - Differential pressure: deltaP = (P_driving - P_back) >= 0.8 bar.
  - Backflow check valve must be healthy (backflow_check_ok=True).
  - Water ingress pre-alarm: level >= 0.5m; flooding alarm: level >= 2.0m.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class CargoHoldBilgeStatus(str, Enum):
    NORMAL = "NORMAL"
    PRE_ALARM = "PRE_ALARM"
    FLOODING_ALARM = "FLOODING_ALARM"
    BACKFLOW_RISK_INHIBIT = "BACKFLOW_RISK_INHIBIT"
    INSUFFICIENT_DRIVING_PRESSURE = "INSUFFICIENT_DRIVING_PRESSURE"


@dataclass(frozen=True)
class CargoHoldBilgeTelemetry:
    water_level_m: float
    driving_pressure_bar: float
    backpressure_bar: float
    backflow_check_ok: bool


@dataclass(frozen=True)
class CargoHoldBilgeAssessment:
    status: CargoHoldBilgeStatus
    eductor_permissive: bool
    flooding_alarm_active: bool
    pre_alarm_active: bool
    remarks: str


class CargoHoldBilgeEductorEngine:
    MIN_DRIVING_P_BAR: float = 4.5
    MIN_DIFF_P_BAR: float = 0.8
    PRE_ALARM_LEVEL_M: float = 0.5
    FLOODING_ALARM_LEVEL_M: float = 2.0

    @classmethod
    def evaluate(cls, telemetry: CargoHoldBilgeTelemetry) -> CargoHoldBilgeAssessment:
        pre_alarm = telemetry.water_level_m >= cls.PRE_ALARM_LEVEL_M
        flooding_alarm = telemetry.water_level_m >= cls.FLOODING_ALARM_LEVEL_M

        if not telemetry.backflow_check_ok:
            return CargoHoldBilgeAssessment(
                status=CargoHoldBilgeStatus.BACKFLOW_RISK_INHIBIT,
                eductor_permissive=False,
                flooding_alarm_active=flooding_alarm,
                pre_alarm_active=pre_alarm,
                remarks="SOLAS XII/9: SDNR check valve failure detected. Eductor suction prohibited to avoid backflow.",
            )

        diff_p = telemetry.driving_pressure_bar - telemetry.backpressure_bar
        if telemetry.driving_pressure_bar < cls.MIN_DRIVING_P_BAR or diff_p < cls.MIN_DIFF_P_BAR:
            return CargoHoldBilgeAssessment(
                status=CargoHoldBilgeStatus.INSUFFICIENT_DRIVING_PRESSURE,
                eductor_permissive=False,
                flooding_alarm_active=flooding_alarm,
                pre_alarm_active=pre_alarm,
                remarks=f"Driving pressure {telemetry.driving_pressure_bar} bar or deltaP {diff_p:.2f} bar below minimum.",
            )

        if flooding_alarm:
            return CargoHoldBilgeAssessment(
                status=CargoHoldBilgeStatus.FLOODING_ALARM,
                eductor_permissive=True,
                flooding_alarm_active=True,
                pre_alarm_active=True,
                remarks=f"SOLAS XII/9 EMERGENCY: Cargo hold water level {telemetry.water_level_m}m >= 2.0m. Flooding alarm active.",
            )

        if pre_alarm:
            return CargoHoldBilgeAssessment(
                status=CargoHoldBilgeStatus.PRE_ALARM,
                eductor_permissive=True,
                flooding_alarm_active=False,
                pre_alarm_active=True,
                remarks=f"WARNING: Cargo hold water level {telemetry.water_level_m}m >= 0.5m. Pre-alarm triggered.",
            )

        return CargoHoldBilgeAssessment(
            status=CargoHoldBilgeStatus.NORMAL,
            eductor_permissive=True,
            flooding_alarm_active=False,
            pre_alarm_active=False,
            remarks="Cargo hold bilge well water level and eductor motive readiness nominal.",
        )
