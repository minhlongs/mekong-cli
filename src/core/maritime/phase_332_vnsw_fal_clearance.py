"""Phase 332: Vietnam National Single Window (VNSW) & IMO FAL 1-7 Clearance.

Validates electronic maritime clearance declarations: IMO FAL Forms 1-7,
customs/quarantine status, and automated Port Clearance Certificate issuance.
Kept strictly under 200 lines according to KISS/YAGNI principles.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import hashlib
import json


@dataclass
class ImoFalDeclarationInput:
    imo_number: str
    vessel_name: str
    call_sign: str
    port_of_call: str
    voyage_number: str
    fal1_general_dec: bool  # IMO FAL 1
    fal2_cargo_dec: bool  # IMO FAL 2
    fal3_stores_dec: bool  # IMO FAL 3
    fal4_crew_effects: bool  # IMO FAL 4
    fal5_crew_list_count: int  # IMO FAL 5
    fal6_passengers_count: int  # IMO FAL 6
    fal7_dangerous_goods_manifest: bool  # IMO FAL 7 (True if DG aboard)
    has_dangerous_goods: bool = False
    customs_status: str = "CLEARED"  # "CLEARED", "PENDING", "REJECTED"
    quarantine_sanitary_cleared: bool = True
    immigration_cleared: bool = True
    harbour_dues_paid: bool = True


@dataclass
class PortClearanceResult:
    imo_number: str
    vessel_name: str
    clearance_granted: bool
    clearance_id: Optional[str]
    missing_requirements: List[str]
    audit_hash: str
    fal_compliance_summary: Dict[str, bool]


class VNSWClearanceEngine:
    MANDATORY_CREW_MIN = 1

    @classmethod
    def evaluate(cls, inp: ImoFalDeclarationInput) -> PortClearanceResult:
        missing: List[str] = []
        fal_summary = {
            "FAL_1_GENERAL": inp.fal1_general_dec,
            "FAL_2_CARGO": inp.fal2_cargo_dec,
            "FAL_3_STORES": inp.fal3_stores_dec,
            "FAL_4_CREW_EFFECTS": inp.fal4_crew_effects,
            "FAL_5_CREW_LIST": inp.fal5_crew_list_count >= cls.MANDATORY_CREW_MIN,
            "FAL_6_PASSENGER_LIST": inp.fal6_passengers_count >= 0,
            "FAL_7_DANGEROUS_GOODS": (
                inp.fal7_dangerous_goods_manifest if inp.has_dangerous_goods else True
            ),
        }

        # Check FAL form completeness
        if not inp.fal1_general_dec:
            missing.append("FAL Form 1 (General Declaration) is missing or unverified")
        if not inp.fal2_cargo_dec:
            missing.append("FAL Form 2 (Cargo Declaration) is missing")
        if not inp.fal3_stores_dec:
            missing.append("FAL Form 3 (Ship's Stores Declaration) is missing")
        if not inp.fal4_crew_effects:
            missing.append("FAL Form 4 (Crew's Effects Declaration) is missing")
        if inp.fal5_crew_list_count < cls.MANDATORY_CREW_MIN:
            missing.append(f"FAL Form 5 Crew count must be >= {cls.MANDATORY_CREW_MIN}")
        if inp.has_dangerous_goods and not inp.fal7_dangerous_goods_manifest:
            missing.append("FAL Form 7 (Dangerous Goods Manifest) required when DG on board")

        # Statutory Authority Checks (Nghị định 58/2017/NĐ-CP)
        if inp.customs_status.upper() != "CLEARED":
            missing.append(f"Customs clearance status is {inp.customs_status} (must be CLEARED)")
        if not inp.quarantine_sanitary_cleared:
            missing.append("International health & sanitary quarantine not cleared")
        if not inp.immigration_cleared:
            missing.append("Border guard immigration clearance not approved")
        if not inp.harbour_dues_paid:
            missing.append("Port & maritime administration dues outstanding")

        granted = len(missing) == 0
        clearance_id = None
        if granted:
            clearance_id = (
                f"VNSW-PC-{inp.port_of_call.upper()}-{inp.imo_number}-{inp.voyage_number}"
            )

        # Audit hash
        audit_payload = {
            "imo": inp.imo_number,
            "vessel": inp.vessel_name,
            "port": inp.port_of_call,
            "voyage": inp.voyage_number,
            "granted": granted,
            "clearance_id": clearance_id,
            "fal_summary": fal_summary,
            "missing": missing,
        }
        audit_hash = hashlib.sha256(
            json.dumps(audit_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return PortClearanceResult(
            imo_number=inp.imo_number,
            vessel_name=inp.vessel_name,
            clearance_granted=granted,
            clearance_id=clearance_id,
            missing_requirements=missing,
            audit_hash=audit_hash,
            fal_compliance_summary=fal_summary,
        )
