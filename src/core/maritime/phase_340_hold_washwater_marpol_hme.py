"""Phase 340: Cargo Hold Washwater & Cleaning MARPOL Annex V HME Engine.

Evaluates cargo residue classification (HME vs Non-HME per Res. MEPC.295(71)),
washwater discharge authorization based on distance from land and special areas,
chemical cleaning dosage, and effluent pH neutralization criteria.
Strictly adheres to KISS/YAGNI/DRY and kept under 200 lines.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HoldCleaningInput:
    hold_id: str
    cargo_name: str
    is_hme: bool = False  # Harmful to the Marine Environment
    distance_from_nearest_land_nm: float = 12.0
    is_in_special_area: bool = False  # Baltic, Mediterranean, Red Sea, etc.
    vessel_en_route: bool = True
    washwater_volume_m3: float = 50.0
    cleaning_agent_ppm: float = 500.0  # Recommended dosage PPM
    effluent_ph: float = 7.2
    port_reception_available: bool = True


@dataclass
class HoldCleaningResult:
    hold_id: str
    cargo_name: str
    is_hme: bool
    discharge_permitted: bool
    destination: str  # "SEA_DISCHARGE" or "PORT_RECEPTION_FACILITY"
    chemical_required_liters: float
    ph_neutralized: bool
    requires_garbage_record_entry: bool
    advisories: List[str] = field(default_factory=list)


class HoldWashwaterMarpolEngine:
    MIN_DISCHARGE_DISTANCE_NM = 12.0
    PH_MIN = 6.5
    PH_MAX = 8.5

    @classmethod
    def evaluate(cls, inp: HoldCleaningInput) -> HoldCleaningResult:
        advisories: List[str] = []

        # 1. Chemical detergent volume: V_chem = V_wash * PPM * 10^-6 * 1000 (Liters)
        chem_liters = round(inp.washwater_volume_m3 * inp.cleaning_agent_ppm * 0.001, 2)

        # 2. pH compliance check
        ph_ok = cls.PH_MIN <= inp.effluent_ph <= cls.PH_MAX
        if not ph_ok:
            advisories.append(f"pH VIOLATION: Effluent pH {inp.effluent_ph} outside safe marine window [6.5, 8.5]. Neutralization required.")

        # 3. Discharge decision per MARPOL Annex V
        discharge_permitted = False
        destination = "PORT_RECEPTION_FACILITY"

        if inp.is_hme:
            discharge_permitted = False
            destination = "PORT_RECEPTION_FACILITY"
            advisories.append("MARPOL ANNEX V HME RESTRICTION: Cargo residues classified as HME. Discharge at sea is strictly prohibited worldwide.")
            advisories.append("MANDATORY PRF: Hold washwater must be retained on board and discharged to Port Reception Facility.")
        else:
            # Non-HME cargo residues
            if not inp.vessel_en_route:
                discharge_permitted = False
                advisories.append("DISCHARGE BARRED: Vessel is not en route. Sea discharge requires vessel underway.")
            elif inp.distance_from_nearest_land_nm < cls.MIN_DISCHARGE_DISTANCE_NM:
                discharge_permitted = False
                advisories.append(f"DISTANCE BARRED: Distance {inp.distance_from_nearest_land_nm} NM < {cls.MIN_DISCHARGE_DISTANCE_NM} NM from nearest land.")
            elif inp.is_in_special_area:
                # Inside Special Area: only allowed if departure and destination ports lack PRF
                if not inp.port_reception_available and ph_ok:
                    discharge_permitted = True
                    destination = "SEA_DISCHARGE"
                    advisories.append("SPECIAL AREA EXCEPTION: No reception facilities available at ports of departure/destination. Discharge permitted >= 12 NM.")
                else:
                    discharge_permitted = False
                    destination = "PORT_RECEPTION_FACILITY"
                    advisories.append("SPECIAL AREA RESTRICTION: Washwater discharge barred inside Special Area when port reception is available.")
            else:
                # Outside special area and >= 12 NM and en route
                if ph_ok:
                    discharge_permitted = True
                    destination = "SEA_DISCHARGE"
                    advisories.append("SEA DISCHARGE PERMITTED: Non-HME residue en route >= 12 NM outside special area with pH neutralized.")
                else:
                    discharge_permitted = False
                    advisories.append("DISCHARGE SUSPENDED: Effluent pH out of spec. Must neutralize before overboard release.")

        return HoldCleaningResult(
            hold_id=inp.hold_id,
            cargo_name=inp.cargo_name,
            is_hme=inp.is_hme,
            discharge_permitted=discharge_permitted,
            destination=destination,
            chemical_required_liters=chem_liters,
            ph_neutralized=ph_ok,
            requires_garbage_record_entry=True,  # Part II Garbage Record Book
            advisories=advisories,
        )
