"""Phase 480: Turbocharger Auxiliary Blower & Surge Protection Engine.

Complies with:
- IACS UR M9 (Scavenge air systems of two-stroke main engines):
  - Cut-in demand: scavenge pressure < 0.85 bar.
  - Cut-out limit: scavenge pressure >= 1.15 bar (returns to normal TC only).
  - Intermediate band [0.85, 1.15 bar): Aux blower running to sustain combustion.
  - Compressor surge detection: rate of pressure change dp/dt <= -0.25 bar/s triggers surge relief bypass.
  - Engine stopped: blower stop command issued.

Strictly < 110 LOC, zero mocks, deterministic rules.
"""

from dataclasses import dataclass
from enum import Enum


class AuxBlowerStatus(str, Enum):
    ENGINE_STOPPED = "ENGINE_STOPPED"
    TC_SURGE_RELIEF_ACTIVE = "TC_SURGE_RELIEF_ACTIVE"
    AUX_BLOWER_CUT_IN_DEMAND = "AUX_BLOWER_CUT_IN_DEMAND"
    NORMAL_TC_ONLY = "NORMAL_TC_ONLY"
    AUX_BLOWER_RUNNING = "AUX_BLOWER_RUNNING"


@dataclass(frozen=True)
class AuxBlowerTelemetry:
    scavenge_pressure_bar: float
    dp_dt_bar_s: float
    blower_running: bool
    engine_running: bool


@dataclass(frozen=True)
class AuxBlowerAssessment:
    status: AuxBlowerStatus
    blower_start_command: bool
    blower_stop_command: bool
    surge_relief_bypass_open: bool
    remarks: str


class TurbochargerAuxBlowerEngine:
    CUT_IN_THRESHOLD_BAR: float = 0.85
    CUT_OUT_THRESHOLD_BAR: float = 1.15
    SURGE_RATE_THRESHOLD_BAR_S: float = -0.25

    @classmethod
    def evaluate(cls, telemetry: AuxBlowerTelemetry) -> AuxBlowerAssessment:
        if not telemetry.engine_running:
            return AuxBlowerAssessment(
                status=AuxBlowerStatus.ENGINE_STOPPED,
                blower_start_command=False,
                blower_stop_command=True,
                surge_relief_bypass_open=False,
                remarks="Main engine stopped; auxiliary blowers secured.",
            )

        if telemetry.dp_dt_bar_s <= cls.SURGE_RATE_THRESHOLD_BAR_S:
            return AuxBlowerAssessment(
                status=AuxBlowerStatus.TC_SURGE_RELIEF_ACTIVE,
                blower_start_command=True,
                blower_stop_command=False,
                surge_relief_bypass_open=True,
                remarks=f"SURGE DETECTED: dp/dt = {telemetry.dp_dt_bar_s} bar/s <= -0.25 bar/s. Opening surge bypass & starting blower.",
            )

        if telemetry.scavenge_pressure_bar < cls.CUT_IN_THRESHOLD_BAR:
            return AuxBlowerAssessment(
                status=AuxBlowerStatus.AUX_BLOWER_CUT_IN_DEMAND,
                blower_start_command=True,
                blower_stop_command=False,
                surge_relief_bypass_open=False,
                remarks=f"IACS UR M9: Scavenge pressure {telemetry.scavenge_pressure_bar} bar < 0.85 bar. Blower cut-in required.",
            )

        if telemetry.scavenge_pressure_bar >= cls.CUT_OUT_THRESHOLD_BAR:
            return AuxBlowerAssessment(
                status=AuxBlowerStatus.NORMAL_TC_ONLY,
                blower_start_command=False,
                blower_stop_command=True,
                surge_relief_bypass_open=False,
                remarks=f"Scavenge pressure {telemetry.scavenge_pressure_bar} bar >= 1.15 bar. Turbocharger autonomous; blower cut-out.",
            )

        return AuxBlowerAssessment(
            status=AuxBlowerStatus.AUX_BLOWER_RUNNING,
            blower_start_command=True,
            blower_stop_command=False,
            surge_relief_bypass_open=False,
            remarks=f"Scavenge pressure {telemetry.scavenge_pressure_bar} bar in transition band [0.85, 1.15 bar). Sustaining blower.",
        )
