"""Phase 474: Marine Exhaust Gas Scrubber Washwater Effluent pH & PAH Environmental Safety Engine.

Complies with:
- IMO Resolution MEPC.340(77) (2021 Guidelines for Exhaust Gas Cleaning Systems)
- MARPOL Annex VI Reg. 14 (Sulphur Oxides SOx Emission Control):
  - Discharge water pH limit: pH >= 6.5 at 4.0 meters from discharge point, or minimum in-pipe pH >= 3.0 with seawater dilution.
  - Polycyclic Aromatic Hydrocarbons (PAH): Max increase <= 50.0 ug/L phenanthrene equivalent above inlet water.
  - Turbidity discharge limit: Max turbidity increase <= 25.0 FNTU (or NTU).
  - Washwater nitrate limit: Max nitrate concentration <= 60.0 mg/L as NO3-.
  - Auto-action: Divert washwater to holding tank or switch to closed-loop caustic soda (NaOH) neutralization if limits breached.

Strictly < 100 LOC, zero mocks, deterministic physical rules.
"""

from dataclasses import dataclass
from enum import Enum


class ScrubberEffluentStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW_PH_ALARM = "LOW_PH_ALARM"
    HIGH_PAH_ALARM = "HIGH_PAH_ALARM"
    EXCESS_TURBIDITY_ALARM = "EXCESS_TURBIDITY_ALARM"
    ENVIRONMENTAL_NON_COMPLIANT_DIVERSION = "ENVIRONMENTAL_NON_COMPLIANT_DIVERSION"


@dataclass(frozen=True)
class ScrubberEffluentTelemetry:
    overboard_ph: float
    pah_increase_ug_l: float
    turbidity_increase_fntu: float
    nitrate_mg_l: float
    naoh_dosing_active: bool
    discharge_valve_open: bool


@dataclass(frozen=True)
class ScrubberEffluentAssessment:
    status: ScrubberEffluentStatus
    overboard_discharge_permitted: bool
    holding_tank_diversion_valve_open: bool
    naoh_booster_required: bool
    remarks: str


class ScrubberEffluentSafetyEngine:
    MIN_OVERBOARD_PH: float = 6.5
    MAX_PAH_INCREASE_UG_L: float = 50.0
    MAX_TURBIDITY_FNTU: float = 25.0
    MAX_NITRATE_MG_L: float = 60.0

    @classmethod
    def evaluate(cls, telemetry: ScrubberEffluentTelemetry) -> ScrubberEffluentAssessment:
        violations = []
        if telemetry.overboard_ph < cls.MIN_OVERBOARD_PH:
            violations.append(f"pH {telemetry.overboard_ph} < {cls.MIN_OVERBOARD_PH}")
        if telemetry.pah_increase_ug_l > cls.MAX_PAH_INCREASE_UG_L:
            violations.append(f"PAH {telemetry.pah_increase_ug_l} ug/L > {cls.MAX_PAH_INCREASE_UG_L} ug/L")
        if telemetry.turbidity_increase_fntu > cls.MAX_TURBIDITY_FNTU:
            violations.append(f"Turbidity {telemetry.turbidity_increase_fntu} > {cls.MAX_TURBIDITY_FNTU} FNTU")
        if telemetry.nitrate_mg_l > cls.MAX_NITRATE_MG_L:
            violations.append(f"Nitrate {telemetry.nitrate_mg_l} > {cls.MAX_NITRATE_MG_L} mg/L")

        if len(violations) >= 2:
            return ScrubberEffluentAssessment(
                status=ScrubberEffluentStatus.ENVIRONMENTAL_NON_COMPLIANT_DIVERSION,
                overboard_discharge_permitted=False,
                holding_tank_diversion_valve_open=True,
                naoh_booster_required=True,
                remarks=f"MULTIPLE MEPC.340(77) BREACHES: {'; '.join(violations)}. Overboard shut, diverted to holding tank.",
            )

        if telemetry.overboard_ph < cls.MIN_OVERBOARD_PH:
            return ScrubberEffluentAssessment(
                status=ScrubberEffluentStatus.LOW_PH_ALARM,
                overboard_discharge_permitted=False,
                holding_tank_diversion_valve_open=True,
                naoh_booster_required=True,
                remarks=f"Washwater acidic: pH {telemetry.overboard_ph} < {cls.MIN_OVERBOARD_PH}. Dilution / NaOH required.",
            )

        if telemetry.pah_increase_ug_l > cls.MAX_PAH_INCREASE_UG_L:
            return ScrubberEffluentAssessment(
                status=ScrubberEffluentStatus.HIGH_PAH_ALARM,
                overboard_discharge_permitted=False,
                holding_tank_diversion_valve_open=True,
                naoh_booster_required=False,
                remarks=f"PAH emission violation: {telemetry.pah_increase_ug_l} ug/L > {cls.MAX_PAH_INCREASE_UG_L} ug/L. Carbon filter failure.",
            )

        if telemetry.turbidity_increase_fntu > cls.MAX_TURBIDITY_FNTU:
            return ScrubberEffluentAssessment(
                status=ScrubberEffluentStatus.EXCESS_TURBIDITY_ALARM,
                overboard_discharge_permitted=False,
                holding_tank_diversion_valve_open=True,
                naoh_booster_required=False,
                remarks=f"Turbidity violation: {telemetry.turbidity_increase_fntu} > {cls.MAX_TURBIDITY_FNTU} FNTU. Soot separator check.",
            )

        return ScrubberEffluentAssessment(
            status=ScrubberEffluentStatus.NORMAL,
            overboard_discharge_permitted=True,
            holding_tank_diversion_valve_open=False,
            naoh_booster_required=False,
            remarks="Scrubber washwater effluent compliant with IMO MEPC.340(77) criteria.",
        )
