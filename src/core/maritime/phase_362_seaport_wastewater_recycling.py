"""Maritime Phase 362: Remote Seaport Wastewater Recycling & Zero-Discharge Engine.

Compliant with MARPOL Annex IV, QCVN 14:2008/BTNMT, and QCVN 40:2011/BTNMT.
Evaluates membrane bioreactor (MBR) effluent BOD5, TDS brackish limits, and zero-liquid discharge (ZLD) recovery rate.
Strictly kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class SeaportWastewaterInput:
    facility_id: str
    influent_flow_m3_day: float
    recycled_permeate_m3_day: float
    effluent_bod5_mg_l: float
    effluent_turbidity_ntu: float
    effluent_coliform_mpn_100ml: float
    feed_tds_mg_l: float
    is_uv_disinfection_active: bool = True


@dataclass
class SeaportWastewaterResult:
    facility_id: str
    water_recovery_rate_percent: float
    is_zld_target_achieved: bool
    is_effluent_compliant: bool
    is_brackish_ro_required: bool
    operational_status: str
    advisories: List[str] = field(default_factory=list)


class SeaportWastewaterEngine:
    """Evaluates wastewater recycling, MBR/UV effluent compliance, and ZLD recovery."""

    MAX_BOD5_LIMIT_MG_L: float = 20.0  # QCVN 14 Class A reuse standard
    MAX_TURBIDITY_NTU: float = 2.0  # Ultrafiltration / MBR permeate standard
    MAX_COLIFORM_MPN: float = 100.0  # Disinfection standard
    MIN_ZLD_RECOVERY_PERCENT: float = 85.0  # Zero liquid discharge target
    BRACKISH_TDS_THRESHOLD_MG_L: float = 1500.0  # High TDS triggers seawater/brackish RO

    @classmethod
    def evaluate(cls, inp: SeaportWastewaterInput) -> SeaportWastewaterResult:
        advisories: List[str] = []

        # 1. Recovery rate calculation
        influent = max(0.1, inp.influent_flow_m3_day)
        recovery_percent = round((inp.recycled_permeate_m3_day / influent) * 100.0, 1)
        is_zld_ok = recovery_percent >= cls.MIN_ZLD_RECOVERY_PERCENT

        if not is_zld_ok:
            advisories.append(
                f"LOW RECOVERY: Water recovery {recovery_percent}% is below {cls.MIN_ZLD_RECOVERY_PERCENT}% ZLD target. High reject discharge."
            )

        # 2. Biological & optical quality checks
        is_bod_ok = inp.effluent_bod5_mg_l <= cls.MAX_BOD5_LIMIT_MG_L
        is_turbidity_ok = inp.effluent_turbidity_ntu <= cls.MAX_TURBIDITY_NTU
        is_coliform_ok = (
            inp.effluent_coliform_mpn_100ml <= cls.MAX_COLIFORM_MPN
            and inp.is_uv_disinfection_active
        )

        if not is_bod_ok:
            advisories.append(f"HIGH BOD5: {inp.effluent_bod5_mg_l} mg/L exceeds 20.0 mg/L limit. Enhance bioreactor aeration.")
        if not is_turbidity_ok:
            advisories.append(f"TURBIDITY ALARM: {inp.effluent_turbidity_ntu} NTU exceeds 2.0 NTU. Membrane fiber breach suspected.")
        if not is_coliform_ok:
            advisories.append("PATHOGEN ALERT: Coliform count exceeded or UV lamp failure. Disinfection compromised.")

        is_effluent_compliant = is_bod_ok and is_turbidity_ok and is_coliform_ok

        # 3. TDS & seawater infiltration check
        is_ro_needed = inp.feed_tds_mg_l > cls.BRACKISH_TDS_THRESHOLD_MG_L
        if is_ro_needed:
            advisories.append(
                f"BRACKISH INTRUSION: Feed TDS {inp.feed_tds_mg_l} mg/L > 1500 mg/L indicates tidal seawater ingress. Secondary RO desalination engaged."
            )

        # Operational status assessment
        if not is_effluent_compliant:
            status = "EFFLUENT_CONTAMINATED_LOCKOUT"
            advisories.append("Recycling line diverted to containment surge tank. Discharge to reuse distribution prohibited.")
        elif not is_zld_ok:
            status = "SUBOPTIMAL_RECOVERY"
        elif is_ro_needed:
            status = "ZLD_RECOVERY_WITH_RO_DESAL"
            advisories.append("Water meets quality standards with active brackish RO polisher.")
        else:
            status = "OPTIMAL_CIRCULAR_RECYCLING"
            advisories.append(f"Recycled {inp.recycled_permeate_m3_day} m3/day ({recovery_percent}%) compliant for terminal washdown and boiler feedwater.")

        return SeaportWastewaterResult(
            facility_id=inp.facility_id,
            water_recovery_rate_percent=recovery_percent,
            is_zld_target_achieved=is_zld_ok,
            is_effluent_compliant=is_effluent_compliant,
            is_brackish_ro_required=is_ro_needed,
            operational_status=status,
            advisories=advisories,
        )
