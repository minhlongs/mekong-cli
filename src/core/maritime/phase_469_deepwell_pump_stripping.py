"""Phase 469: Marine Cargo Deepwell Pump Stripping & Dry-Running Protection Engine.

Complies with:
- IBC Code Ch. 5 / MARPOL Annex II Reg. 12 (Pumping, piping and unloading arrangements)
- DNV Pt.4 Ch.6 Sec.4 (Cargo pumping systems & dry run protection)
- Deepwell submerged hydraulic/electric cargo pump stripping limit:
  - Cavitation / dry run risk when discharge pressure drops below 1.5 bar with motor current/hydraulic drive drop
  - Motor current underload trip: I <= 30% of rated nominal current (indicating loss of suction/dry impeller)
  - Pump casing temperature rise: T >= 75.0 deg C (frictional heating of PTFE wear rings)
  - Stripping purge nitrogen pressure: P >= 4.0 bar to ensure cargo well purge without backflow

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class DeepwellPumpStatus(str, Enum):
    NORMAL_DISCHARGE = "NORMAL_DISCHARGE"
    STRIPPING_ACTIVE = "STRIPPING_ACTIVE"
    DRY_RUN_CAVITATION_TRIP = "DRY_RUN_CAVITATION_TRIP"
    CASING_OVERHEAT_TRIP = "CASING_OVERHEAT_TRIP"
    LOW_PURGE_PRESSURE_ALARM = "LOW_PURGE_PRESSURE_ALARM"


@dataclass(frozen=True)
class DeepwellPumpTelemetry:
    discharge_pressure_bar: float
    casing_temp_c: float
    motor_current_pct: float  # Percentage of full load amp (FLA)
    stripping_mode_selected: bool
    purge_n2_pressure_bar: float
    pump_running: bool


@dataclass(frozen=True)
class DeepwellPumpAssessment:
    status: DeepwellPumpStatus
    auto_stop_permissive: bool
    stripping_n2_valve_open: bool
    remarks: str


class DeepwellPumpProtectionEngine:
    MIN_STRIPPING_PURGE_P_BAR: float = 4.0
    MAX_CASING_TEMP_C: float = 75.0
    MIN_CURRENT_PCT_TRIP: float = 30.0
    MIN_DISCHARGE_P_BAR: float = 1.5

    @classmethod
    def evaluate(cls, telemetry: DeepwellPumpTelemetry) -> DeepwellPumpAssessment:
        if not telemetry.pump_running:
            return DeepwellPumpAssessment(
                status=DeepwellPumpStatus.NORMAL_DISCHARGE,
                auto_stop_permissive=False,
                stripping_n2_valve_open=False,
                remarks="Cargo pump stopped.",
            )

        if telemetry.casing_temp_c >= cls.MAX_CASING_TEMP_C:
            return DeepwellPumpAssessment(
                status=DeepwellPumpStatus.CASING_OVERHEAT_TRIP,
                auto_stop_permissive=True,
                stripping_n2_valve_open=False,
                remarks=f"Casing overheat trip: T={telemetry.casing_temp_c}C >= {cls.MAX_CASING_TEMP_C}C (PTFE wear ring risk).",
            )

        # Cavitation / dry running detection
        if (
            telemetry.motor_current_pct <= cls.MIN_CURRENT_PCT_TRIP
            and telemetry.discharge_pressure_bar <= cls.MIN_DISCHARGE_P_BAR
        ):
            return DeepwellPumpAssessment(
                status=DeepwellPumpStatus.DRY_RUN_CAVITATION_TRIP,
                auto_stop_permissive=True,
                stripping_n2_valve_open=telemetry.stripping_mode_selected,
                remarks=f"Dry run trip: motor current {telemetry.motor_current_pct}% <= {cls.MIN_CURRENT_PCT_TRIP}% & discharge P {telemetry.discharge_pressure_bar} bar <= {cls.MIN_DISCHARGE_P_BAR} bar.",
            )

        if telemetry.stripping_mode_selected:
            if telemetry.purge_n2_pressure_bar < cls.MIN_STRIPPING_PURGE_P_BAR:
                return DeepwellPumpAssessment(
                    status=DeepwellPumpStatus.LOW_PURGE_PRESSURE_ALARM,
                    auto_stop_permissive=False,
                    stripping_n2_valve_open=False,
                    remarks=f"Low purge pressure: N2 P={telemetry.purge_n2_pressure_bar} bar < min {cls.MIN_STRIPPING_PURGE_P_BAR} bar.",
                )
            return DeepwellPumpAssessment(
                status=DeepwellPumpStatus.STRIPPING_ACTIVE,
                auto_stop_permissive=False,
                stripping_n2_valve_open=True,
                remarks="Deepwell stripping mode active: N2 well purge pressurized.",
            )

        return DeepwellPumpAssessment(
            status=DeepwellPumpStatus.NORMAL_DISCHARGE,
            auto_stop_permissive=False,
            stripping_n2_valve_open=False,
            remarks="Deepwell cargo discharge operating normally under full suction head.",
        )
