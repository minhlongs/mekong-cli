from dataclasses import dataclass
from enum import Enum


class DryPowderSystemState(str, Enum):
    DCP_STANDBY_READY = "DCP_STANDBY_READY"
    DCP_MONITOR_DISCHARGE_ACTIVE = "DCP_MONITOR_DISCHARGE_ACTIVE"
    FLUIDIZATION_INCOMPLETE_HOLD_INTERLOCK = "FLUIDIZATION_INCOMPLETE_HOLD_INTERLOCK"
    PROPELLANT_NITROGEN_LOW_PRESSURE_LOCKOUT = "PROPELLANT_NITROGEN_LOW_PRESSURE_LOCKOUT"


@dataclass(frozen=True)
class DryPowderSystemTelemetry:
    propellant_n2_pressure_bar: float
    powder_vessel_pressure_bar: float
    fluidization_elapsed_s: float
    discharge_requested: bool = False


@dataclass(frozen=True)
class DryPowderSystemAssessment:
    state: DryPowderSystemState
    main_powder_release_valve_open: bool
    reserve_nitrogen_bank_cut_in: bool
    interlock_code: str


class DryChemicalPowderNitrogenEngine:
    """IMO IGC Code Ch. 11.4 & FSS Code Ch. 14 Fixed Dry Chemical Powder N2 Interlock."""

    @classmethod
    def evaluate(cls, t: DryPowderSystemTelemetry) -> DryPowderSystemAssessment:
        if t.propellant_n2_pressure_bar < 160.0:
            return DryPowderSystemAssessment(
                DryPowderSystemState.PROPELLANT_NITROGEN_LOW_PRESSURE_LOCKOUT,
                False,
                True,
                "FSS_CH14_DCP_PROPELLANT_N2_LOW_PRESSURE_LOCKOUT",
            )
        if t.discharge_requested:
            if t.powder_vessel_pressure_bar < 12.0 or t.fluidization_elapsed_s < 15.0:
                return DryPowderSystemAssessment(
                    DryPowderSystemState.FLUIDIZATION_INCOMPLETE_HOLD_INTERLOCK,
                    False,
                    False,
                    "IGC_CH11_DCP_FLUIDIZATION_INCOMPLETE_VALVE_HOLD",
                )
            return DryPowderSystemAssessment(
                DryPowderSystemState.DCP_MONITOR_DISCHARGE_ACTIVE,
                True,
                False,
                "NONE",
            )
        return DryPowderSystemAssessment(
            DryPowderSystemState.DCP_STANDBY_READY,
            False,
            False,
            "NONE",
        )
