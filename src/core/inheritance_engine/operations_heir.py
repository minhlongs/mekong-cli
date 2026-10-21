# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Heir registration, statutory classifications, and disclaimers under Civil Code 2015."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .enums import HeirEligibilityStatus, HeirRank, HeirRelationship, SuccessionType
from .operations_estate import get_estate_record


def register_heir_record(
    conn: sqlite3.Connection,
    estate_id: str,
    full_name: str,
    id_number: str,
    dob: str,
    relationship: str,
    heir_rank: str | None = None,
    is_alive_at_opening: bool = True,
    is_conceived_before_opening: bool = False,
    is_minor_or_disabled: bool = False,
    is_disqualified_art621: bool = False,
    is_forgiven_in_will: bool = False,
    is_substitutional_art652: bool = False,
    substituting_for_name: str | None = None,
    testamentary_share_percent: float = 0.0,
    testamentary_fixed_amount: float = 0.0,
    notes: str | None = None,
    heir_id: str | None = None,
) -> dict[str, typing.Any]:
    """Register heir with kinship mapping, forced heir check (Art. 644), or substitution (Art. 652)."""
    estate = get_estate_record(conn, estate_id)

    if not heir_rank:
        if is_substitutional_art652 and relationship in (HeirRelationship.GRANDCHILD.value, HeirRelationship.GREAT_GRANDCHILD.value):
            heir_rank = HeirRank.FIRST_RANK.value
        elif relationship in (
            HeirRelationship.SPOUSE.value, HeirRelationship.BIOLOGICAL_CHILD.value, HeirRelationship.ADOPTED_CHILD.value,
            HeirRelationship.BIOLOGICAL_PARENT.value, HeirRelationship.ADOPTIVE_PARENT.value, HeirRelationship.STEPCHILD_STEPPARENT.value,
        ):
            heir_rank = HeirRank.FIRST_RANK.value
        elif relationship in (HeirRelationship.GRANDPARENT.value, HeirRelationship.SIBLING.value, HeirRelationship.GRANDCHILD.value):
            heir_rank = HeirRank.SECOND_RANK.value
        elif relationship in (
            HeirRelationship.GREAT_GRANDPARENT.value, HeirRelationship.UNCLE_AUNT.value,
            HeirRelationship.NEPHEW_NIECE.value, HeirRelationship.GREAT_GRANDCHILD.value,
        ):
            heir_rank = HeirRank.THIRD_RANK.value
        else:
            heir_rank = HeirRank.TESTAMENTARY_ONLY.value

    d_opening = datetime.date.fromisoformat(estate["date_of_death"])
    d_dob = datetime.date.fromisoformat(dob)
    age_at_opening = (d_opening - d_dob).days / 365.25
    is_minor = age_at_opening < 18.0

    is_forced_heir_candidate = (
        relationship in (HeirRelationship.SPOUSE.value, HeirRelationship.BIOLOGICAL_PARENT.value, HeirRelationship.ADOPTIVE_PARENT.value)
        or (relationship in (HeirRelationship.BIOLOGICAL_CHILD.value, HeirRelationship.ADOPTED_CHILD.value) and (is_minor or is_minor_or_disabled))
    )

    eligibility = HeirEligibilityStatus.ELIGIBLE.value
    if is_disqualified_art621:
        eligibility = HeirEligibilityStatus.ELIGIBLE.value if is_forgiven_in_will else HeirEligibilityStatus.DISQUALIFIED_ART621.value
    elif is_substitutional_art652:
        eligibility = HeirEligibilityStatus.SUBSTITUTIONAL_ART652.value
    elif is_forced_heir_candidate and estate["succession_type"] == SuccessionType.TESTAMENTARY.value:
        eligibility = HeirEligibilityStatus.FORCED_HEIR_ART644.value

    hid = heir_id or f"HIR-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO heirs (
            heir_id, estate_id, full_name, id_number, dob, relationship,
            heir_rank, is_alive_at_opening, is_conceived_before_opening,
            is_minor_or_disabled, is_disqualified_art621, is_forgiven_in_will,
            has_disclaimed_art620, is_substitutional_art652, substituting_for_name,
            eligibility_status, testamentary_share_percent, testamentary_fixed_amount,
            allocated_amount, allocated_percentage, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, 0.0, 0.0, ?, ?)
        """,
        (
            hid, estate_id, full_name, id_number, dob, relationship, heir_rank,
            1 if is_alive_at_opening else 0, 1 if is_conceived_before_opening else 0,
            1 if (is_minor or is_minor_or_disabled) else 0, 1 if is_disqualified_art621 else 0,
            1 if is_forgiven_in_will else 0, 1 if is_substitutional_art652 else 0,
            substituting_for_name, eligibility, testamentary_share_percent, testamentary_fixed_amount,
            notes, now,
        ),
    )
    conn.commit()

    return {
        "heir_id": hid, "estate_id": estate_id, "full_name": full_name, "id_number": id_number,
        "dob": dob, "age_at_opening": round(age_at_opening, 1), "relationship": relationship,
        "heir_rank": heir_rank, "eligibility_status": eligibility,
        "is_forced_heir_candidate": is_forced_heir_candidate,
        "is_substitutional": is_substitutional_art652,
        "testamentary_share_percent": testamentary_share_percent,
        "testamentary_fixed_amount": testamentary_fixed_amount,
    }


def record_disclaimer_record(
    conn: sqlite3.Connection,
    estate_id: str,
    heir_id: str,
    declaration_date: str,
    notary_or_ubnd_office: str,
    notary_document_number: str,
    reason: str | None = None,
    is_for_debt_evasion: bool = False,
    disclaimer_id: str | None = None,
) -> dict[str, typing.Any]:
    """Record renunciation of inheritance under Art. 620 Civil Code 2015."""
    estate = get_estate_record(conn, estate_id)

    c = conn.execute("SELECT * FROM heirs WHERE heir_id = ? AND estate_id = ?", (heir_id, estate_id))
    heir = c.fetchone()
    if not heir:
        raise ValueError(f"Không tìm thấy người thừa kế {heir_id} trong hồ sơ di sản {estate_id}")

    heir_dict = dict(heir)
    if estate["is_settled"]:
        raise ValueError("Không thể từ chối nhận di sản sau khi di sản đã được phân chia.")

    is_valid = 1 if not is_for_debt_evasion else 0
    did = disclaimer_id or f"DIS-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO disclaimers (
            disclaimer_id, estate_id, heir_id, heir_name, declaration_date,
            notary_or_ubnd_office, notary_document_number, reason,
            is_for_debt_evasion, is_valid, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (did, estate_id, heir_id, heir_dict["full_name"], declaration_date, notary_or_ubnd_office, notary_document_number, reason, 1 if is_for_debt_evasion else 0, is_valid, now),
    )
    if is_valid:
        conn.execute(
            "UPDATE heirs SET has_disclaimed_art620 = 1, eligibility_status = ? WHERE heir_id = ?",
            (HeirEligibilityStatus.DISCLAIMED_ART620.value, heir_id),
        )
    conn.commit()

    return {
        "disclaimer_id": did, "estate_id": estate_id, "heir_id": heir_id, "heir_name": heir_dict["full_name"],
        "declaration_date": declaration_date, "notary_or_ubnd_office": notary_or_ubnd_office,
        "notary_document_number": notary_document_number, "is_valid": bool(is_valid),
        "status": "RECORDED" if is_valid else "VOID_DEBT_EVASION", "is_for_debt_evasion": is_for_debt_evasion,
        "warning": "Từ chối nhận di sản vô hiệu nếu nhằm trốn tránh thực hiện nghĩa vụ tài sản (Điều 620 K1 BLDS)." if is_for_debt_evasion else None,
    }


__all__ = ["register_heir_record", "record_disclaimer_record"]
