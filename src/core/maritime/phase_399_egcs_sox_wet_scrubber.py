"""Phase 399: Exhaust Gas Cleaning System (EGCS) SOx Wet Scrubber.

Compliant with IMO MARPOL Annex VI Reg 14 and Resolution MEPC.340(77).
Strictly < 200 LOC, zero external dependencies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class EgcsMode(str, Enum):
    OPEN_LOOP = "OPEN_LOOP"
    CLOSED_LOOP = "CLOSED_LOOP"
    HYBRID = "HYBRID"


@dataclass
class EgcsScrubberInput:
    so2_ppm: float = 12.0
    co2_pct: float = 5.0
    washwater_ph: float = 6.8
    inlet_pah_ug_l: float = 5.0
    discharge_pah_ug_l: float = 15.0
    turbidity_fnu: float = 8.0
    operating_mode: EgcsMode = EgcsMode.OPEN_LOOP
    in_eca_or_restricted_port: bool = False


@dataclass
class EgcsScrubberResult:
    emission_ratio: float
    mepc_340_77_compliant: bool
    sox_washwater_status: str
    naoh_dosing_active: bool
    discharge_lockout: bool
    operating_mode: str
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "emission_ratio": round(self.emission_ratio, 2),
            "mepc_340_77_compliant": self.mepc_340_77_compliant,
            "sox_washwater_status": self.sox_washwater_status,
            "naoh_dosing_active": self.naoh_dosing_active,
            "discharge_lockout": self.discharge_lockout,
            "operating_mode": self.operating_mode,
            "warnings": self.warnings,
        }


class EgcsSoxScrubberEngine:
    """Evaluates marine SOx scrubber gas emissions and washwater discharge criteria."""

    GLOBAL_CAP_RATIO = 21.7  # 0.50% S equivalent
    SECA_CAP_RATIO = 4.3    # 0.10% S equivalent
    MIN_DISCHARGE_PH = 6.5
    MAX_DELTA_PAH_UG_L = 50.0
    MAX_TURBIDITY_FNU = 25.0

    def evaluate(self, inp: EgcsScrubberInput) -> EgcsScrubberResult:
        warnings = []
        co2_val = max(inp.co2_pct, 0.01)
        ratio = inp.so2_ppm / co2_val

        # Check emission ratio against regulatory caps
        max_ratio = self.SECA_CAP_RATIO if inp.in_eca_or_restricted_port else self.GLOBAL_CAP_RATIO
        ratio_compliant = ratio <= max_ratio
        if not ratio_compliant:
            warnings.append(
                f"MARPOL ANNEX VI NON-COMPLIANCE: SO2/CO2 ratio {ratio:.2f} exceeds limit {max_ratio:.1f}"
            )

        # Washwater criteria
        delta_pah = max(0.0, inp.discharge_pah_ug_l - inp.inlet_pah_ug_l)
        ph_ok = inp.washwater_ph >= self.MIN_DISCHARGE_PH
        pah_ok = delta_pah <= self.MAX_DELTA_PAH_UG_L
        turbidity_ok = inp.turbidity_fnu <= self.MAX_TURBIDITY_FNU

        discharge_lockout = False
        naoh_dosing = False

        if inp.operating_mode == EgcsMode.CLOSED_LOOP:
            naoh_dosing = True
            # Closed-loop washwater is recirculated or held onboard
            sox_washwater_status = "CLOSED_LOOP_RECIRCULATION_ACTIVE"
        elif inp.in_eca_or_restricted_port and inp.operating_mode == EgcsMode.OPEN_LOOP:
            discharge_lockout = True
            sox_washwater_status = "OPEN_LOOP_DISCHARGE_PROHIBITED_IN_PORT"
            warnings.append("LOCAL PORT RESTRICTION: Open-loop washwater discharge prohibited in port/ECA")
        elif not ph_ok:
            discharge_lockout = True
            sox_washwater_status = "ACIDIC_DISCHARGE_LOCKED_PH_LOW"
            warnings.append(f"WASHWATER ACIDITY VIOLATION: pH {inp.washwater_ph:.2f} < 6.5")
        elif not pah_ok or not turbidity_ok:
            discharge_lockout = True
            sox_washwater_status = "CONTAMINATED_WASHWATER_PAH_OR_TURBIDITY"
            warnings.append("WASHWATER CONTAMINATION: Delta PAH or turbidity exceeds MEPC.340(77)")
        else:
            sox_washwater_status = "MEPC_340_77_WASHWATER_COMPLIANT"

        compliant = ratio_compliant and (not discharge_lockout or inp.operating_mode == EgcsMode.CLOSED_LOOP)

        return EgcsScrubberResult(
            emission_ratio=ratio,
            mepc_340_77_compliant=compliant,
            sox_washwater_status=sox_washwater_status,
            naoh_dosing_active=naoh_dosing,
            discharge_lockout=discharge_lockout,
            operating_mode=inp.operating_mode.value,
            warnings=warnings,
        )
