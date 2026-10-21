"""Phase 496: Marine Incinerator Primary Chamber Draft & Temp Protection.

Complies with IMO Res. MEPC.244(66) & SOLAS II-2 Reg 16.
Regulates negative pressure draft, primary chamber temperature, and flue gas outlet.
Strictly <= 100 LOC.
"""

from dataclasses import dataclass
from enum import Enum


class IncineratorStatus(str, Enum):
    NORMAL = "normal"
    DRAFT_LOSS_TRIP = "draft_loss_trip"
    LOW_TEMP_BURNER_LOCKOUT = "low_temp_burner_lockout"
    HIGH_TEMP_REFRACTORY_TRIP = "high_temp_refractory_trip"
    FLUE_GAS_HIGH_TEMP_ALARM = "flue_gas_high_temp_alarm"


@dataclass(frozen=True)
class IncineratorTelemetry:
    chamber_draft_mmwc: float  # Negative gauge: -15.0 to -5.0 mmWC nominal
    primary_chamber_temp_c: float  # 850.0 to 1200.0 C nominal
    flue_gas_temp_c: float  # < 350.0 C nominal
    induced_draft_fan_running: bool = True
    sludge_burner_active: bool = False


@dataclass(frozen=True)
class IncineratorAssessment:
    status: IncineratorStatus
    operation_permitted: bool
    burner_shutdown_command: bool
    sludge_dosing_permitted: bool
    flue_damper_override: bool
    description: str


class IncineratorCombustionChamberDraftEngine:
    """Evaluates marine waste incinerator negative pressure and temperature thresholds."""

    @staticmethod
    def evaluate(t: IncineratorTelemetry) -> IncineratorAssessment:
        # Negative pressure draft loss (blowback safety risk to machinery room)
        if t.chamber_draft_mmwc > -2.0 or not t.induced_draft_fan_running:
            return IncineratorAssessment(
                status=IncineratorStatus.DRAFT_LOSS_TRIP,
                operation_permitted=False,
                burner_shutdown_command=True,
                sludge_dosing_permitted=False,
                flue_damper_override=True,
                description="Chamber draft > -2.0 mmWC or ID fan failed: emergency burner trip to prevent blowback.",
            )

        # Refractory lining protection from excessive thermal peak
        if t.primary_chamber_temp_c > 1200.0:
            return IncineratorAssessment(
                status=IncineratorStatus.HIGH_TEMP_REFRACTORY_TRIP,
                operation_permitted=False,
                burner_shutdown_command=True,
                sludge_dosing_permitted=False,
                flue_damper_override=False,
                description="Primary chamber temp > 1200.0 C: emergency shutdown to protect refractory brickwork.",
            )

        # Low primary chamber temperature (statutory dioxin destruction requirement)
        if t.primary_chamber_temp_c < 850.0:
            return IncineratorAssessment(
                status=IncineratorStatus.LOW_TEMP_BURNER_LOCKOUT,
                operation_permitted=True,
                burner_shutdown_command=False,
                sludge_dosing_permitted=False,
                flue_damper_override=False,
                description="Chamber temp < 850.0 C: waste oil / sludge dosing inhibited (pilot burner heating active).",
            )

        # Flue gas exhaust high temperature alarm
        if t.flue_gas_temp_c > 380.0:
            return IncineratorAssessment(
                status=IncineratorStatus.FLUE_GAS_HIGH_TEMP_ALARM,
                operation_permitted=True,
                burner_shutdown_command=False,
                sludge_dosing_permitted=True,
                flue_damper_override=True,
                description="Flue gas outlet temp > 380.0 C: high temp alarm; cooling dilution damper opened.",
            )

        return IncineratorAssessment(
            status=IncineratorStatus.NORMAL,
            operation_permitted=True,
            burner_shutdown_command=False,
            sludge_dosing_permitted=True,
            flue_damper_override=False,
            description="Incinerator primary chamber draft and combustion temperatures nominal.",
        )
