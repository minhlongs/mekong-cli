"""Phase 495: OWS 15 ppm Bilge Alarm & 3-Way Recirculation Valve Interlock.
MARPOL Annex I Reg 14 & IMO Res. MEPC.107(49) compliance. Strictly < 95 LOC.
"""
from dataclasses import dataclass
from enum import Enum

class ValveRouting(str, Enum):
    OVERBOARD = "OVERBOARD"
    RECIRC_TO_BILGE_TANK = "RECIRC_TO_BILGE_TANK"

@dataclass(frozen=True)
class OwsTelemetry:
    oil_content_ppm: float
    sample_flow_l_per_min: float
    clean_water_flushing_active: bool = False
    in_special_area: bool = False
    sample_cell_fouled: bool = False

@dataclass(frozen=True)
class OwsAssessment:
    valve_routing: ValveRouting
    overboard_allowed: bool
    alarm_active: bool
    alarm_reason: str
    recirculation_command: bool

class Ows15PpmBilgeAlarmEngine:
    MAX_PERMISSIBLE_PPM = 15.0
    MIN_SAMPLE_FLOW_LPM = 0.5

    @classmethod
    def evaluate(cls, telem: OwsTelemetry) -> OwsAssessment:
        if telem.sample_cell_fouled:
            return OwsAssessment(
                valve_routing=ValveRouting.RECIRC_TO_BILGE_TANK,
                overboard_allowed=False,
                alarm_active=True,
                alarm_reason="SAMPLE_CELL_FOULED_OPTICAL_FAULT",
                recirculation_command=True,
            )
        if telem.clean_water_flushing_active:
            return OwsAssessment(
                valve_routing=ValveRouting.RECIRC_TO_BILGE_TANK,
                overboard_allowed=False,
                alarm_active=False,
                alarm_reason="CLEAN_WATER_FLUSHING_INTERLOCK",
                recirculation_command=True,
            )
        if telem.in_special_area:
            return OwsAssessment(
                valve_routing=ValveRouting.RECIRC_TO_BILGE_TANK,
                overboard_allowed=False,
                alarm_active=True,
                alarm_reason="SPECIAL_AREA_ZERO_DISCHARGE_RESTRICTION",
                recirculation_command=True,
            )
        if telem.sample_flow_l_per_min < cls.MIN_SAMPLE_FLOW_LPM:
            return OwsAssessment(
                valve_routing=ValveRouting.RECIRC_TO_BILGE_TANK,
                overboard_allowed=False,
                alarm_active=True,
                alarm_reason="SAMPLE_FLOW_LOSS_DEFECT",
                recirculation_command=True,
            )
        if telem.oil_content_ppm > cls.MAX_PERMISSIBLE_PPM:
            return OwsAssessment(
                valve_routing=ValveRouting.RECIRC_TO_BILGE_TANK,
                overboard_allowed=False,
                alarm_active=True,
                alarm_reason=f"HIGH_OIL_CONTENT_{telem.oil_content_ppm:.1f}_PPM_EXCEEDS_15PPM",
                recirculation_command=True,
            )
        return OwsAssessment(
            valve_routing=ValveRouting.OVERBOARD,
            overboard_allowed=True,
            alarm_active=False,
            alarm_reason="NORMAL_COMPLIANT_DISCHARGE",
            recirculation_command=False,
        )
