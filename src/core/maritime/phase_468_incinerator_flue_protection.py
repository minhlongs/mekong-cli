"""Phase 468: Marine Waste Incinerator Flue Gas High Temperature & Vacuum Protection Engine.

Complies with:
- MARPOL Annex VI Reg. 16 (Shipboard Incineration)
- IMO Res. MEPC.76(40) / MEPC.244(66) (Standard Specification for Shipboard Incinerators)
- Flue gas temperature envelope: trip waste burner if flue gas T >= 350.0 deg C (warning >= 320.0 deg C)
- Combustion chamber negative pressure (draft vacuum): -20 to -50 mm WG (-2.0 to -5.0 mbar)
- Furnace draft trip if draft pressure >= -5.0 mm WG (loss of negative draft / risk of flareback)
- Combustion chamber temperature permissive: primary chamber >= 850.0 deg C before waste sludge feed

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class IncineratorStatus(str, Enum):
    NORMAL = "NORMAL"
    HIGH_FLUE_TEMP_WARNING = "HIGH_FLUE_TEMP_WARNING"
    FLUE_OVERHEAT_TRIP = "FLUE_OVERHEAT_TRIP"
    DRAFT_LOSS_TRIP = "DRAFT_LOSS_TRIP"
    CHAMBER_UNDER_TEMP_INTERLOCK = "CHAMBER_UNDER_TEMP_INTERLOCK"


@dataclass(frozen=True)
class IncineratorTelemetry:
    primary_chamber_temp_c: float
    flue_gas_temp_c: float
    furnace_draft_mm_wg: float  # Negative value represents vacuum
    sludge_burn_valve_open: bool
    induced_draft_fan_running: bool


@dataclass(frozen=True)
class IncineratorAssessment:
    status: IncineratorStatus
    waste_feed_permissive: bool
    emergency_damper_open: bool
    remarks: str


class IncineratorProtectionEngine:
    MAX_FLUE_TRIP_TEMP_C: float = 350.0
    MAX_FLUE_WARN_TEMP_C: float = 320.0
    MAX_DRAFT_PRESSURE_MM_WG: float = -5.0  # If draft rises above -5 mm WG (e.g. -2 mm WG), draft is lost
    MIN_CHAMBER_BURN_TEMP_C: float = 850.0

    @classmethod
    def evaluate(cls, telemetry: IncineratorTelemetry) -> IncineratorAssessment:
        if not telemetry.induced_draft_fan_running or telemetry.furnace_draft_mm_wg >= cls.MAX_DRAFT_PRESSURE_MM_WG:
            return IncineratorAssessment(
                status=IncineratorStatus.DRAFT_LOSS_TRIP,
                waste_feed_permissive=False,
                emergency_damper_open=True,
                remarks=f"Loss of negative draft: draft {telemetry.furnace_draft_mm_wg} mm WG >= {cls.MAX_DRAFT_PRESSURE_MM_WG} mm WG or fan stopped.",
            )

        if telemetry.flue_gas_temp_c >= cls.MAX_FLUE_TRIP_TEMP_C:
            return IncineratorAssessment(
                status=IncineratorStatus.FLUE_OVERHEAT_TRIP,
                waste_feed_permissive=False,
                emergency_damper_open=True,
                remarks=f"Flue gas overheat trip: flue temp {telemetry.flue_gas_temp_c}C >= {cls.MAX_FLUE_TRIP_TEMP_C}C.",
            )

        if telemetry.sludge_burn_valve_open and telemetry.primary_chamber_temp_c < cls.MIN_CHAMBER_BURN_TEMP_C:
            return IncineratorAssessment(
                status=IncineratorStatus.CHAMBER_UNDER_TEMP_INTERLOCK,
                waste_feed_permissive=False,
                emergency_damper_open=False,
                remarks=f"Sludge feed interlock: chamber temp {telemetry.primary_chamber_temp_c}C below MARPOL min {cls.MIN_CHAMBER_BURN_TEMP_C}C.",
            )

        if telemetry.flue_gas_temp_c >= cls.MAX_FLUE_WARN_TEMP_C:
            return IncineratorAssessment(
                status=IncineratorStatus.HIGH_FLUE_TEMP_WARNING,
                waste_feed_permissive=True,
                emergency_damper_open=False,
                remarks=f"High flue temp warning: {telemetry.flue_gas_temp_c}C >= {cls.MAX_FLUE_WARN_TEMP_C}C. Modulate burner load.",
            )

        return IncineratorAssessment(
            status=IncineratorStatus.NORMAL,
            waste_feed_permissive=telemetry.primary_chamber_temp_c >= cls.MIN_CHAMBER_BURN_TEMP_C,
            emergency_damper_open=False,
            remarks="Incinerator operation compliant with MARPOL VI Reg 16.",
        )
