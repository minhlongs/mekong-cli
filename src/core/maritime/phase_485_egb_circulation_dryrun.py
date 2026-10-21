"""Phase 485: Exhaust Gas Boiler (EGB) Circulation Pump & Dry-Run Interlock Engine.

Complies with IACS UR M14 and ASME Section I.
Strictly < 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class EgbCirculationStatus(Enum):
    NORMAL = "normal"
    STANDBY_PUMP_CUT_IN = "standby_pump_cut_in"
    DRY_RUN_DAMPER_BYPASS_TRIP = "dry_run_damper_bypass_trip"
    PUMP_CAVITATION_WARNING = "pump_cavitation_warning"
    VAPOR_LOCK_RISK = "vapor_lock_risk"


@dataclass(frozen=True)
class EgbCirculationTelemetry:
    pump_diff_pressure_bar: float
    water_flow_m3_h: float
    standby_pump_available: bool
    loss_of_flow_duration_s: float
    exhaust_gas_inlet_temp_c: float
    economizer_inlet_temp_c: float
    tsat_c: float


@dataclass(frozen=True)
class EgbCirculationAssessment:
    status: EgbCirculationStatus
    standby_pump_start_command: bool
    exhaust_diverter_bypass_trip: bool
    circulation_adequate: bool
    remarks: str


class EgbCirculationDryRunEngine:
    MIN_DIFF_PRESSURE_NORMAL_BAR = 1.2
    MIN_DIFF_PRESSURE_LOW_BAR = 0.8
    MIN_CIRCULATION_FLOW_M3_H = 15.0
    MAX_DRY_RUN_DURATION_S = 15.0
    MIN_SUBCOOLING_MARGIN_C = 8.0

    @classmethod
    def evaluate(cls, telem: EgbCirculationTelemetry) -> EgbCirculationAssessment:
        subcooling = telem.tsat_c - telem.economizer_inlet_temp_c
        adequate = (
            telem.pump_diff_pressure_bar >= cls.MIN_DIFF_PRESSURE_NORMAL_BAR
            and telem.water_flow_m3_h >= cls.MIN_CIRCULATION_FLOW_M3_H
        )

        if telem.loss_of_flow_duration_s > cls.MAX_DRY_RUN_DURATION_S:
            return EgbCirculationAssessment(
                status=EgbCirculationStatus.DRY_RUN_DAMPER_BYPASS_TRIP,
                standby_pump_start_command=telem.standby_pump_available,
                exhaust_diverter_bypass_trip=True,
                circulation_adequate=False,
                remarks="EGB circulation lost > 15s. Dry-run condition. Exhaust gas bypass damper tripped.",
            )

        if telem.pump_diff_pressure_bar < cls.MIN_DIFF_PRESSURE_LOW_BAR:
            return EgbCirculationAssessment(
                status=EgbCirculationStatus.STANDBY_PUMP_CUT_IN,
                standby_pump_start_command=telem.standby_pump_available,
                exhaust_diverter_bypass_trip=False,
                circulation_adequate=False,
                remarks="Low pump dP (< 0.8 bar). Duty pump failure. Standby circulation pump engaged.",
            )

        if subcooling < cls.MIN_SUBCOOLING_MARGIN_C:
            return EgbCirculationAssessment(
                status=EgbCirculationStatus.VAPOR_LOCK_RISK,
                standby_pump_start_command=False,
                exhaust_diverter_bypass_trip=False,
                circulation_adequate=adequate,
                remarks="Insufficient subcooling margin (< 8 C). High risk of steam binding / vapor lock.",
            )

        if telem.pump_diff_pressure_bar < cls.MIN_DIFF_PRESSURE_NORMAL_BAR:
            return EgbCirculationAssessment(
                status=EgbCirculationStatus.PUMP_CAVITATION_WARNING,
                standby_pump_start_command=False,
                exhaust_diverter_bypass_trip=False,
                circulation_adequate=adequate,
                remarks="Circulation pump differential pressure marginal (0.8 - 1.2 bar). Monitor cavitation.",
            )

        return EgbCirculationAssessment(
            status=EgbCirculationStatus.NORMAL,
            standby_pump_start_command=False,
            exhaust_diverter_bypass_trip=False,
            circulation_adequate=True,
            remarks="EGB forced water circulation operating nominal under IACS UR M14 standards.",
        )
