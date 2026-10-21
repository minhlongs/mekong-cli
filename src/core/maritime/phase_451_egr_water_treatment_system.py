"""Phase 451: Marine Diesel Exhaust Gas Recirculation (EGR) Water Treatment System (WTS).

Compliant with IMO Resolution MEPC.307(73) & MARPOL Annex VI Regulation 13.
Controls bleed-off water pH neutralization, particulate centrifuge separation,
turbidity (FNU), and polycyclic aromatic hydrocarbons (PAH) monitoring.
"""

from dataclasses import dataclass
from enum import Enum


class EgrWtsStatus(str, Enum):
    OPTIMAL = "OPTIMAL"
    DEGRADED = "DEGRADED"
    DISCHARGE_PROHIBITED = "DISCHARGE_PROHIBITED"
    EMERGENCY_SHUTDOWN = "EMERGENCY_SHUTDOWN"


@dataclass(frozen=True)
class EgrWtsTelemetry:
    ph_level: float
    turbidity_fnu: float
    pah_ppb: float
    centrifuge_sep_eff_pct: float
    sludge_tank_capacity_pct: float


@dataclass(frozen=True)
class EgrWtsAssessment:
    status: EgrWtsStatus
    overboard_discharge_permitted: bool
    sludge_holding_alarm: bool
    recirculation_required: bool
    remarks: str


class EgrWaterTreatmentEngine:
    MIN_DISCHARGE_PH: float = 6.5
    MAX_DISCHARGE_PH: float = 9.0
    MAX_TURBIDITY_FNU: float = 25.0
    MAX_PAH_PPB: float = 50.0
    MIN_CENTRIFUGE_EFF_PCT: float = 90.0
    SLUDGE_HIGH_LEVEL_TRIP_PCT: float = 85.0

    @classmethod
    def evaluate(cls, telemetry: EgrWtsTelemetry) -> EgrWtsAssessment:
        sludge_trip = telemetry.sludge_tank_capacity_pct >= cls.SLUDGE_HIGH_LEVEL_TRIP_PCT
        centrifuge_fail = telemetry.centrifuge_sep_eff_pct < cls.MIN_CENTRIFUGE_EFF_PCT

        if sludge_trip or centrifuge_fail:
            status = EgrWtsStatus.EMERGENCY_SHUTDOWN
            discharge = False
            recirc = True
            remarks = "EGR WTS trip: Sludge tank full or centrifuge failure"
            return EgrWtsAssessment(status, discharge, sludge_trip, recirc, remarks)

        ph_compliant = cls.MIN_DISCHARGE_PH <= telemetry.ph_level <= cls.MAX_DISCHARGE_PH
        turbidity_compliant = telemetry.turbidity_fnu <= cls.MAX_TURBIDITY_FNU
        pah_compliant = telemetry.pah_ppb <= cls.MAX_PAH_PPB

        if not (ph_compliant and turbidity_compliant and pah_compliant):
            return EgrWtsAssessment(
                status=EgrWtsStatus.DISCHARGE_PROHIBITED,
                overboard_discharge_permitted=False,
                sludge_holding_alarm=False,
                recirculation_required=True,
                remarks="Effluent limits violated: Recirculating bleed-off to buffer tank",
            )

        if telemetry.turbidity_fnu > 20.0 or telemetry.pah_ppb > 40.0:
            return EgrWtsAssessment(
                status=EgrWtsStatus.DEGRADED,
                overboard_discharge_permitted=True,
                sludge_holding_alarm=False,
                recirculation_required=False,
                remarks="Approaching regulatory discharge boundaries",
            )

        return EgrWtsAssessment(
            status=EgrWtsStatus.OPTIMAL,
            overboard_discharge_permitted=True,
            sludge_holding_alarm=False,
            recirculation_required=False,
            remarks="EGR WTS fully compliant with MEPC.307(73)",
        )
