"""Phase 405: Marine Incinerator Flue Gas & Waste Sludge Oil Thermal Destruction.

Complies with IMO MEPC.76(40) Standard Specification for Shipboard Incinerators and MARPOL Annex VI Reg 16.
Governs combustion chamber temperatures, sludge atomization preheating, and port-limit interlocks.
Strictly < 180 LOC, zero-mock deterministic combustion thermodynamics.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class SludgeIncinerationStatus(str, Enum):
    """Safety and combustion state for sludge destruction."""
    PERMITTED_RUNNING = "PERMITTED_RUNNING"
    COMBUSTION_TEMP_LOCKOUT = "COMBUSTION_TEMP_LOCKOUT"
    VISCOSITY_ATOMIZATION_FAULT = "VISCOSITY_ATOMIZATION_FAULT"
    PORT_LIMIT_FORBIDDEN_ZONE = "PORT_LIMIT_FORBIDDEN_ZONE"
    DRAFT_PRESSURE_FAULT = "DRAFT_PRESSURE_FAULT"


@dataclass
class SludgeIncineratorInput:
    """Operational telemetry for marine waste sludge burner."""
    combustion_chamber_temp_c: float = 920.0  # Combustion chamber temp (MEPC.76(40) min 850°C)
    flue_gas_exit_temp_c: float = 280.0  # Flue gas economizer/stack outlet temp (limit < 350°C)
    sludge_service_temp_c: float = 95.0  # Preheating temp in sludge dosing tank
    sludge_viscosity_cst: float = 12.5  # Atomization viscosity at burner nozzle (target 10 - 15 cSt)
    furnace_draft_pressure_mmwc: float = -15.0  # Induced negative draft pressure (target -5 to -25 mmWC)
    in_port_or_estuary: bool = False  # MARPOL Annex VI Reg 16 port operation flag
    flame_scanner_active: bool = True  # UV/IR flame detector healthy
    sludge_water_fraction_pct: float = 18.0  # Emulsified water content in waste oil sludge


@dataclass
class SludgeIncineratorResult:
    """Combustion safety and emission interlock evaluation."""
    status: SludgeIncinerationStatus
    sludge_feed_permitted: bool
    temperature_compliant: bool
    atomization_compliant: bool
    flue_draft_compliant: bool
    burner_safety_interlock: bool
    warnings: List[str] = field(default_factory=list)


class SludgeIncineratorEngine:
    """Combustion safety engine for marine waste oil sludge burning."""

    MIN_COMBUSTION_TEMP_C = 850.0  # Mandatory MEPC.76(40) threshold
    MAX_FLUE_EXIT_TEMP_C = 350.0
    MIN_ATOM_VISCOSITY_CST = 10.0
    MAX_ATOM_VISCOSITY_CST = 15.0
    MIN_DRAFT_MMWC = -25.0
    MAX_DRAFT_MMWC = -5.0

    def evaluate(self, telemetry: SludgeIncineratorInput) -> SludgeIncineratorResult:
        warnings: List[str] = []

        temperature_compliant = (
            telemetry.combustion_chamber_temp_c >= self.MIN_COMBUSTION_TEMP_C
            and telemetry.flue_gas_exit_temp_c <= self.MAX_FLUE_EXIT_TEMP_C
        )
        if telemetry.combustion_chamber_temp_c < self.MIN_COMBUSTION_TEMP_C:
            warnings.append(
                f"Chamber temp {telemetry.combustion_chamber_temp_c}°C < {self.MIN_COMBUSTION_TEMP_C}°C. "
                "Auto-burner sludge dosing valve locked out."
            )
        if telemetry.flue_gas_exit_temp_c > self.MAX_FLUE_EXIT_TEMP_C:
            warnings.append(
                f"Flue exit temp {telemetry.flue_gas_exit_temp_c}°C > {self.MAX_FLUE_EXIT_TEMP_C}°C. High exhaust hazard."
            )

        atomization_compliant = (
            self.MIN_ATOM_VISCOSITY_CST <= telemetry.sludge_viscosity_cst <= self.MAX_ATOM_VISCOSITY_CST
        )
        if not atomization_compliant:
            warnings.append(
                f"Sludge viscosity {telemetry.sludge_viscosity_cst} cSt outside {self.MIN_ATOM_VISCOSITY_CST}-{self.MAX_ATOM_VISCOSITY_CST} cSt. "
                "Risk of unburnt oil dripping or flame impingement."
            )

        flue_draft_compliant = (
            self.MIN_DRAFT_MMWC <= telemetry.furnace_draft_pressure_mmwc <= self.MAX_DRAFT_MMWC
        )
        if not flue_draft_compliant:
            warnings.append(
                f"Furnace draft {telemetry.furnace_draft_pressure_mmwc} mmWC outside {self.MIN_DRAFT_MMWC} to {self.MAX_DRAFT_MMWC} mmWC."
            )

        port_forbidden = telemetry.in_port_or_estuary
        if port_forbidden:
            warnings.append(
                "Vessel located in port, harbor, or estuary: Incineration of waste sludge prohibited by MARPOL Annex VI Reg 16."
            )

        burner_safety_interlock = (
            telemetry.flame_scanner_active
            and not port_forbidden
            and temperature_compliant
            and flue_draft_compliant
        )

        sludge_feed_permitted = burner_safety_interlock and atomization_compliant

        if port_forbidden:
            status = SludgeIncinerationStatus.PORT_LIMIT_FORBIDDEN_ZONE
        elif not temperature_compliant:
            status = SludgeIncinerationStatus.COMBUSTION_TEMP_LOCKOUT
        elif not flue_draft_compliant:
            status = SludgeIncinerationStatus.DRAFT_PRESSURE_FAULT
        elif not atomization_compliant:
            status = SludgeIncinerationStatus.VISCOSITY_ATOMIZATION_FAULT
        else:
            status = SludgeIncinerationStatus.PERMITTED_RUNNING

        return SludgeIncineratorResult(
            status=status,
            sludge_feed_permitted=sludge_feed_permitted,
            temperature_compliant=temperature_compliant,
            atomization_compliant=atomization_compliant,
            flue_draft_compliant=flue_draft_compliant,
            burner_safety_interlock=burner_safety_interlock,
            warnings=warnings,
        )
