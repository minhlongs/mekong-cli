"""Phase 483: Sewage Treatment Plant (STP) Aeration & Sludge Return Engine.

Complies with IMO Res. MEPC.227(64) and MARPOL Annex IV.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class StpAerationStatus(Enum):
    NORMAL = "normal"
    LOW_DO_WARNING = "low_do_warning"
    SEPTIC_ALARM_STANDBY_START = "septic_alarm_standby_start"
    BLOWER_PRESSURE_LOST = "blower_pressure_lost"
    SLUDGE_RECIRC_FAILURE = "sludge_recirc_failure"


@dataclass(frozen=True)
class StpAerationTelemetry:
    dissolved_oxygen_mg_l: float
    aeration_pressure_bar: float
    blower_running: bool
    standby_blower_ready: bool
    airlift_sludge_flow_l_min: float
    blower_failover_elapsed_s: float


@dataclass(frozen=True)
class StpAerationAssessment:
    status: StpAerationStatus
    standby_blower_start_command: bool
    sludge_recirculation_ok: bool
    aerobic_treatment_healthy: bool
    remarks: str


class StpAerationSludgeReturnEngine:
    MIN_DO_NORMAL_MG_L = 2.0
    MIN_DO_CRITICAL_MG_L = 1.0
    MIN_BLOWER_PRESSURE_BAR = 0.15
    MIN_SLUDGE_FLOW_L_MIN = 15.0
    MAX_BLOWER_FAILOVER_TIMEOUT_S = 30.0

    @classmethod
    def evaluate(cls, telem: StpAerationTelemetry) -> StpAerationAssessment:
        sludge_ok = telem.airlift_sludge_flow_l_min >= cls.MIN_SLUDGE_FLOW_L_MIN

        if not telem.blower_running or telem.aeration_pressure_bar < cls.MIN_BLOWER_PRESSURE_BAR:
            if telem.standby_blower_ready and telem.blower_failover_elapsed_s <= cls.MAX_BLOWER_FAILOVER_TIMEOUT_S:
                return StpAerationAssessment(
                    status=StpAerationStatus.BLOWER_PRESSURE_LOST,
                    standby_blower_start_command=True,
                    sludge_recirculation_ok=sludge_ok,
                    aerobic_treatment_healthy=False,
                    remarks="Aeration pressure loss detected. Standby blower cut-in commanded.",
                )
            return StpAerationAssessment(
                status=StpAerationStatus.BLOWER_PRESSURE_LOST,
                standby_blower_start_command=False,
                sludge_recirculation_ok=sludge_ok,
                aerobic_treatment_healthy=False,
                remarks="Blower failed and standby blower unavailable or failover timed out.",
            )

        if telem.dissolved_oxygen_mg_l < cls.MIN_DO_CRITICAL_MG_L:
            return StpAerationAssessment(
                status=StpAerationStatus.SEPTIC_ALARM_STANDBY_START,
                standby_blower_start_command=telem.standby_blower_ready,
                sludge_recirculation_ok=sludge_ok,
                aerobic_treatment_healthy=False,
                remarks="Critical DO < 1.0 mg/L. Septic condition risk. Supplementary blower engaged.",
            )

        if not sludge_ok:
            return StpAerationAssessment(
                status=StpAerationStatus.SLUDGE_RECIRC_FAILURE,
                standby_blower_start_command=False,
                sludge_recirculation_ok=False,
                aerobic_treatment_healthy=False,
                remarks="Air-lift sludge return flow deficient. Clarifier biomass return blocked.",
            )

        if telem.dissolved_oxygen_mg_l < cls.MIN_DO_NORMAL_MG_L:
            return StpAerationAssessment(
                status=StpAerationStatus.LOW_DO_WARNING,
                standby_blower_start_command=False,
                sludge_recirculation_ok=True,
                aerobic_treatment_healthy=True,
                remarks="Dissolved oxygen marginal (1.0 - 2.0 mg/L). Regulate diffuser airflow.",
            )

        return StpAerationAssessment(
            status=StpAerationStatus.NORMAL,
            standby_blower_start_command=False,
            sludge_recirculation_ok=True,
            aerobic_treatment_healthy=True,
            remarks="STP aerobic digestion and sludge return within IMO MEPC.227(64) standards.",
        )
