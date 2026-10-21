# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Asset inventory and estate obligation operations under Civil Code 2015."""

from __future__ import annotations

import datetime
import sqlite3
import typing
import uuid

from .enums import ObligationPriority
from .operations_estate import get_estate_record


def add_estate_asset_record(
    conn: sqlite3.Connection,
    estate_id: str,
    asset_name: str,
    category: str,
    estimated_value: float,
    is_sole_ownership: bool = True,
    ownership_share: float = 1.0,
    legal_document_ref: str | None = None,
    location: str | None = None,
    is_for_worship: bool = False,
    asset_id: str | None = None,
) -> dict[str, typing.Any]:
    """Add asset to estate inventory with ownership share calculation under Art. 612 Civil Code 2015."""
    if estimated_value <= 0:
        raise ValueError("Giá trị ước tính của tài sản phải lớn hơn 0.")
    if ownership_share <= 0 or ownership_share > 1.0:
        raise ValueError("Tỷ lệ sở hữu của người chết phải nằm trong khoảng (0, 1.0].")

    get_estate_record(conn, estate_id)

    net_estate_value = estimated_value * (1.0 if is_sole_ownership else ownership_share)
    aid = asset_id or f"AST-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO estate_assets (
            asset_id, estate_id, asset_name, category, estimated_value,
            is_sole_ownership, ownership_share, net_estate_value,
            legal_document_ref, location, is_for_worship, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            aid, estate_id, asset_name, category, estimated_value,
            1 if is_sole_ownership else 0, 1.0 if is_sole_ownership else ownership_share,
            net_estate_value, legal_document_ref, location, 1 if is_for_worship else 0, now,
        ),
    )
    conn.commit()
    return {
        "asset_id": aid,
        "estate_id": estate_id,
        "asset_name": asset_name,
        "category": category,
        "estimated_value": estimated_value,
        "is_sole_ownership": is_sole_ownership,
        "ownership_share": 1.0 if is_sole_ownership else ownership_share,
        "net_estate_value": net_estate_value,
        "legal_document_ref": legal_document_ref,
        "location": location,
        "is_for_worship": is_for_worship,
    }


def add_estate_obligation_record(
    conn: sqlite3.Connection,
    estate_id: str,
    creditor_name: str,
    obligation_name: str,
    priority: str,
    amount: float,
    legal_basis: str | None = None,
    obligation_id: str | None = None,
) -> dict[str, typing.Any]:
    """Add debt or liability with statutory payment priority ranking under Art. 658 Civil Code 2015."""
    if amount <= 0:
        raise ValueError("Số tiền nghĩa vụ tài sản phải lớn hơn 0.")

    get_estate_record(conn, estate_id)

    valid_priorities = [p.value for p in ObligationPriority]
    if priority not in valid_priorities:
        raise ValueError(f"Thứ tự ưu tiên không hợp lệ: {priority}. Phải là một trong: {valid_priorities}")

    oid = obligation_id or f"OBL-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO estate_obligations (
            obligation_id, estate_id, creditor_name, obligation_name,
            priority, amount, paid_amount, is_settled, legal_basis, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 0.0, 0, ?, ?)
        """,
        (oid, estate_id, creditor_name, obligation_name, priority, amount, legal_basis, now),
    )
    conn.commit()
    return {
        "obligation_id": oid,
        "estate_id": estate_id,
        "creditor_name": creditor_name,
        "obligation_name": obligation_name,
        "priority": priority,
        "amount": amount,
        "legal_basis": legal_basis,
    }


__all__ = ["add_estate_asset_record", "add_estate_obligation_record"]
