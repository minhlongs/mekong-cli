"""Phase 482: Steering Gear Phase Failure & Hydraulic Auto-Isolation Engine.

Complies with:
- SOLAS II-1 Reg 29 & IACS UR M42 (Steering gear power units and alarms):
  - Reservoir level: level < 35.0% triggers emergency auto-isolation of damaged unit.
  - Phase failure: voltage phase imbalance > 10.0% or phase loss triggers alarm & standby auto-start.
  - Standby pump takeover: Must reach working pressure (>= 160.0 bar) within <= 45.0 seconds.
  - If elapsed time > 45.0s and standby pressure < 160.0 bar, flag STANDBY_FAILED_TO_PRESSURIZE.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class SteeringGearStatus(str, Enum):
    NORMAL = "NORMAL"
    RESERVOIR_LOW_AUTO_ISOLATE = "RESERVOIR_LOW_AUTO_ISOLATE"
    PHASE_FAILURE_STANDBY_START = "PHASE_FAILURE_STANDBY_START"
    STANDBY_PRESSURE_REACHED = "STANDBY_PRESSURE_REACHED"
    STANDBY_FAILED_TO_PRESSURIZE = "STANDBY_FAILED_TO_PRESSURIZE"


@dataclass(frozen=True)
class SteeringGearTelemetry:
    reservoir_level_pct: float
    phase_imbalance_pct: float
    phase_loss: bool
    standby_pressure_bar: float
    standby_elapsed_s: float


@dataclass(frozen=True)
class SteeringGearAssessment:
    status: SteeringGearStatus
    auto_isolate_unit: bool
    phase_failure_alarm: bool
    standby_auto_start_command: bool
    steering_capable: bool
    remarks: str


class SteeringGearSafetyEngine:
    MIN_RESERVOIR_LEVEL_PCT: float = 35.0
    MAX_PHASE_IMBALANCE_PCT: float = 10.0
    WORKING_PRESSURE_BAR: float = 160.0
    MAX_START_TAKEOVER_TIME_S: float = 45.0

    @classmethod
    def evaluate(cls, telemetry: SteeringGearTelemetry) -> SteeringGearAssessment:
        phase_failure = telemetry.phase_loss or telemetry.phase_imbalance_pct > cls.MAX_PHASE_IMBALANCE_PCT

        if telemetry.reservoir_level_pct < cls.MIN_RESERVOIR_LEVEL_PCT:
            return SteeringGearAssessment(
                status=SteeringGearStatus.RESERVOIR_LOW_AUTO_ISOLATE,
                auto_isolate_unit=True,
                phase_failure_alarm=phase_failure,
                standby_auto_start_command=True,
                steering_capable=telemetry.standby_pressure_bar >= cls.WORKING_PRESSURE_BAR,
                remarks=f"SOLAS II-1/29 CRITICAL: Reservoir level {telemetry.reservoir_level_pct}% < 35.0%. Auto-isolating steering unit.",
            )

        if phase_failure:
            if telemetry.standby_pressure_bar >= cls.WORKING_PRESSURE_BAR:
                return SteeringGearAssessment(
                    status=SteeringGearStatus.STANDBY_PRESSURE_REACHED,
                    auto_isolate_unit=False,
                    phase_failure_alarm=True,
                    standby_auto_start_command=True,
                    steering_capable=True,
                    remarks=f"Standby pump reached full working pressure ({telemetry.standby_pressure_bar} bar >= 160 bar) in {telemetry.standby_elapsed_s}s.",
                )

            if telemetry.standby_elapsed_s > cls.MAX_START_TAKEOVER_TIME_S and telemetry.standby_pressure_bar < cls.WORKING_PRESSURE_BAR:
                return SteeringGearAssessment(
                    status=SteeringGearStatus.STANDBY_FAILED_TO_PRESSURIZE,
                    auto_isolate_unit=False,
                    phase_failure_alarm=True,
                    standby_auto_start_command=True,
                    steering_capable=False,
                    remarks=f"CRITICAL: Standby unit failed to reach 160 bar in {telemetry.standby_elapsed_s}s (> 45s). Loss of rudder control.",
                )

            return SteeringGearAssessment(
                status=SteeringGearStatus.PHASE_FAILURE_STANDBY_START,
                auto_isolate_unit=False,
                phase_failure_alarm=True,
                standby_auto_start_command=True,
                steering_capable=True,
                remarks=f"SOLAS II-1/29 ALARM: Power supply phase failure (imbalance {telemetry.phase_imbalance_pct}%). Standby pump auto-start engaged.",
            )

        return SteeringGearAssessment(
            status=SteeringGearStatus.NORMAL,
            auto_isolate_unit=False,
            phase_failure_alarm=False,
            standby_auto_start_command=False,
            steering_capable=True,
            remarks="Steering gear power supplies, hydraulic inventory, and standby systems nominal.",
        )
