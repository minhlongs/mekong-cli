"""Phase 445: Cargo Hold Toxic H2S Gas Detection & Vapor Extraction Fan Safety Interlock.

Compliance:
- IMO MSC.268(85) IMSBC Code (Bulk Cargo Toxic & Combustible Gas Control)
- ISGOTT Ch.2 & IMO MSC.282(86) SOLAS VI Reg 5-2
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ToxicGasExtractionTelemetry:
    h2s_concentration_ppm: float
    lel_combustible_pct: float
    fan_dp_pascals: float
    exhaust_temp_celsius: float
    extraction_fan_running: bool


@dataclass(frozen=True)
class ToxicGasExtractionAssessment:
    is_safe: bool
    h2s_alarm: bool
    h2s_evacuation_trip: bool
    lel_combustible_trip: bool
    ventilation_failure: bool
    exhaust_overtemp_alarm: bool
    emergency_booster_fan_required: bool
    active_alarms: List[str]


class ToxicGasExtractionEngine:
    TLV_TWA_H2S_PPM: float = 5.0
    CRITICAL_H2S_PPM: float = 10.0
    MAX_SAFE_LEL_PCT: float = 10.0
    TRIP_LEL_PCT: float = 20.0
    MIN_FAN_DP_PA: float = 250.0
    MAX_EXHAUST_TEMP_C: float = 60.0

    def evaluate(self, telem: ToxicGasExtractionTelemetry) -> ToxicGasExtractionAssessment:
        alarms: List[str] = []
        h2s_warn = telem.h2s_concentration_ppm > self.TLV_TWA_H2S_PPM
        h2s_trip = telem.h2s_concentration_ppm > self.CRITICAL_H2S_PPM

        lel_trip = telem.lel_combustible_pct > self.TRIP_LEL_PCT
        lel_warn = telem.lel_combustible_pct > self.MAX_SAFE_LEL_PCT

        vent_fail = (not telem.extraction_fan_running) or (telem.fan_dp_pascals < self.MIN_FAN_DP_PA)
        overtemp = telem.exhaust_temp_celsius > self.MAX_EXHAUST_TEMP_C

        if h2s_trip:
            alarms.append("CRITICAL: H2S concentration severe (>10 ppm) - initiate evacuation")
        elif h2s_warn:
            alarms.append("WARNING: H2S concentration above TLV-TWA threshold (>5 ppm)")

        if lel_trip:
            alarms.append("CRITICAL: Explosive hydrocarbon vapor limit exceeded (>20% LEL)")
        elif lel_warn:
            alarms.append("WARNING: Elevated combustible vapor detected (>10% LEL)")

        if vent_fail:
            alarms.append("CRITICAL: Cargo hold extraction fan flow failure (DP < 250 Pa)")

        if overtemp:
            alarms.append("WARNING: ATEX extraction fan motor/duct temperature high (>60°C)")

        is_safe = not (h2s_trip or lel_trip or vent_fail)
        booster_req = h2s_warn or lel_warn or vent_fail

        return ToxicGasExtractionAssessment(
            is_safe=is_safe,
            h2s_alarm=h2s_warn,
            h2s_evacuation_trip=h2s_trip,
            lel_combustible_trip=lel_trip,
            ventilation_failure=vent_fail,
            exhaust_overtemp_alarm=overtemp,
            emergency_booster_fan_required=booster_req,
            active_alarms=alarms,
        )
