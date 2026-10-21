"""Maritime Phase 391: Oily Water Separator (OWS) 15 ppm & Ceramic Membrane.

Complies with IMO Res. MEPC.107(49) and MARPOL Annex I Reg 14.
Zero mock dependencies, strict physical calculations.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class OilyWaterSeparatorInput:
    bilge_oil_content_ppm: float = 8.5
    feed_flow_rate_m3_h: float = 2.5
    transmembrane_pressure_bar: float = 1.2
    vessel_en_route: bool = True
    in_port_or_anchor: bool = False
    three_way_valve_status: str = "OVERBOARD"


@dataclass
class OilyWaterSeparatorResult:
    oil_content_ppm: float
    discharge_permitted: bool
    alarm_status: str
    three_way_valve_command: str
    membrane_fouling_status: str
    regulatory_status: str
    warnings: List[str] = field(default_factory=list)


class OilyWaterSeparatorEngine:
    """Evaluates bilge oily water separation performance under MEPC.107(49)."""

    ALARM_THRESHOLD_PPM = 15.0
    WARNING_THRESHOLD_PPM = 12.0
    TMP_CLEAN_BAR = 1.0
    TMP_DIRTY_BAR = 2.2

    def evaluate(self, inp: OilyWaterSeparatorInput) -> OilyWaterSeparatorResult:
        warnings = []
        oil_ppm = round(inp.bilge_oil_content_ppm, 2)

        # Membrane fouling assessment based on Transmembrane Pressure (TMP)
        if inp.transmembrane_pressure_bar >= self.TMP_DIRTY_BAR:
            membrane_status = "FOULING_CRITICAL_BACKWASH_REQ"
            warnings.append("CERAMIC MEMBRANE FOULING CRITICAL: Backwash sequence mandatory")
        elif inp.transmembrane_pressure_bar > 1.8:
            membrane_status = "FOULING_MODERATE"
        else:
            membrane_status = "NORMAL_PERMEATE"

        # MEPC.107(49) 15 ppm alarm & 3-way diversion valve interlock
        if oil_ppm >= self.ALARM_THRESHOLD_PPM:
            alarm_status = "ALARM_15PPM_EXCEEDED"
            valve_cmd = "DIVERT_TO_BILGE_TANK"
            discharge_ok = False
            warnings.append("MARPOL ANNEX I VIOLATION: Oil content >= 15 ppm, overboard valve locked")
        elif oil_ppm >= self.WARNING_THRESHOLD_PPM:
            alarm_status = "WARNING_PRE_ALARM"
            valve_cmd = "OVERBOARD"
            discharge_ok = inp.vessel_en_route and not inp.in_port_or_anchor
        else:
            alarm_status = "NOMINAL_SAFE"
            valve_cmd = "OVERBOARD"
            discharge_ok = inp.vessel_en_route and not inp.in_port_or_anchor

        # Navigational gating: Vessel must be en route and not in port/anchor
        if inp.in_port_or_anchor:
            discharge_ok = False
            valve_cmd = "DIVERT_TO_BILGE_TANK"
            regulatory = "DISCHARGE_PROHIBITED_IN_PORT"
            warnings.append("ZERO DISCHARGE: Vessel in port or at anchor")
        elif not inp.vessel_en_route:
            discharge_ok = False
            valve_cmd = "DIVERT_TO_BILGE_TANK"
            regulatory = "DISCHARGE_PROHIBITED_VESSEL_NOT_EN_ROUTE"
            warnings.append("VESSEL NOT EN ROUTE: En route requirement violated under MARPOL Reg 14")
        elif oil_ppm >= self.ALARM_THRESHOLD_PPM:
            regulatory = "OVERBOARD_DISCHARGE_LOCKED_15PPM"
        else:
            regulatory = "MEPC_107_49_COMPLIANT_DISCHARGE_PERMITTED"

        return OilyWaterSeparatorResult(
            oil_content_ppm=oil_ppm,
            discharge_permitted=discharge_ok,
            alarm_status=alarm_status,
            three_way_valve_command=valve_cmd,
            membrane_fouling_status=membrane_status,
            regulatory_status=regulatory,
            warnings=warnings,
        )
