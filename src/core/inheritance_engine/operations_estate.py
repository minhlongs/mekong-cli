# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Estate file management operations for InheritanceEngine under Civil Code 2015."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .enums import SuccessionType


def create_estate_record(
    conn: sqlite3.Connection,
    decedent_name: str,
    decedent_id_number: str,
    decedent_dob: str,
    date_of_death: str,
    place_of_death: str = "Hà Nội, Việt Nam",
    last_residence: str = "Hà Nội, Việt Nam",
    place_of_opening: str | None = None,
    administrator_name: str | None = None,
    administrator_contact: str | None = None,
    succession_type: str = SuccessionType.INTESTATE.value,
    dedicated_worship_amount: float = 0.0,
    dedicated_worship_description: str | None = None,
    notes: str | None = None,
    estate_id: str | None = None,
) -> str:
    """Validate inputs and insert a new estate record under Articles 609, 611, 612 Civil Code 2015."""
    if not decedent_name or not decedent_id_number or not date_of_death:
        raise ValueError("Tên người chết, số định danh cá nhân/CCCD và ngày chết là bắt buộc.")

    try:
        d_death = datetime.date.fromisoformat(date_of_death)
        d_dob = datetime.date.fromisoformat(decedent_dob)
        if d_death < d_dob:
            raise ValueError("Ngày chết không thể trước ngày sinh.")
    except Exception as e:
        if "Ngày chết không thể" in str(e):
            raise
        raise ValueError(f"Định dạng ngày không hợp lệ (YYYY-MM-DD): {e}")

    actual_place_of_opening = place_of_opening or last_residence
    eid = estate_id or f"EST-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO estates (
            estate_id, decedent_name, decedent_id_number, decedent_dob,
            date_of_death, place_of_death, last_residence, place_of_opening,
            administrator_name, administrator_contact, succession_type,
            dedicated_worship_amount, dedicated_worship_description,
            is_settled, created_at, updated_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """,
        (
            eid, decedent_name, decedent_id_number, decedent_dob,
            date_of_death, place_of_death, last_residence, actual_place_of_opening,
            administrator_name, administrator_contact, succession_type,
            dedicated_worship_amount, dedicated_worship_description, now, now, notes,
        ),
    )
    conn.commit()
    return eid


def get_estate_record(conn: sqlite3.Connection, estate_id: str) -> dict[str, typing.Any]:
    """Retrieve full details of an estate including assets, obligations, wills, and heirs."""
    cursor = conn.execute("SELECT * FROM estates WHERE estate_id = ?", (estate_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Không tìm thấy hồ sơ di sản với mã: {estate_id}")
    estate_dict = dict(row)

    c_assets = conn.execute("SELECT * FROM estate_assets WHERE estate_id = ?", (estate_id,))
    estate_dict["assets"] = [dict(r) for r in c_assets.fetchall()]

    c_ob = conn.execute("SELECT * FROM estate_obligations WHERE estate_id = ? ORDER BY priority ASC", (estate_id,))
    estate_dict["obligations"] = [dict(r) for r in c_ob.fetchall()]

    c_will = conn.execute("SELECT * FROM wills WHERE estate_id = ?", (estate_id,))
    estate_dict["wills"] = [dict(r) for r in c_will.fetchall()]

    c_heirs = conn.execute("SELECT * FROM heirs WHERE estate_id = ?", (estate_id,))
    estate_dict["heirs"] = [dict(r) for r in c_heirs.fetchall()]

    total_gross = sum(a["net_estate_value"] for a in estate_dict["assets"])
    total_obligations = sum(o["amount"] for o in estate_dict["obligations"])
    worship_amount = estate_dict["dedicated_worship_amount"]
    net_distributable = max(0.0, total_gross - total_obligations - worship_amount)

    estate_dict["summary"] = {
        "total_gross_assets": total_gross,
        "total_obligations": total_obligations,
        "dedicated_worship_amount": worship_amount,
        "net_distributable_estate": net_distributable,
        "total_assets_count": len(estate_dict["assets"]),
        "total_heirs_count": len(estate_dict["heirs"]),
    }
    return estate_dict


def list_estates_record(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, typing.Any]]:
    """List summary of all estate files ordered by creation date."""
    cursor = conn.execute("SELECT * FROM estates ORDER BY created_at DESC LIMIT ?", (limit,))
    return [dict(r) for r in cursor.fetchall()]


__all__ = [
    "create_estate_record",
    "get_estate_record",
    "list_estates_record",
]
