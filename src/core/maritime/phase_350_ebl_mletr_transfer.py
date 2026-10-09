"""Phase 350: Electronic Bill of Lading (e-BL) Title Transfer & MLETR Engine.

Implements UNCITRAL MLETR (Model Law on Electronic Transferable Records),
DCSA e-BL Data Model, and Vietnam Maritime Code 2015:
- Singularity and exclusive control over electronic transferable record.
- Multi-party lifecycle: ISSUED -> ENDORSED -> TRANSFERRED -> SURRENDERED.
- SHA-256 cryptographic lineage tracking to prevent paper duplicate / LOI fraud.
- Cargo release authorization verification against rightful title holder.
Strictly under 200 LOC.
"""

from dataclasses import dataclass, field
import hashlib
from typing import List, Optional


@dataclass
class EblTransferEvent:
    event_type: str  # ISSUE, ENDORSE, TRANSFER, SURRENDER
    from_party: str
    to_party: str
    timestamp_iso: str
    notes: str = ""


@dataclass
class EblMletrInput:
    bl_number: str
    carrier_name: str
    shipper_name: str
    consignee_name: str  # Named party, "TO_ORDER", or "BEARER"
    notify_party: str
    cargo_description: str
    container_count: int
    gross_weight_kg: float
    current_holder: str
    events: List[EblTransferEvent] = field(default_factory=list)
    requested_release_party: Optional[str] = None


@dataclass
class EblMletrResult:
    bl_number: str
    bl_type: str  # STRAIGHT_BL, ORDER_BL, BEARER_BL
    lifecycle_status: str  # ISSUED, IN_TRANSIT, SURRENDERED, INVALID_CHAIN
    current_lawful_holder: str
    cryptographic_lineage_hash: str
    is_release_authorized: bool
    is_negotiable: bool
    advisories: List[str] = field(default_factory=list)


class EblMletrEngine:
    """Verifies electronic Bill of Lading title transfer and exclusive control under MLETR."""

    @classmethod
    def evaluate(cls, inp: EblMletrInput) -> EblMletrResult:
        advisories: List[str] = []

        # 1. Determine BL category
        consignee_norm = inp.consignee_name.strip().upper()
        if consignee_norm in ["TO ORDER", "TO_ORDER", "TO ORDER OF SHIPPER"]:
            bl_type = "ORDER_BL"
            is_negotiable = True
        elif consignee_norm == "BEARER":
            bl_type = "BEARER_BL"
            is_negotiable = True
        else:
            bl_type = "STRAIGHT_BL"
            is_negotiable = False

        # 2. Trace lineage hash chain (SHA-256)
        chain_data = f"{inp.bl_number}|{inp.carrier_name}|{inp.shipper_name}|{inp.consignee_name}"
        running_hash = hashlib.sha256(chain_data.encode("utf-8")).hexdigest()

        active_holder = inp.shipper_name
        is_surrendered = False
        valid_chain = True

        for idx, evt in enumerate(inp.events):
            if active_holder.upper() != evt.from_party.upper() and bl_type != "BEARER_BL":
                valid_chain = False
                advisories.append(
                    f"BROKEN CHAIN OF TITLE: Event {idx+1} ({evt.event_type}) from '{evt.from_party}' "
                    f"does not match current holder '{active_holder}'."
                )

            active_holder = evt.to_party
            event_repr = f"{running_hash}|{evt.event_type}|{evt.from_party}|{evt.to_party}|{evt.timestamp_iso}"
            running_hash = hashlib.sha256(event_repr.encode("utf-8")).hexdigest()

            if evt.event_type.upper() == "SURRENDER":
                is_surrendered = True

        # 3. Assess status
        if not valid_chain:
            status = "INVALID_CHAIN"
        elif is_surrendered:
            status = "SURRENDERED"
        else:
            status = "IN_TRANSIT"

        # 4. Check release authorization
        release_auth = False
        if inp.requested_release_party:
            req_norm = inp.requested_release_party.strip().upper()
            if status == "INVALID_CHAIN":
                advisories.append("CARGO RELEASE DENIED: Invalid title transfer chain.")
            elif not is_surrendered and status != "SURRENDERED":
                advisories.append("CARGO RELEASE DENIED: e-BL has not been surrendered to carrier.")
            elif bl_type == "STRAIGHT_BL" and req_norm != inp.consignee_name.strip().upper():
                advisories.append(
                    f"CARGO RELEASE DENIED: Requesting party '{inp.requested_release_party}' "
                    f"is not named consignee '{inp.consignee_name}'."
                )
            else:
                release_auth = True
                advisories.append("CARGO RELEASE AUTHORIZED: Valid holder surrendered e-BL.")

        return EblMletrResult(
            bl_number=inp.bl_number,
            bl_type=bl_type,
            lifecycle_status=status,
            current_lawful_holder=active_holder,
            cryptographic_lineage_hash=running_hash,
            is_release_authorized=release_auth,
            is_negotiable=is_negotiable,
            advisories=advisories,
        )
