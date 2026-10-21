"""Phase 442: Ballast Water Treatment System Neutralization TRO Dosing & Interlock.

IMO BWM Convention D-2 & USCG Title 33 CFR 151 compliant de-ballasting neutralization engine.
Monitors Total Residual Oxidants (TRO), neutralizer dosing ratio, ORP, and overboard valve interlock.
Strictly < 130 LOC, zero mocks.
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class BwmsNeutralizationTelemetry:
    effluent_tro_mg_l: float
    neutralizer_dosing_flow_l_h: float
    ballast_discharge_flow_m3_h: float
    redox_potential_orp_mv: float
    sample_pump_running: bool


@dataclass(frozen=True)
class BwmsNeutralizationAssessment:
    is_overboard_discharge_permitted: bool
    is_tro_within_discharge_limit: bool
    is_neutralizer_flow_confirmed: bool
    is_orp_normal: bool
    calculated_stoichiometric_ratio: float
    alarms: List[str]
    trips: List[str]
    summary_vi: str
    summary_en: str


class BwmsNeutralizationEngine:
    MAX_DISCHARGE_TRO_MG_L: float = 0.10
    MAX_SAFE_ORP_MV: float = 350.0
    MIN_STOICHIOMETRIC_RATIO: float = 1.05

    def evaluate(self, telemetry: BwmsNeutralizationTelemetry) -> BwmsNeutralizationAssessment:
        alarms: List[str] = []
        trips: List[str] = []

        is_tro_ok = telemetry.effluent_tro_mg_l <= self.MAX_DISCHARGE_TRO_MG_L
        if not is_tro_ok:
            trips.append(f"Effluent TRO {telemetry.effluent_tro_mg_l} mg/L exceeds IMO D-2 limit {self.MAX_DISCHARGE_TRO_MG_L} mg/L")

        if not telemetry.sample_pump_running:
            trips.append("Sample water measurement stream not running, sensor feedback untrusted")

        flow_confirmed = telemetry.neutralizer_dosing_flow_l_h > 0.05
        if not flow_confirmed:
            trips.append("Zero neutralizer dosing chemical flow detected during deballast")

        water_flow = max(1.0, telemetry.ballast_discharge_flow_m3_h)
        # Approximate stoichiometric ratio based on dosing per flow unit
        stoich_ratio = round((telemetry.neutralizer_dosing_flow_l_h * 20.0) / water_flow, 2)
        if stoich_ratio < self.MIN_STOICHIOMETRIC_RATIO:
            alarms.append(f"Neutralizer ratio {stoich_ratio} below safety margin {self.MIN_STOICHIOMETRIC_RATIO}")

        is_orp_ok = telemetry.redox_potential_orp_mv <= self.MAX_SAFE_ORP_MV
        if not is_orp_ok:
            alarms.append(f"Redox potential {telemetry.redox_potential_orp_mv} mV indicates residual oxidant presence")

        permitted = len(trips) == 0 and is_tro_ok

        summary_en = (
            "BWMS deballasting neutralization compliant, discharge permitted"
            if permitted and not alarms
            else f"BWMS discharge interlocked: {len(trips)} trip interlocks, {len(alarms)} warnings"
        )
        summary_vi = (
            "Hệ thống trung hòa nước dằn BWMS đạt chuẩn, cho phép xả mạn"
            if permitted and not alarms
            else f"Khóa xả mạn BWMS: {len(trips)} khóa ngắt, {len(alarms)} cảnh báo"
        )

        return BwmsNeutralizationAssessment(
            is_overboard_discharge_permitted=permitted,
            is_tro_within_discharge_limit=is_tro_ok,
            is_neutralizer_flow_confirmed=flow_confirmed,
            is_orp_normal=is_orp_ok,
            calculated_stoichiometric_ratio=stoich_ratio,
            alarms=alarms,
            trips=trips,
            summary_vi=summary_vi,
            summary_en=summary_en,
        )
