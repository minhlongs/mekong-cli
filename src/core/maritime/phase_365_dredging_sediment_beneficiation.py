"""Maritime Phase 365: Port Dredging Sediment Quality & Beneficial Reuse Engine.

Compliant with London Protocol 1996 and Vietnam QCVN 43:2017/BTNMT (Marine Sediment).
Evaluates heavy metal/PAH/TBT toxicity, solids dewatering, and geotechnical UCS for port reclamation.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DredgedSedimentInput:
    batch_id: str
    tbt_mg_kg: float
    total_pah_mg_kg: float
    heavy_metals: Dict[str, float]
    solids_content_pct: float
    stabilized_ucs_kpa: float


@dataclass
class SedimentReuseResult:
    batch_id: str
    sediment_class: str
    is_open_sea_dump_permitted: bool
    is_beneficial_reuse_approved: bool
    reuse_destination: str
    compliance_status: str
    advisories: List[str] = field(default_factory=list)


class DredgingSedimentBeneficiationEngine:
    """Evaluates sediment chemical contamination and geotechnical criteria for port reclamation."""

    TBT_MAX_LIMIT_MG_KG: float = 0.001
    PAH_CLASS_1_LIMIT_MG_KG: float = 10.0
    MIN_SOLIDS_REUSE_PCT: float = 60.0
    MIN_UCS_REUSE_KPA: float = 50.0

    # QCVN 43:2017/BTNMT Class 1 thresholds (mg/kg dry weight)
    CLASS_1_METALS: Dict[str, float] = {
        "as": 20.0,
        "cd": 1.5,
        "pb": 50.0,
        "hg": 0.4,
        "cu": 65.0,
        "zn": 200.0,
    }

    @classmethod
    def evaluate(cls, inp: DredgedSedimentInput) -> SedimentReuseResult:
        advisories: List[str] = []

        # TBT organotin zero-tolerance check for offshore dumping
        tbt_exceeded = inp.tbt_mg_kg > cls.TBT_MAX_LIMIT_MG_KG
        if tbt_exceeded:
            advisories.append(
                f"ĐỘC TÍNH NẶNG: Nồng độ Tributyltin (TBT) {inp.tbt_mg_kg} mg/kg vượt ngưỡng {cls.TBT_MAX_LIMIT_MG_KG} mg/kg. CẤM ĐỔ BIỂN."
            )

        # PAH check
        pah_exceeded = inp.total_pah_mg_kg > cls.PAH_CLASS_1_LIMIT_MG_KG
        if pah_exceeded:
            advisories.append(
                f"CẢNH BÁO: Tổng PAH {inp.total_pah_mg_kg} mg/kg vượt ngưỡng Loại 1 ({cls.PAH_CLASS_1_LIMIT_MG_KG} mg/kg)."
            )

        # Heavy metal toxicity check against QCVN 43:2017 Class 1
        metal_violations: List[str] = []
        for metal, limit in cls.CLASS_1_METALS.items():
            val = inp.heavy_metals.get(metal, 0.0)
            if val > limit:
                metal_violations.append(f"{metal.upper()} ({val} > {limit})")

        if metal_violations:
            advisories.append(
                f"Ô NHIỄM KIM LOẠI: Vượt ngưỡng QCVN 43 Loại 1 tại: {', '.join(metal_violations)} mg/kg."
            )

        # Determine sediment chemical class
        is_chemically_clean = (not tbt_exceeded) and (not pah_exceeded) and (len(metal_violations) == 0)
        sediment_class = "CLASS_1_CLEAN" if is_chemically_clean else ("CLASS_2_MODERATE" if not tbt_exceeded else "CLASS_3_HAZARDOUS")

        # Open sea dumping permission (strict London Protocol & QCVN 43)
        open_sea_ok = is_chemically_clean

        # Geotechnical beneficial reuse gate (solids >= 60%, stabilized UCS >= 50 kPa)
        geotech_ok = (inp.solids_content_pct >= cls.MIN_SOLIDS_REUSE_PCT) and (inp.stabilized_ucs_kpa >= cls.MIN_UCS_REUSE_KPA)

        if not geotech_ok:
            if inp.solids_content_pct < cls.MIN_SOLIDS_REUSE_PCT:
                advisories.append(
                    f"ĐỊA KỸ THUẬT: Hàm lượng chất rắn {inp.solids_content_pct}% < 60.0%, cần vắt nước/lắng tách."
                )
            if inp.stabilized_ucs_kpa < cls.MIN_UCS_REUSE_KPA:
                advisories.append(
                    f"CƯỜNG ĐỘ: Cường độ nén nở hông UCS {inp.stabilized_ucs_kpa} kPa < 50.0 kPa, cần gia cố xi măng/vôi."
                )

        # Beneficial reuse approved if not hazardous and geotechnical criteria met
        reuse_approved = (sediment_class in ("CLASS_1_CLEAN", "CLASS_2_MODERATE")) and geotech_ok

        if reuse_approved:
            reuse_destination = "PORT_RECLAMATION_CONTAINER_DYKES"
            compliance_status = "APPROVED_FOR_BENEFICIAL_REUSE"
        elif open_sea_ok:
            reuse_destination = "OFFSHORE_DESIGNATED_DISPOSAL_SITE"
            compliance_status = "PERMITTED_FOR_OPEN_SEA_DUMPING"
        else:
            reuse_destination = "CONFINED_HAZARDOUS_DISPOSAL_FACILITY"
            compliance_status = "REJECTED_CONFINED_TREATMENT_REQUIRED"

        return SedimentReuseResult(
            batch_id=inp.batch_id,
            sediment_class=sediment_class,
            is_open_sea_dump_permitted=open_sea_ok,
            is_beneficial_reuse_approved=reuse_approved,
            reuse_destination=reuse_destination,
            compliance_status=compliance_status,
            advisories=advisories,
        )
