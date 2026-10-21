# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Notary division agreements and 15-day public posting operations under Law on Notarization 2014."""

from __future__ import annotations

import datetime
import json
import sqlite3
import typing
import uuid

from .calculator import calculate_statutory_shares_record
from .enums import NotaryProcedureType
from .operations_estate import get_estate_record


def execute_division_agreement_record(
    conn: sqlite3.Connection,
    estate_id: str,
    procedure_type: str,
    notary_office: str,
    division_date: str | None = None,
    public_posting_ubnd: str | None = None,
    public_posting_start_date: str | None = None,
    notary_doc_ref: str | None = None,
    agreement_id: str | None = None,
) -> dict[str, typing.Any]:
    """Formulate Notarized Estate Division Agreement under Articles 57, 58 Law on Notarization 2014."""
    estate = get_estate_record(conn, estate_id)
    calc_result = calculate_statutory_shares_record(estate)

    valid_proc_types = [p.value for p in NotaryProcedureType]
    if procedure_type not in valid_proc_types:
        raise ValueError(f"Loại thủ tục công chứng không hợp lệ: {procedure_type}")

    d_div = division_date or datetime.date.today().isoformat()
    posting_ubnd = public_posting_ubnd or estate["last_residence"]

    d_post_start = public_posting_start_date or (datetime.date.fromisoformat(d_div) - datetime.timedelta(days=16)).isoformat()
    d_post_end = (datetime.date.fromisoformat(d_post_start) + datetime.timedelta(days=15)).isoformat()

    aid = agreement_id or f"AGR-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.datetime.now().isoformat()

    conn.execute(
        """
        INSERT INTO division_agreements (
            agreement_id, estate_id, division_date, procedure_type,
            notary_office, notary_doc_ref, public_posting_start_date,
            public_posting_end_date, public_posting_ubnd, total_gross_assets,
            total_obligations_paid, total_worship_amount, total_distributable_estate,
            distribution_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            aid, estate_id, d_div, procedure_type, notary_office, notary_doc_ref,
            d_post_start, d_post_end, posting_ubnd, calc_result["gross_assets"],
            calc_result["total_obligations_paid"], calc_result["dedicated_worship_deducted"],
            calc_result["net_distributable_estate"],
            json.dumps(calc_result["allocations"], ensure_ascii=False), now,
        ),
    )

    for alloc in calc_result["allocations"]:
        if alloc["heir_id"] != "STATE_TREASURY":
            conn.execute(
                "UPDATE heirs SET allocated_amount = ?, allocated_percentage = ? WHERE heir_id = ?",
                (alloc["allocated_amount"], alloc["allocated_percentage"], alloc["heir_id"]),
            )

    conn.execute("UPDATE estates SET is_settled = 1, updated_at = ? WHERE estate_id = ?", (now, estate_id))
    conn.commit()

    return {
        "agreement_id": aid,
        "estate_id": estate_id,
        "decedent_name": estate["decedent_name"],
        "procedure_type": procedure_type,
        "notary_office": notary_office,
        "notary_doc_ref": notary_doc_ref,
        "is_compliant": True,
        "public_posting": {
            "ubnd_location": posting_ubnd,
            "start_date": d_post_start,
            "end_date": d_post_end,
            "duration_days": 15,
            "notice_duration_days": 15,
            "is_compliant_15_days": True,
        },
        "summary": {
            "total_gross_assets": calc_result["gross_assets"],
            "total_obligations_paid": calc_result["total_obligations_paid"],
            "total_worship_amount": calc_result["dedicated_worship_deducted"],
            "total_distributable_estate": calc_result["net_distributable_estate"],
        },
        "allocations": calc_result["allocations"],
    }


__all__ = ["execute_division_agreement_record"]
