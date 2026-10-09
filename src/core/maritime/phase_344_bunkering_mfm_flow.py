"""Phase 344: Bunkering MFM Coriolis Mass Balance & Cappuccino Alert Engine.

Implements Singapore SS 648:2019 and ISO 22192 standards for Coriolis Mass
Flow Metering bunkering verification, aerated bunker (cappuccino effect)
detection via drive gain, mass balance dispute thresholds, and NoP generation.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BunkeringMfmInput:
    bunker_id: str
    fuel_grade: str = "VLSFO"  # "VLSFO", "MGO", "ULSFO"
    mfm_totalizer_mass_mt: float = 500.0  # Mass delivered by barge MFM
    vessel_sounding_mass_mt: float = 495.0  # Mass received by vessel soundings
    average_drive_gain_pct: float = 45.0  # Coriolis tube drive gain (< 80% normal)
    fuel_density_kg_m3: float = 985.0
    density_fluctuation_pct: float = 0.5  # Sudden drop indicates aeration
    sulfur_content_pct: float = 0.48
    is_eca_zone: bool = False


@dataclass
class BunkeringMfmResult:
    bunker_id: str
    fuel_grade: str
    mass_discrepancy_mt: float
    discrepancy_pct: float
    cappuccino_effect_detected: bool
    is_mpe_compliant: bool  # MPE within +/- 0.5%
    sulfur_compliant: bool
    notice_of_protest_required: bool
    bunker_status: str  # "ACCEPTED", "DISPUTED", "REJECTED"
    advisories: List[str] = field(default_factory=list)


class BunkeringMfmEngine:
    MPE_LIMIT_PCT = 0.5  # Maximum Permissible Error 0.5% per SS 648
    DRIVE_GAIN_ALERT_PCT = 80.0
    DENSITY_FLUCTUATION_LIMIT_PCT = 2.0
    SULFUR_CAP_GLOBAL = 0.50
    SULFUR_CAP_ECA = 0.10

    @classmethod
    def evaluate(cls, inp: BunkeringMfmInput) -> BunkeringMfmResult:
        advisories: List[str] = []

        # 1. Mass balance calculation
        diff_mt = round(inp.mfm_totalizer_mass_mt - inp.vessel_sounding_mass_mt, 3)
        if inp.mfm_totalizer_mass_mt > 0:
            pct_diff = round((abs(diff_mt) / inp.mfm_totalizer_mass_mt) * 100.0, 3)
        else:
            pct_diff = 0.0

        is_mpe_ok = pct_diff <= cls.MPE_LIMIT_PCT

        # 2. Cappuccino effect / entrained air detection per SS 648
        aerated = (
            inp.average_drive_gain_pct >= cls.DRIVE_GAIN_ALERT_PCT
            or inp.density_fluctuation_pct >= cls.DENSITY_FLUCTUATION_LIMIT_PCT
        )

        if aerated:
            advisories.append(
                f"CAPPUCCINO EFFECT ALERT: Drive gain {inp.average_drive_gain_pct}% >= 80% or "
                f"density drop {inp.density_fluctuation_pct}% indicates entrained air / aerated fuel."
            )

        # 3. Sulfur cap verification per MARPOL Annex VI
        sulfur_limit = cls.SULFUR_CAP_ECA if inp.is_eca_zone else cls.SULFUR_CAP_GLOBAL
        sulfur_ok = inp.sulfur_content_pct <= sulfur_limit
        if not sulfur_ok:
            advisories.append(
                f"MARPOL ANNEX VI VIOLATION: Sulfur {inp.sulfur_content_pct}% exceeds {sulfur_limit}% statutory limit."
            )

        # 4. Dispute status and Notice of Protest (NoP)
        nop_needed = (not is_mpe_ok) or aerated or (not sulfur_ok)

        if not sulfur_ok:
            bunker_status = "REJECTED"
            advisories.append("BUNKER REJECTED: Off-spec fuel must not be consumed; request debunkering.")
        elif nop_needed:
            bunker_status = "DISPUTED"
            advisories.append(
                f"NOTICE OF PROTEST ISSUED: Mass difference {diff_mt:.2f} MT ({pct_diff:.2f}%) exceeds MPE tolerance (0.5%)."
            )
        else:
            bunker_status = "ACCEPTED"
            advisories.append("BUNKERING APPROVED: Mass balance and fuel quality fully conform to SS 648:2019.")

        return BunkeringMfmResult(
            bunker_id=inp.bunker_id,
            fuel_grade=inp.fuel_grade,
            mass_discrepancy_mt=diff_mt,
            discrepancy_pct=pct_diff,
            cappuccino_effect_detected=aerated,
            is_mpe_compliant=is_mpe_ok,
            sulfur_compliant=sulfur_ok,
            notice_of_protest_required=nop_needed,
            bunker_status=bunker_status,
            advisories=advisories,
        )
