"""Phase 345: Marine Boiler Water Treatment & Chemical Conditioning Engine.

Implements ISO 5814, BS 2486, and marine classification society standards
for boiler water quality, pH buffering, chloride stress-corrosion limits,
oxygen scavenging (hydrazine), phosphate reserve, and blowdown calculation.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BoilerWaterInput:
    boiler_id: str
    boiler_type: str = "AUXILIARY"  # "AUXILIARY", "HIGH_PRESSURE"
    operating_pressure_bar: float = 8.5
    water_ph: float = 10.2
    chloride_ppm: float = 120.0
    p_alkalinity_ppm: float = 180.0
    phosphate_ppm: float = 30.0
    hydrazine_ppm: float = 0.12
    feedwater_chloride_ppm: float = 5.0


@dataclass
class BoilerWaterResult:
    boiler_id: str
    boiler_type: str
    ph_compliant: bool
    chloride_compliant: bool
    alkalinity_compliant: bool
    phosphate_compliant: bool
    scavenger_compliant: bool
    recommended_blowdown_pct: float
    overall_status: str  # "OPTIMAL", "ACCEPTABLE", "CRITICAL_ACTION_REQUIRED"
    chemical_actions: List[str] = field(default_factory=list)
    advisories: List[str] = field(default_factory=list)


class BoilerWaterTreatmentEngine:
    @classmethod
    def evaluate(cls, inp: BoilerWaterInput) -> BoilerWaterResult:
        chemical_actions: List[str] = []
        advisories: List[str] = []

        is_hp = inp.boiler_type.upper() == "HIGH_PRESSURE"
        # Set reference thresholds
        ph_min, ph_max = (9.8, 10.5) if is_hp else (9.5, 11.0)
        max_cl = 30.0 if is_hp else 300.0
        alk_min, alk_max = (50.0, 150.0) if is_hp else (100.0, 300.0)
        po4_min, po4_max = (15.0, 30.0) if is_hp else (20.0, 50.0)
        n2h4_min, n2h4_max = (0.02, 0.10) if is_hp else (0.05, 0.25)

        # 1. Parameter compliance
        ph_ok = ph_min <= inp.water_ph <= ph_max
        cl_ok = inp.chloride_ppm <= max_cl
        alk_ok = alk_min <= inp.p_alkalinity_ppm <= alk_max
        po4_ok = po4_min <= inp.phosphate_ppm <= po4_max
        n2h4_ok = n2h4_min <= inp.hydrazine_ppm <= n2h4_max

        # 2. Chemical actions & advisories
        if not ph_ok:
            if inp.water_ph < ph_min:
                chemical_actions.append("Dose alkaline booster (Sodium Hydroxide) to raise pH.")
            else:
                chemical_actions.append("Increase bottom blowdown to reduce caustic alkalinity.")

        if not cl_ok:
            advisories.append(f"CHLORIDE CORROSION ALERT: Chloride {inp.chloride_ppm} ppm > limit {max_cl} ppm.")
            chemical_actions.append("Perform urgent bottom blowdown to expel accumulated chloride salts.")

        if not po4_ok:
            if inp.phosphate_ppm < po4_min:
                chemical_actions.append("Dose sodium phosphate sludge conditioner to prevent hard scale.")
            else:
                advisories.append(f"HIGH PHOSPHATE: Excess phosphate {inp.phosphate_ppm} ppm may cause carryover.")

        if not n2h4_ok:
            if inp.hydrazine_ppm < n2h4_min:
                chemical_actions.append("Increase hydrazine/DEHA oxygen scavenger dosing to prevent pitting.")
            else:
                advisories.append("HIGH OXYGEN SCAVENGER: Reduce hydrazine dosing rate.")

        # 3. Continuous / intermittent blowdown rate calculation
        if cl_ok:
            target_cl = max_cl * 0.7  # target buffer
        else:
            target_cl = max_cl

        if target_cl > inp.feedwater_chloride_ppm:
            blowdown_pct = round((inp.feedwater_chloride_ppm / (target_cl - inp.feedwater_chloride_ppm)) * 100.0, 2)
        else:
            blowdown_pct = 15.0

        if not cl_ok:
            blowdown_pct = max(blowdown_pct, 10.0)

        # 4. Overall status determination
        violations = sum(not x for x in [ph_ok, cl_ok, alk_ok, po4_ok, n2h4_ok])
        if not cl_ok or inp.water_ph < 9.0:
            overall_status = "CRITICAL_ACTION_REQUIRED"
        elif violations == 0:
            overall_status = "OPTIMAL"
            advisories.append("BOILER WATER SOUND: All chemical parameters within optimal operating envelope.")
        else:
            overall_status = "ACCEPTABLE"

        return BoilerWaterResult(
            boiler_id=inp.boiler_id,
            boiler_type=inp.boiler_type,
            ph_compliant=ph_ok,
            chloride_compliant=cl_ok,
            alkalinity_compliant=alk_ok,
            phosphate_compliant=po4_ok,
            scavenger_compliant=n2h4_ok,
            recommended_blowdown_pct=blowdown_pct,
            overall_status=overall_status,
            chemical_actions=chemical_actions,
            advisories=advisories,
        )
